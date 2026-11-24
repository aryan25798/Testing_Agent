"""
Base Agent Architecture for Testing Agent Platform.
Provides lifecycle management, dynamic model resolution, structured validation,
execution tracking, and error handling for all 6 specialized agents.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from src.llm.router.agent_model_router import agent_model_router
from src.database.session import SessionLocal
from src.models.entities import AgentExecution
from src.core.logging import get_logger
from src.core.exceptions import AgentExecutionError
from src.core.security.sanitizer import prompt_sanitizer

logger = get_logger("base_agent")


class BaseAgent(ABC):
    def __init__(self, agent_id: str, agent_name: str, system_instructions: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.system_instructions = system_instructions

    @abstractmethod
    def run(self, input_data: Any, project_id: Optional[str] = None) -> Any:
        """Executes the specialized agent task with validated input and output."""
        pass

    def execute_with_llm(
        self,
        prompt: str,
        output_schema: Optional[Type[BaseModel]] = None,
        project_id: Optional[str] = None,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Executes a prompt against the agent's dynamically configured AI model,
        retrying on failure and persisting token and latency metrics.
        """
        provider, model_id = agent_model_router.get_provider_and_model(self.agent_id)
        logger.info(f"Agent '{self.agent_name}' ({self.agent_id}) running on {provider.__class__.__name__} [{model_id}]")

        # Defense-in-depth: automatically redact any accidentally included credentials from outgoing prompt
        safe_prompt = prompt_sanitizer.redact_secrets(prompt)

        last_error = None
        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                # On retry, inject explicit feedback with the previous error so model self-repairs syntax
                attempt_prompt = safe_prompt
                if attempt > 0 and last_error:
                    attempt_prompt = (
                        f"{safe_prompt}\n\n"
                        f"CRITICAL CORRECTION (Retry {attempt}): Your previous output encountered validation error: {last_error[:300]}.\n"
                        f"You MUST return strictly valid, RFC-8259 compliant JSON matching the requested schema. "
                        f"Avoid unescaped quotes inside strings and remove trailing commas."
                    )

                response = provider.generate_structured(
                    prompt=attempt_prompt,
                    system_prompt=self.system_instructions,
                    output_schema=output_schema,
                    model=model_id,
                    temperature=None,
                )
                latency = time.time() - start_time

                # Persist execution metric to database
                self._record_execution(
                    project_id=project_id,
                    provider=response.provider,
                    model=response.model,
                    in_tokens=response.input_tokens,
                    out_tokens=response.output_tokens,
                    latency=latency,
                    status="Success",
                )

                from src.core.utils.json_sanitizer import normalize_to_schema, repair_and_parse_json

                if response.structured_data:
                    if output_schema:
                        return normalize_to_schema(response.structured_data, output_schema).model_dump()
                    return response.structured_data
                elif output_schema:
                    # Parse and normalize text if structured_data is empty
                    parsed = repair_and_parse_json(response.text)
                    return normalize_to_schema(parsed, output_schema).model_dump()
                return {"text": response.text}

            except Exception as e:
                from src.core.exceptions import QuotaExceededError
                if isinstance(e, QuotaExceededError):
                    logger.error(f"Quota exceeded during agent execution: {e}")
                    raise e
                latency = time.time() - start_time
                last_error = str(e)
                logger.warning(f"Agent '{self.agent_name}' attempt {attempt + 1} failed: {e}")
                self._record_execution(
                    project_id=project_id,
                    provider=provider.__class__.__name__,
                    model=model_id,
                    in_tokens=0,
                    out_tokens=0,
                    latency=latency,
                    status="Failed",
                    error_message=last_error,
                )

        raise AgentExecutionError(f"Agent '{self.agent_name}' failed after {max_retries + 1} attempts: {last_error}")

    def _record_execution(
        self,
        project_id: Optional[str],
        provider: str,
        model: str,
        in_tokens: int,
        out_tokens: int,
        latency: float,
        status: str,
        error_message: Optional[str] = None,
    ):
        try:
            with SessionLocal() as db:
                record = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    provider=provider,
                    model=model,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    latency_seconds=round(latency, 2),
                    status=status,
                    error_message=error_message,
                )
                db.add(record)
                db.commit()
        except Exception as e:
            logger.warning(f"Could not record agent execution metrics: {e}")
