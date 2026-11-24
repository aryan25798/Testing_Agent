"""
Agent 2: Test Scenario Generation Agent.
Converts approved requirements into comprehensive test scenarios:
Positive, Negative, Boundary, Security, Edge-Case, and Integration scenarios.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from src.agents.base.base_agent import BaseAgent
from src.agents.requirement_analysis.agent import ExtractedRequirement
from src.core.logging import get_logger

logger = get_logger("scenario_generation_agent")


class GeneratedScenario(BaseModel):
    scenario_key: str = Field(description="Unique scenario ID like SCEN-001")
    requirement_key: str = Field(description="Traceable reference to parent requirement ID")
    title: str = Field(description="Concise scenario title")
    description: str = Field(default="", description="What is being validated and under what conditions")
    test_type: str = Field(default="Positive", description="Positive, Negative, Boundary, Security, UI, API, or Edge Case")
    preconditions: str = Field(default="", description="Initial system state required before test begins")
    test_objective: str = Field(default="", description="The explicit goal of this test scenario")
    priority: str = Field(default="Medium", description="Low, Medium, High, or Critical")
    risk: str = Field(default="Medium", description="Low, Medium, High, or Critical")
    expected_outcome: str = Field(default="", description="High-level expected system response")
    automation_suitability: str = Field(default="Yes", description="Yes, No, or Partial")

    @field_validator("preconditions", "test_objective", "expected_outcome", "description", mode="before")
    @classmethod
    def coerce_list_or_any_to_string(cls, v: Any) -> str:
        if isinstance(v, list):
            return "\n".join(str(item).strip() for item in v if item is not None)
        if isinstance(v, dict):
            return ", ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""


class ScenarioGenerationInput(BaseModel):
    requirements: List[ExtractedRequirement]


class ScenarioGenerationOutput(BaseModel):
    scenarios: List[GeneratedScenario] = Field(default_factory=list)
    total_scenarios: int = Field(default=0)
    coverage_summary: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def reconcile_scenario_output(cls, data: Any) -> Any:
        if isinstance(data, dict):
            scens = data.get("scenarios") or data.get("test_scenarios") or []
            if "total_scenarios" not in data or not data["total_scenarios"]:
                data["total_scenarios"] = len(scens)
            if "coverage_summary" not in data or not data["coverage_summary"]:
                data["coverage_summary"] = f"Generated {len(scens)} AI test scenarios."
        return data


SYSTEM_INSTRUCTIONS = """You are a Principal Test Automation Architect and QA Scenario Specialist.
Your mission is to take approved software requirements and design a thorough, balanced, and comprehensive suite of test scenarios.

TEST SCENARIO STRATEGY:
1. COMPREHENSIVE COVERAGE: Synthesize diverse test scenarios covering:
   - Positive / Happy Path validation
   - Negative / Error Handling & Invalid input validation
   - Boundary & Edge Cases
   - Security, Authentication, & Access Control
   - UI / Workflow Integration
2. Maintain strict traceability: every scenario must link to its parent 'requirement_key'.
3. Avoid redundant duplicate scenarios.
4. Provide clear preconditions, explicit test objectives, and measurable expected outcomes.
5. Return only valid JSON conforming to the requested schema.
"""


class ScenarioGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent_2_scenario_generation",
            agent_name="Test Scenario Generation Agent",
            system_instructions=SYSTEM_INSTRUCTIONS,
        )

    def run(self, input_data: ScenarioGenerationInput, project_id: Optional[str] = None, target_count: Optional[int] = None) -> ScenarioGenerationOutput:
        from src.core.security.sanitizer import prompt_sanitizer

        req_summaries = []
        for r in input_data.requirements:
            req_summaries.append(
                f"Requirement ID: {r.requirement_key}\n"
                f"Title: {r.title}\n"
                f"Description: {r.description}\n"
                f"Acceptance Criteria: {'; '.join(r.acceptance_criteria)}\n"
                f"Business Rules: {'; '.join(r.business_rules)}"
            )

        combined_text = "\n\n".join(req_summaries)

        wrapped_reqs = prompt_sanitizer.wrap_untrusted_input(
            combined_text, label="approved_requirements_data"
        )

        count_instruction = ""
        if target_count:
            count_instruction = f"""
STRICT QUANTITY REQUIREMENT:
The user explicitly requested target count: EXACTLY {target_count} scenarios.
Generate EXACTLY {target_count} high-priority, high-value scenarios covering this scope. Do not generate more or fewer than {target_count}."""

        prompt = f"""Generate comprehensive test scenarios for the following approved requirements data:

{wrapped_reqs}
{count_instruction}

Ensure requirements have balanced positive, negative, boundary, validation, and security scenarios.
Return complete JSON matching the ScenarioGenerationOutput schema."""

        try:
            data = self.execute_with_llm(
                prompt=prompt,
                output_schema=ScenarioGenerationOutput,
                project_id=project_id,
            )
            from src.core.utils.json_sanitizer import normalize_to_schema
            validated = normalize_to_schema(data, ScenarioGenerationOutput)
            if not validated.scenarios:
                raise LLMGenerationError(
                    "AI scenario generation returned empty scenario list.",
                    details={"agent": self.agent_id, "project_id": project_id},
                )
            if target_count and len(validated.scenarios) > target_count:
                logger.info(f"Trimming generated scenarios to user-requested limit {target_count}.")
                validated.scenarios = validated.scenarios[:target_count]
                validated.total_scenarios = len(validated.scenarios)
            return validated
        except Exception as e:
            logger.error(f"AI Scenario Generation failed: {e}")
            raise e
