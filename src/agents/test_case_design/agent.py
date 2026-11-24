"""
Agent 3: Test Case Design Agent.
Converts approved test scenarios into detailed, executable manual & automated test cases.
Generates synthetic test data (never real customer PII) and measurable execution steps.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from src.agents.base.base_agent import BaseAgent
from src.agents.scenario_generation.agent import GeneratedScenario
from src.core.logging import get_logger
from src.core.exceptions import LLMGenerationError

logger = get_logger("test_case_design_agent")


class ExecutionStep(BaseModel):
    step_number: int = 1
    action: str = ""
    expected: str = ""

    @model_validator(mode="before")
    @classmethod
    def reconcile_execution_step(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"step_number": 1, "action": data, "expected": "Step succeeds without error"}
        if isinstance(data, dict):
            num = data.get("step_number") or data.get("number") or data.get("step") or 1
            act = data.get("action") or data.get("description") or data.get("step_description") or ""
            exp = data.get("expected") or data.get("expected_result") or data.get("expected_outcome") or "Step completed"
            return {"step_number": int(num) if str(num).isdigit() else 1, "action": str(act), "expected": str(exp)}
        return data


class GeneratedTestCase(BaseModel):
    test_case_key: str = Field(default="TC-001", description="Unique Test Case ID like TC-001")
    scenario_key: str = Field(default="SCEN-001", description="Parent Scenario ID like SCEN-001")
    requirement_key: str = Field(default="REQ-001", description="Parent Requirement ID like REQ-001")
    title: str = Field(default="Verification of test scenario", description="Descriptive title of test case")
    objective: str = Field(default="", description="Exact verification goal")
    test_type: str = Field(default="Functional")
    priority: str = Field(default="Medium")
    preconditions: str = Field(default="", description="System state prior to step execution")
    test_environment: str = Field(default="QA")
    test_data: Dict[str, Any] = Field(default_factory=dict, description="Synthetic test data payload")
    execution_steps: List[ExecutionStep] = Field(default_factory=list, description="Ordered action-expected steps")
    expected_results: str = Field(default="", description="Final expected outcome of entire test case")
    automation_suitability: str = Field(default="Yes")
    tags: List[str] = Field(default_factory=list)

    @field_validator("preconditions", "objective", "expected_results", mode="before")
    @classmethod
    def coerce_string_fields(cls, v: Any) -> str:
        if isinstance(v, list):
            return "\n".join(str(item).strip() for item in v if item is not None)
        if isinstance(v, dict):
            return ", ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    @model_validator(mode="before")
    @classmethod
    def reconcile_test_case_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Resolve steps aliases
            steps = data.get("execution_steps") or data.get("steps") or data.get("step_list") or []
            if isinstance(steps, str):
                steps = [steps]
            data["execution_steps"] = steps

            # Resolve expected results aliases
            if not data.get("expected_results"):
                data["expected_results"] = data.get("expected_result") or data.get("expected") or data.get("expected_outcome") or "Test case passes verification."

            # Resolve title alias
            if not data.get("title"):
                data["title"] = data.get("name") or data.get("test_name") or f"Verify {data.get('scenario_key', 'scenario')}"

            # Ensure test data is a dict
            if not isinstance(data.get("test_data"), dict):
                data["test_data"] = {}
        return data


class TestCaseDesignInput(BaseModel):
    __test__ = False
    scenarios: List[GeneratedScenario]


class TestCaseDesignOutput(BaseModel):
    test_cases: List[GeneratedTestCase] = Field(default_factory=list)
    total_test_cases: int = Field(default=0)
    summary: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def reconcile_test_case_output(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"test_cases": data, "total_test_cases": len(data), "summary": f"Designed {len(data)} detailed test cases."}
        if isinstance(data, dict):
            cases = data.get("test_cases") or data.get("cases") or data.get("items") or []
            data["test_cases"] = cases
            if not data.get("total_test_cases"):
                data["total_test_cases"] = len(cases)
            if not data.get("summary"):
                data["summary"] = f"Designed {len(cases)} detailed test cases."
        return data


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

            count_rule = f"\n4. Output exactly {target_count} test cases matching the scenarios." if target_count else ""

            prompt = f"""Convert these scenarios into granular, step-by-step test cases with synthetic test data:

{wrapped_scenarios}

CRITICAL RULES:
1. Return valid JSON matching TestCaseDesignOutput.
2. Ensure every test case references its parent 'scenario_key' and 'requirement_key'.
3. Include unambiguous 'execution_steps' and synthetic 'test_data'.{count_rule}"""

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
            except Exception as e:
                logger.error(f"Batch {b_idx + 1}/{len(batches)} LLM test case design failed: {e}")
                raise e

        if not all_test_cases:
            raise LLMGenerationError(
                "AI test case design returned empty test case collection.",
                details={"agent": self.agent_id, "project_id": project_id},
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
