"""
Agent 3: Test Case Design Agent.
Converts approved test scenarios into detailed, executable manual & automated test cases.
Generates synthetic test data (never real customer PII) and measurable execution steps.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.agents.base.base_agent import BaseAgent
from src.agents.scenario_generation.agent import GeneratedScenario
from src.core.logging import get_logger

logger = get_logger("test_case_design_agent")


class ExecutionStep(BaseModel):
    step_number: int
    action: str
    expected: str


class GeneratedTestCase(BaseModel):
    test_case_key: str = Field(description="Unique Test Case ID like TC-001")
    scenario_key: str = Field(description="Parent Scenario ID like SCEN-001")
    requirement_key: str = Field(description="Parent Requirement ID like REQ-001")
    title: str = Field(description="Descriptive title of test case")
    objective: str = Field(description="Exact verification goal")
    test_type: str = Field(default="Functional")
    priority: str = Field(default="Medium")
    preconditions: str = Field(description="System state prior to step execution")
    test_environment: str = Field(default="QA")
    test_data: Dict[str, Any] = Field(default_factory=dict, description="Synthetic test data payload")
    execution_steps: List[ExecutionStep] = Field(description="Ordered action-expected steps")
    expected_results: str = Field(description="Final expected outcome of entire test case")
    automation_suitability: str = Field(default="Yes")
    tags: List[str] = Field(default_factory=list)


class TestCaseDesignInput(BaseModel):
    __test__ = False
    scenarios: List[GeneratedScenario]


class TestCaseDesignOutput(BaseModel):
    test_cases: List[GeneratedTestCase]
    total_test_cases: int
    summary: str


SYSTEM_INSTRUCTIONS = """You are a Senior QA Test Case Designer.
Your mission is to convert high-level test scenarios into granular, executable test cases.

QUALITY STANDARDS:
1. Every step must be unambiguous, actionable, and state clear expectations.
2. Generate SYNTHETIC test data (never real customer PII or real credentials).
3. Test data must include valid, invalid, boundary, and special character values.
4. Maintain strict traceability: reference 'scenario_key' and 'requirement_key'.
5. Clearly specify preconditions and measurable expected results.
6. Return only valid JSON conforming to the requested schema.
"""


class TestCaseDesignAgent(BaseAgent):
    __test__ = False

    def __init__(self):
        super().__init__(
            agent_id="agent_3_test_case_design",
            agent_name="Test Case Design Agent",
            system_instructions=SYSTEM_INSTRUCTIONS,
        )

    def run(self, input_data: TestCaseDesignInput, project_id: Optional[str] = None, target_count: Optional[int] = None) -> TestCaseDesignOutput:
        from src.core.security.sanitizer import prompt_sanitizer
        from src.core.utils.json_sanitizer import normalize_to_schema

        scenarios = input_data.scenarios or []
        if not scenarios:
            return TestCaseDesignOutput(test_cases=[], total_test_cases=0, summary="No scenarios provided for test case design.")

        if target_count and len(scenarios) > target_count:
            logger.info(f"Limiting input scenarios for test case design to target count {target_count}.")
            scenarios = scenarios[:target_count]

        # Batch scenarios in chunks of 5 to eliminate token exhaustion and JSON delimiter syntax truncation
        batch_size = 5
        batches = [scenarios[i : i + batch_size] for i in range(0, len(scenarios), batch_size)]
        all_test_cases: List[GeneratedTestCase] = []

        for b_idx, batch in enumerate(batches):
            scenario_prompts = []
            for s in batch:
                scenario_prompts.append(
                    f"Scenario: {s.scenario_key} (Req: {s.requirement_key})\n"
                    f"Title: {s.title}\n"
                    f"Type: {s.test_type} | Priority: {s.priority}\n"
                    f"Objective: {s.test_objective}\n"
                    f"Preconditions: {s.preconditions}\n"
                    f"Expected Outcome: {s.expected_outcome}"
                )

            wrapped_scenarios = prompt_sanitizer.wrap_untrusted_input(
                "\n\n".join(scenario_prompts), label=f"client_scenarios_batch_{b_idx + 1}"
            )

            prompt = f"""Convert these scenarios into granular, step-by-step test cases with synthetic test data:

{wrapped_scenarios}

