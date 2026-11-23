"""
Agent 2: Test Scenario Generation Agent.
Converts approved requirements into comprehensive test scenarios:
Positive, Negative, Boundary, Security, Edge-Case, and Integration scenarios.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.agents.base.base_agent import BaseAgent
from src.agents.requirement_analysis.agent import ExtractedRequirement
from src.core.logging import get_logger

logger = get_logger("scenario_generation_agent")


class GeneratedScenario(BaseModel):
    scenario_key: str = Field(description="Unique scenario ID like SCEN-001")
    requirement_key: str = Field(description="Traceable reference to parent requirement ID")
    title: str = Field(description="Concise scenario title")
    description: str = Field(description="What is being validated and under what conditions")
    test_type: str = Field(description="Positive, Negative, Boundary, Security, UI, API, or Edge Case")
    preconditions: str = Field(description="Initial system state required before test begins")
    test_objective: str = Field(description="The explicit goal of this test scenario")
    priority: str = Field(default="Medium", description="Low, Medium, High, or Critical")
    risk: str = Field(default="Medium", description="Low, Medium, High, or Critical")
    expected_outcome: str = Field(description="High-level expected system response")
    automation_suitability: str = Field(default="Yes", description="Yes, No, or Partial")


class ScenarioGenerationInput(BaseModel):
    requirements: List[ExtractedRequirement]


class ScenarioGenerationOutput(BaseModel):
    scenarios: List[GeneratedScenario]
    total_scenarios: int
    coverage_summary: str


SYSTEM_INSTRUCTIONS = """You are a Principal Test Automation Architect and QA Scenario Specialist.
Your mission is to take approved software requirements and design a thorough, balanced suite of test scenarios.

TEST SCENARIO STRATEGY:
1. STRICT USER COUNT & SCOPE COMPLIANCE:
   - If the user requirements specify an explicit count or target (e.g. "create only 3 login tests with three different roles", "3 scenarios", "limit to 5"), you MUST generate EXACTLY that requested number of scenarios!
   - NEVER generate dozens of unrequested scenarios when the user explicitly asked for a small specific set.
