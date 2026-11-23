"""
Background Workflow Runner for Testing Agent Platform.
Runs LangGraph workflow invocations in background threads with state tracking,
cancellation support, and timeout handling.
"""

import asyncio
import uuid
import time
import threading
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from src.core.logging import get_logger

logger = get_logger("workflow_runner")

# Default timeout for a full workflow invocation (10 minutes)
DEFAULT_WORKFLOW_TIMEOUT_SECONDS = 600


class WorkflowState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowRecord:
    """Tracks a single workflow execution."""
    workflow_id: str
    project_id: str
    state: WorkflowState = WorkflowState.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    current_agent: str = "pending"
    step_count: int = 0
    errors: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    _cancel_event: threading.Event = field(default_factory=threading.Event)

    def to_dict(self) -> Dict[str, Any]:
        elapsed = (self.end_time or time.time()) - self.start_time
        return {
            "workflow_id": self.workflow_id,
            "project_id": self.project_id,
            "state": self.state.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": round(elapsed, 2),
            "current_agent": self.current_agent,
            "step_count": self.step_count,
            "errors": self.errors,
            "result": self.result,
        }


class WorkflowRunner:
    """
    Manages background workflow executions.
    Uses an in-memory dict to track active and completed workflows.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowRecord] = {}
        self._project_cancel_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def register_project_run(self, project_id: str) -> threading.Event:
        """Initializes or resets a cancellation event for a project's active run."""
        with self._lock:
            event = threading.Event()
            self._project_cancel_events[project_id] = event
            return event

    def is_cancelled(self, project_id: Optional[str] = None, workflow_id: Optional[str] = None) -> bool:
        """Checks if cancellation has been requested for a project or workflow."""
        with self._lock:
            if workflow_id:
                record = self._workflows.get(workflow_id)
                if record and (record._cancel_event.is_set() or record.state == WorkflowState.CANCELLED):
                    return True
            if project_id:
                evt = self._project_cancel_events.get(project_id)
                if evt and evt.is_set():
                    return True
        return False

    def cancel_project_workflows(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Signals cancellation to all workflows (both background runner and SSE streams)
        associated with the given project.
        """
        cancelled_records = []
        with self._lock:
            # Signal project-level cancel event
            evt = self._project_cancel_events.get(project_id)
            if evt:
                evt.set()
            else:
                new_evt = threading.Event()
                new_evt.set()
                self._project_cancel_events[project_id] = new_evt

            # Signal any registered WorkflowRecords for this project
            for record in self._workflows.values():
                if record.project_id == project_id and record.state in (WorkflowState.PENDING, WorkflowState.RUNNING):
                    record._cancel_event.set()
                    record.state = WorkflowState.CANCELLED
                    record.end_time = time.time()
                    record.errors.append("Workflow cancelled by user request")
                    cancelled_records.append(record.to_dict())

        logger.info(f"Cancellation triggered for project {project_id} ({len(cancelled_records)} background workflows stopped)")
        return cancelled_records

    async def start_workflow(
        self,
        graph,
        initial_state: Dict[str, Any],
        project_id: str,
        timeout_seconds: int = DEFAULT_WORKFLOW_TIMEOUT_SECONDS,
    ) -> WorkflowRecord:
        """
        Launches a graph invocation in a background thread.
        Returns immediately with the WorkflowRecord (state=pending).
        """
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        initial_state["workflow_id"] = workflow_id

        record = WorkflowRecord(
            workflow_id=workflow_id,
            project_id=project_id,
        )

        with self._lock:
            self._workflows[workflow_id] = record

        # Launch graph.invoke in a background thread via asyncio.to_thread
        asyncio.ensure_future(
            self._run_in_background(graph, initial_state, record, timeout_seconds)
        )

        logger.info(f"Workflow {workflow_id} launched for project {project_id}")
        return record

    async def _run_in_background(
        self,
        graph,
        initial_state: Dict[str, Any],
        record: WorkflowRecord,
        timeout_seconds: int,
    ):
        """Executes the graph in a background thread with timeout and cancellation."""
        record.state = WorkflowState.RUNNING
        record.current_agent = "starting"

        try:
            # Run the synchronous graph.invoke in a thread so it doesn't block
            # the FastAPI event loop. Wrap with asyncio.wait_for for timeout.
            final_state = await asyncio.wait_for(
                asyncio.to_thread(self._invoke_graph, graph, initial_state, record),
                timeout=timeout_seconds,
            )

            if record.state == WorkflowState.CANCELLED:
                logger.info(f"Workflow {record.workflow_id} was cancelled during execution")
                return

            record.state = WorkflowState.COMPLETED
            record.current_agent = final_state.get("current_agent", "completed")
            record.step_count = final_state.get("step_count", 0)
            record.result = {
                "workflow_status": final_state.get("workflow_status"),
                "steps_completed": final_state.get("step_count"),
                "total_requirements": len(final_state.get("requirements", [])),
                "total_scenarios": len(final_state.get("test_scenarios", [])),
                "total_test_cases": len(final_state.get("test_cases", [])),
                "total_scripts": len(final_state.get("automation_scripts", [])),
                "total_executions": len(final_state.get("execution_results", [])),
            }
            # Capture any errors accumulated during the run
            if final_state.get("errors"):
                record.errors.extend(final_state["errors"])
            if final_state.get("workflow_status") == "Failed":
                record.state = WorkflowState.FAILED

            logger.info(f"Workflow {record.workflow_id} completed successfully")

        except asyncio.TimeoutError:
            record.state = WorkflowState.FAILED
            record.errors.append(
                f"Workflow timed out after {timeout_seconds} seconds"
            )
            logger.error(f"Workflow {record.workflow_id} timed out after {timeout_seconds}s")

        except Exception as exc:
            record.state = WorkflowState.FAILED
            record.errors.append(f"Workflow execution error: {str(exc)}")
            logger.error(f"Workflow {record.workflow_id} failed: {exc}", exc_info=True)

        finally:
            record.end_time = time.time()

    @staticmethod
    def _invoke_graph(graph, initial_state: Dict[str, Any], record: WorkflowRecord) -> Dict[str, Any]:
        """
        Synchronous wrapper that calls graph.invoke().
        Runs inside a background thread managed by asyncio.to_thread().
        Checks the cancellation event before returning.
        """
        final_state = graph.invoke(initial_state)

        # Check if cancellation was requested while graph was running
        if record._cancel_event.is_set():
            record.state = WorkflowState.CANCELLED
            logger.info(f"Workflow {record.workflow_id} cancelled after graph completion")

        return final_state

    def get_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Returns the current status dict for a workflow, or None if not found."""
        with self._lock:
            record = self._workflows.get(workflow_id)
        if record is None:
            return None
        return record.to_dict()

    def cancel_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Requests cancellation of a running workflow.
        Sets the cancel event so the runner marks it cancelled on completion.
        Returns the updated status dict, or None if workflow not found.
        """
        with self._lock:
            record = self._workflows.get(workflow_id)
        if record is None:
            return None

        if record.state in (WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED):
            return record.to_dict()

        record._cancel_event.set()
        record.state = WorkflowState.CANCELLED
        record.end_time = time.time()
        record.errors.append("Workflow cancelled by user request")
        logger.info(f"Workflow {workflow_id} cancellation requested")
        return record.to_dict()

    def list_active(self) -> List[Dict[str, Any]]:
        """Returns a list of all workflows that are currently pending or running."""
        with self._lock:
            return [
                record.to_dict()
                for record in self._workflows.values()
                if record.state in (WorkflowState.PENDING, WorkflowState.RUNNING)
            ]

    def list_all(self) -> List[Dict[str, Any]]:
        """Returns a list of all tracked workflows."""
        with self._lock:
            return [record.to_dict() for record in self._workflows.values()]


# Module-level singleton instance
workflow_runner = WorkflowRunner()