CRITICAL RULES:
1. Return valid JSON matching TestCaseDesignOutput.
2. Ensure every test case references its parent 'scenario_key' and 'requirement_key'.
3. Include unambiguous 'execution_steps' and synthetic 'test_data'."""

            batch_succeeded = False
            try:
                data = self.execute_with_llm(
                    prompt=prompt,
                    output_schema=TestCaseDesignOutput,
                    project_id=project_id,
                )
                if data:
                    validated = normalize_to_schema(data, TestCaseDesignOutput)
                    if validated.test_cases:
                        all_test_cases.extend(validated.test_cases)
                        batch_succeeded = True
            except Exception as e:
                logger.warning(f"Batch {b_idx + 1}/{len(batches)} LLM test case design failed: {e}. Applying rule-based fallback for this batch.")

            if not batch_succeeded:
                # Deterministic Rule-Based Fallback for this batch
                for s in batch:
                    tc_idx = len(all_test_cases) + 1
                    s_lower = s.title.lower()
                    if "admin" in s_lower:
                        all_test_cases.append(
                            GeneratedTestCase(
                                test_case_key=f"TC-{tc_idx:03d}",
                                scenario_key=s.scenario_key,
                                requirement_key=s.requirement_key,
                                title="Verify Admin Role Login & Dashboard Access",
                                objective="Confirm successful authentication for Administrator with full cohort allocation privileges.",
                                test_type="Functional",
                                priority="Critical",
                                preconditions="Admin user account is provisioned in the database.",
                                test_environment="QA",
                                test_data={"username": "admin@trainmate.com", "role": "admin", "redirect_url": "/dashboard"},
                                execution_steps=[
                                    ExecutionStep(step_number=1, action="Navigate to the application login portal.", expected="Login page renders with username and password fields."),
                                    ExecutionStep(step_number=2, action="Enter valid Admin credentials: username='admin@trainmate.com'.", expected="Input fields accept credentials securely."),
                                    ExecutionStep(step_number=3, action="Click the 'Sign In' button.", expected="Authentication succeeds; token is issued."),
                                    ExecutionStep(step_number=4, action="Verify redirected URL and dashboard view.", expected="User is redirected to Admin Dashboard with cohort management controls."),
                                ],
                                expected_results="Admin user is authenticated and granted full administrative portal permissions.",
                                automation_suitability="Yes",
                                tags=["auth", "admin", "smoke"],
                            )
                        )
                    elif "trainer" in s_lower:
                        all_test_cases.append(
                            GeneratedTestCase(
                                test_case_key=f"TC-{tc_idx:03d}",
                                scenario_key=s.scenario_key,
                                requirement_key=s.requirement_key,
                                title="Verify Trainer Role Login & Schedule Access",
                                objective="Confirm successful authentication for Trainer role with assigned cohort schedule access.",
                                test_type="Functional",
                                priority="High",
                                preconditions="Trainer user account is active in the database.",
                                test_environment="QA",
                                test_data={"username": "trainer.lead@trainmate.com", "role": "trainer", "redirect_url": "/trainer/schedule"},
                                execution_steps=[
                                    ExecutionStep(step_number=1, action="Navigate to the application login portal.", expected="Login page renders successfully."),
                                    ExecutionStep(step_number=2, action="Enter valid Trainer credentials: username='trainer.lead@trainmate.com'.", expected="Credentials entered without errors."),
                                    ExecutionStep(step_number=3, action="Click the 'Sign In' button.", expected="Authentication succeeds."),
                                    ExecutionStep(step_number=4, action="Verify redirected portal view.", expected="User is redirected to Trainer Schedule view showing assigned training cohorts."),
                                ],
                                expected_results="Trainer user is authenticated and receives trainer role navigation.",
                                automation_suitability="Yes",
                                tags=["auth", "trainer", "smoke"],
                            )
                        )
                    elif "trainee" in s_lower or "student" in s_lower or "user" in s_lower:
                        all_test_cases.append(
                            GeneratedTestCase(
                                test_case_key=f"TC-{tc_idx:03d}",
                                scenario_key=s.scenario_key,
                                requirement_key=s.requirement_key,
                                title="Verify Trainee Role Login & Learning Portal Access",
                                objective="Confirm successful authentication for Trainee role with course module access.",
                                test_type="Functional",
                                priority="High",
                                preconditions="Trainee user account is enrolled in an active cohort.",
                                test_environment="QA",
                                test_data={"username": "trainee.cohort01@trainmate.com", "role": "trainee", "redirect_url": "/modules"},
                                execution_steps=[
                                    ExecutionStep(step_number=1, action="Navigate to the application login portal.", expected="Login page renders successfully."),
                                    ExecutionStep(step_number=2, action="Enter valid Trainee credentials: username='trainee.cohort01@trainmate.com'.", expected="Credentials accepted."),
                                    ExecutionStep(step_number=3, action="Click the 'Sign In' button.", expected="Authentication succeeds."),
                                    ExecutionStep(step_number=4, action="Verify redirected portal view.", expected="User is redirected to Trainee Learning Portal showing enrolled cohorts."),
                                ],
                                expected_results="Trainee user is authenticated and restricted to trainee module view.",
                                automation_suitability="Yes",
                                tags=["auth", "trainee", "smoke"],
                            )
                        )
                    elif s.test_type == "Positive":
                        all_test_cases.append(
                            GeneratedTestCase(
                                test_case_key=f"TC-{tc_idx:03d}",
                                scenario_key=s.scenario_key,
                                requirement_key=s.requirement_key,
                                title=f"{s.title} - Standard Flow",
                                objective=s.test_objective,
                                test_type="Functional",
                                priority=s.priority,
                                preconditions=s.preconditions,
                                test_environment="QA",
                                test_data={"username": "qa_tester_01@example.com", "valid_payload": True, "amount": 99.99},
                                execution_steps=[
                                    ExecutionStep(step_number=1, action="Navigate to the application page under test.", expected="Page loads completely with HTTP 200 within 2 seconds."),
                                    ExecutionStep(step_number=2, action="Fill in valid form data from test_data payload.", expected="Input fields accept entries without validation warnings."),
                                    ExecutionStep(step_number=3, action="Click the primary Submit / Action button.", expected="Submission spinner appears and request dispatches."),
                                    ExecutionStep(step_number=4, action="Inspect the resulting page state and database record.", expected="Success confirmation banner is displayed and record is stored."),
                                ],
                                expected_results=s.expected_outcome,
                                automation_suitability="Yes",
                                tags=["smoke", "regression", "core"],
                            )
                        )
                    elif s.test_type == "Negative":
                        all_test_cases.append(
                            GeneratedTestCase(
                                test_case_key=f"TC-{tc_idx:03d}",
                                scenario_key=s.scenario_key,
                                requirement_key=s.requirement_key,
                                title=f"{s.title} - Malformed & Empty Inputs",
                                objective=s.test_objective,
                                test_type="Negative",
                                priority=s.priority,
                                preconditions=s.preconditions,
                                test_data={"username": "", "invalid_email": "bad_email_format", "special_chars": "'; DROP TABLE users;--"},
                                execution_steps=[
                                    ExecutionStep(step_number=1, action="Navigate to the form or interface under test.", expected="Form is displayed with clean inputs."),
                                    ExecutionStep(step_number=2, action="Submit form leaving required fields empty.", expected="Validation alerts highlight required missing fields."),
                                    ExecutionStep(step_number=3, action="Enter malformed data from test_data and click submit.", expected="Inline error appears: 'Please enter a valid format'."),
                                ],
                                expected_results="Form is not submitted and clear validation messages guide the user.",
                                automation_suitability="Yes",
                                tags=["negative", "validation"],
                            )
                        )
                    else:
                        all_test_cases.append(
                            GeneratedTestCase(
                                test_case_key=f"TC-{tc_idx:03d}",
                                scenario_key=s.scenario_key,
                                requirement_key=s.requirement_key,
                                title=f"{s.title} - Boundary & Security Verification",
                                objective=s.test_objective,
                                test_type=s.test_type,
                                priority=s.priority,
                                preconditions=s.preconditions,
                                test_data={"boundary_min": 1, "boundary_max": 255, "overflow": "A" * 300},
                                execution_steps=[
                                    ExecutionStep(step_number=1, action="Navigate to the target endpoint or interface.", expected="Interface renders."),
                                    ExecutionStep(step_number=2, action="Supply maximum boundary length string.", expected="System accepts maximum boundary value safely."),
                                    ExecutionStep(step_number=3, action="Supply string exceeding boundary limit.", expected="Client prevents further typing or API responds with 422 Unprocessable Entity."),
                                ],
                                expected_results=s.expected_outcome,
                                automation_suitability="Yes",
                                tags=["boundary", "security"],
                            )
                        )

        if target_count and len(all_test_cases) > target_count:
            logger.info(f"Capping designed test cases from {len(all_test_cases)} to target count {target_count}.")
            all_test_cases = all_test_cases[:target_count]

        # Normalize test case keys consecutively
        for idx, tc in enumerate(all_test_cases, start=1):
            tc.test_case_key = f"TC-{idx:03d}"

        return TestCaseDesignOutput(
            test_cases=all_test_cases,
            total_test_cases=len(all_test_cases),
            summary=f"Designed {len(all_test_cases)} actionable test cases with synthetic test datasets across {len(batches)} batches.",
        )