2. If no count is specified, generate balanced Positive, Negative, Boundary, and Security scenarios.
3. Maintain strict traceability: every scenario must link to its parent 'requirement_key'.
4. Do not generate redundant duplicate scenarios.
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
        import re

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
        
        # Auto-detect target count from text if not explicitly provided
        if target_count is None:
            match = re.search(r'\b(?:only|generate|create|limit\s+to|at\s+most)\s+(\d+)\s*(?:login\s+)?tests?\b', combined_text, re.IGNORECASE)
            if match:
                target_count = int(match.group(1))

        wrapped_reqs = prompt_sanitizer.wrap_untrusted_input(
            combined_text, label="approved_requirements_data"
        )

        count_instruction = ""
        if target_count:
            count_instruction = f"""
STRICT QUANTITY REQUIREMENT:
The user explicitly requested EXACTLY {target_count} tests/scenarios.
You MUST output EXACTLY {target_count} scenarios and NO MORE!
For example, if 3 different roles are requested, output exactly 3 scenarios (one for each role).
Do NOT generate extra boundary or negative scenarios that exceed the {target_count} scenario limit!"""

        prompt = f"""Generate test scenarios for the following approved requirements data:

{wrapped_reqs}
{count_instruction}

If no specific count is requested, ensure requirements have positive, negative, and boundary scenarios.
Return complete JSON matching the ScenarioGenerationOutput schema."""

        try:
            data = self.execute_with_llm(
                prompt=prompt,
                output_schema=ScenarioGenerationOutput,
                project_id=project_id,
            )
            from src.core.utils.json_sanitizer import normalize_to_schema
            validated = normalize_to_schema(data, ScenarioGenerationOutput)
            if validated.scenarios:
                if target_count and len(validated.scenarios) > target_count:
                    logger.info(f"Capping generated scenarios from {len(validated.scenarios)} to user-requested limit {target_count}.")
                    validated.scenarios = validated.scenarios[:target_count]
                    validated.total_scenarios = len(validated.scenarios)
                return validated
        except Exception as e:
            logger.warning(f"Scenario generation LLM fell back to rule-based generator: {e}")

        # Deterministic Rule-Based Fallback
        scenarios = []
        counter = 1
        is_auth_intent = any(k in combined_text.lower() for k in ["role", "auth", "login"])
        
        for r in input_data.requirements:
            r_title_lower = r.title.lower()
            if (target_count and target_count <= 3) and (is_auth_intent or "role" in r_title_lower or "auth" in r_title_lower or "login" in r_title_lower):
                role_defs = [
                    ("Admin", "Verify successful login and administrative dashboard access with valid Admin credentials.", "Positive"),
                    ("Trainer", "Verify successful login and cohort schedule access with valid Trainer credentials.", "Positive"),
                    ("Trainee", "Verify successful login and module progress access with valid Trainee credentials.", "Positive"),
                ]
                for role_name, role_desc, role_type in role_defs:
                    scenarios.append(
                        GeneratedScenario(
                            scenario_key=f"SCEN-{counter:03d}",
                            requirement_key=r.requirement_key,
                            title=f"Verify {role_name} Role Login - {r.title}",
                            description=role_desc,
                            test_type=role_type,
                            preconditions=f"User has valid {role_name} credentials and target environment is online.",
                            test_objective=f"Confirm that {role_name} can log in successfully and receives correct role authorization.",
                            priority="High",
                            risk="High",
                            expected_outcome=f"{role_name} authenticated successfully and redirected to role home.",
                            automation_suitability="Yes",
                        )
                    )
                    counter += 1
            else:
                # 1. Positive Happy Path
                scenarios.append(
                    GeneratedScenario(
                        scenario_key=f"SCEN-{counter:03d}",
                        requirement_key=r.requirement_key,
                        title=f"Verify Happy Path - {r.title}",
                        description=f"Validate that user can successfully complete {r.title} with valid standard inputs.",
                        test_type="Positive",
                        preconditions="User is authenticated and system is in normal operational state.",
                        test_objective=f"Confirm core business goal: {r.business_objective}",
                        priority="High",
                        risk="High",
                        expected_outcome="Operation completes successfully with positive feedback to user.",
                        automation_suitability="Yes",
                    )
                )
                counter += 1

                # 2. Negative Validation
                scenarios.append(
                    GeneratedScenario(
                        scenario_key=f"SCEN-{counter:03d}",
                        requirement_key=r.requirement_key,
                        title=f"Verify Error Handling on Invalid Input - {r.title}",
                        description="Validate system response when mandatory fields are missing or format is malformed.",
                        test_type="Negative",
                        preconditions="User accesses the feature page.",
                        test_objective="Ensure user-friendly validation error is displayed without system crash.",
                        priority="High",
                        risk="Medium",
                        expected_outcome="Clear validation error displayed; transaction blocked.",
                        automation_suitability="Yes",
                    )
                )
                counter += 1

                # 3. Boundary & Edge Case
                scenarios.append(
                    GeneratedScenario(
                        scenario_key=f"SCEN-{counter:03d}",
                        requirement_key=r.requirement_key,
                        title=f"Boundary & Character Limit Checks - {r.title}",
                        description="Submit data at minimum boundary, maximum boundary, and exceeding maximum length.",
                        test_type="Boundary",
                        preconditions="System ready for input.",
                        test_objective="Verify boundary enforcement and buffer overflow protections.",
                        priority="Medium",
                        risk="Medium",
                        expected_outcome="Inputs exceeding limits are truncated or rejected with boundary warning.",
                        automation_suitability="Yes",
                    )
                )
                counter += 1

            # 4. Security & Authorization
            scenarios.append(
                GeneratedScenario(
                    scenario_key=f"SCEN-{counter:03d}",
                    requirement_key=r.requirement_key,
                    title=f"Unauthorized Access & Session Expiry - {r.title}",
                    description="Attempt execution with expired authentication token or invalid privileges.",
                    test_type="Security",
                    preconditions="Session token is invalidated or user has read-only role.",
                    test_objective="Prevent unauthorized actions and enforce role-based access control.",
                    priority="High",
                    risk="Critical",
                    expected_outcome="HTTP 401/403 or immediate redirect to login; no data exposed.",
                    automation_suitability="Yes",
                )
            )
            counter += 1

        if target_count and len(scenarios) > target_count:
            scenarios = scenarios[:target_count]

        return ScenarioGenerationOutput(
            scenarios=scenarios,
            total_scenarios=len(scenarios),
            coverage_summary=f"Generated {len(scenarios)} balanced scenarios covering positive, negative, boundary, and security test types.",
        )
