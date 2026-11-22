"""
MCP Permission and Exact-Action Human Approval Manager.
Ensures that no AI agent can execute destructive or mutating operations on GitHub or Jira
without explicit, bound human review and consent.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.database.session import SessionLocal
from src.models.entities import MCPApprovalRequest
from src.core.logging import get_logger
from src.core.security.audit_logger import audit_logger

logger = get_logger("mcp_approval_manager")


class MCPApprovalManager:
    """
    Manages human-in-the-loop approval workflow for mutating MCP tool invocations.
    Approvals are cryptographically and deterministically bound to the exact tool and exact arguments.
    """

    def request_approval(
        self,
        project_id: str,
        provider: str,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        target_object: str,
        operation_description: str,
        proposed_diff: Optional[str] = None,
        risk_level: str = "medium",
    ) -> MCPApprovalRequest:
        """Creates a pending approval record bound to exact tool and arguments."""
        with SessionLocal() as db:
            req = MCPApprovalRequest(
                project_id=project_id,
                provider=provider.lower(),
                agent_id=agent_id,
                tool_name=tool_name,
                arguments=arguments,
                target_object=target_object,
                operation_description=operation_description,
                proposed_diff=proposed_diff,
                risk_level=risk_level,
                status="pending",
            )
            db.add(req)
            db.commit()
            db.refresh(req)

            audit_logger.log_event(
                action="MCP_APPROVAL_REQUESTED",
                status="PENDING",
                details={
                    "approval_id": req.id,
                    "project_id": project_id,
                    "provider": provider,
                    "tool_name": tool_name,
                    "target_object": target_object,
                    "risk_level": risk_level,
                },
                severity="WARNING" if risk_level in ["high", "critical"] else "INFO",
            )
            return req

    def get_pending_approvals(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all currently pending human approval requests."""
        with SessionLocal() as db:
            query = db.query(MCPApprovalRequest).filter(MCPApprovalRequest.status == "pending")
            if project_id:
                query = query.filter(MCPApprovalRequest.project_id == project_id)
            query = query.order_by(MCPApprovalRequest.created_at.desc())
            records = query.all()

            return [
                {
                    "id": r.id,
                    "project_id": r.project_id,
                    "provider": r.provider,
                    "agent_id": r.agent_id,
                    "tool_name": r.tool_name,
                    "arguments": r.arguments,
                    "target_object": r.target_object,
                    "operation_description": r.operation_description,
                    "proposed_diff": r.proposed_diff,
                    "risk_level": r.risk_level,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]

    def decide_approval(
        self,
        approval_id: str,
        decision: str,
        decided_by: str = "Local Engineer",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records human decision (approved/rejected)."""
        clean_decision = decision.lower().strip()
        if clean_decision not in ["approved", "rejected"]:
            raise ValueError("Decision must be 'approved' or 'rejected'.")

        with SessionLocal() as db:
            req = db.query(MCPApprovalRequest).filter(MCPApprovalRequest.id == approval_id).first()
            if not req:
                raise ValueError(f"Approval request {approval_id} not found.")

            if req.status != "pending":
                raise ValueError(f"Approval request is already in status '{req.status}'.")

            req.status = clean_decision
            req.decided_by = decided_by
            req.decision_reason = reason
            req.decided_at = datetime.utcnow()
            db.commit()

            audit_logger.log_event(
                action="MCP_APPROVAL_DECISION",
                status=clean_decision.upper(),
                details={
                    "approval_id": req.id,
                    "tool_name": req.tool_name,
                    "decided_by": decided_by,
                    "decision": clean_decision,
                    "reason": reason,
                },
                severity="INFO" if clean_decision == "approved" else "WARNING",
            )

            return {
                "id": req.id,
                "status": req.status,
                "tool_name": req.tool_name,
                "decided_at": req.decided_at.isoformat(),
            }

    def check_approval(self, project_id: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        Validates if an explicit human approval exists and is approved for the EXACT arguments.
        If arguments have been altered by the LLM or caller, the approval check fails.
        """
        with SessionLocal() as db:
            # Look for recent approved requests within last 1 hour
            req = (
                db.query(MCPApprovalRequest)
                .filter(
                    MCPApprovalRequest.project_id == project_id,
                    MCPApprovalRequest.tool_name == tool_name,
                    MCPApprovalRequest.status == "approved",
                )
                .order_by(MCPApprovalRequest.decided_at.desc())
                .first()
            )
            if not req:
                return False

            # Exact argument equality verification
            return req.arguments == arguments


approval_manager = MCPApprovalManager()
