"""
Agent 1: Requirement Analysis Agent.
Analyzes user stories, acceptance criteria, business rules, and documents.
Identifies functional/non-functional requirements, ambiguities, and edge cases.
Never invents missing business requirements.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from src.agents.base.base_agent import BaseAgent
from src.core.logging import get_logger
from src.core.exceptions import LLMGenerationError

logger = get_logger("requirement_analysis_agent")


class RequirementAnalysisInput(BaseModel):
    raw_text: str
    title: Optional[str] = "Feature Specification"
    source_type: str = "manual"  # jira, file, manual
    jira_issue_key: Optional[str] = None
    target_count: Optional[int] = None
    user_directive: Optional[str] = None


class ExtractedRequirement(BaseModel):
    requirement_key: str = Field(description="Unique requirement ID like REQ-001 or JIRA key")
    title: str = Field(description="Clear title of the requirement")
    description: str = Field(default="", description="Detailed requirement description")
    business_objective: str = Field(default="", description="Core business value or goal")
    functional_requirements: List[str] = Field(default_factory=list, description="Specific functional behaviors expected")
    non_functional_requirements: List[str] = Field(default_factory=list, description="Performance, security, usability rules")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Conditions that must be met to consider complete")
    business_rules: List[str] = Field(default_factory=list, description="Explicit constraints or business policies")
    dependencies: List[str] = Field(default_factory=list, description="External systems or predecessor requirements")
    missing_information: List[str] = Field(default_factory=list, description="Gaps or undefined behavior in requirements")
    clarification_questions: List[str] = Field(default_factory=list, description="Targeted questions for the stakeholder")
    risk_level: str = Field(default="Medium", description="Low, Medium, High, or Critical")
    priority: str = Field(default="Medium", description="Low, Medium, High, or Critical")
    testability_status: str = Field(default="Testable", description="Testable, Needs Clarification, or Untestable")

    @field_validator("description", "business_objective", mode="before")
    @classmethod
    def coerce_string_field(cls, v: Any) -> str:
        if isinstance(v, list):
            return "\n".join(str(x).strip() for x in v if x is not None)
        return str(v) if v is not None else ""

    @field_validator("functional_requirements", "acceptance_criteria", "business_rules", "non_functional_requirements", mode="before")
    @classmethod
    def coerce_list_field(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [line.strip("- *").strip() for line in v.splitlines() if line.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item is not None]
        return []


class RequirementAnalysisOutput(BaseModel):
    requirements: List[ExtractedRequirement] = Field(default_factory=list)
    summary: str = Field(default="")


SYSTEM_INSTRUCTIONS = """You are an expert Principal Software Testing & QA Requirements Analyst.
Your mission is to rigorously analyze requirements (user stories, SRS documents, acceptance criteria, business rules, PRDs) and extract structured, verifiable, testable requirements.

CORE PRINCIPLES:
1. COMPREHENSIVE EXTRACTION: Extract all distinct functional and non-functional requirements from the submitted specification without arbitrary truncation.
2. PRESERVE GROUND TRUTH: Never invent missing business requirements outside the provided specification.
3. IDENTIFY GAPS HONESTLY: If requirements are ambiguous or incomplete, document the exact ambiguities under 'missing_information' and provide targeted 'clarification_questions'.
4. STRUCTURED DETAIL: For each requirement, extract clear acceptance criteria, functional behaviors, business rules, and non-functional constraints (security, performance, usability).
5. If the user gave an explicit scoping directive (e.g., 'focus on checkout' or 'generate 5 tests'), prioritize and highlight those features while maintaining traceability.
6. Return only valid JSON conforming to the requested schema.
"""


class RequirementAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent_1_requirement_analysis",
            agent_name="Requirement Analysis Agent",
            system_instructions=SYSTEM_INSTRUCTIONS,
        )

    def run(self, input_data: RequirementAnalysisInput, project_id: Optional[str] = None) -> RequirementAnalysisOutput:
        from src.core.security.sanitizer import prompt_sanitizer

        wrapped_requirements = prompt_sanitizer.wrap_untrusted_input(
            input_data.raw_text, label=f"client_requirement_{input_data.source_type}"
        )

        scoping_prompt = ""
        if input_data.user_directive:
            scoping_prompt = f"""
EXPLICIT USER TESTING INSTRUCTION:
"{input_data.user_directive}"
Ensure requirements directly address this testing instruction with highest priority."""

        prompt = f"""Please analyze the following software requirements data:

Source Type: {input_data.source_type}
Issue Key: {input_data.jira_issue_key or 'N/A'}
Title: {input_data.title}

{scoping_prompt}

{wrapped_requirements}

ANALYSIS GUIDELINES:
1. Extract all verifiable functional and non-functional requirements systematically.
2. Group related functionality into logical requirements with keys REQ-001, REQ-002, etc. (or keep Jira keys if provided).
3. Identify all actors, user journeys, business rules, and acceptance criteria.
4. If details are missing or ambiguous, list them under 'missing_information' and 'clarification_questions'.
5. Return complete JSON matching the RequirementAnalysisOutput schema."""

        try:
            data = self.execute_with_llm(
                prompt=prompt,
                output_schema=RequirementAnalysisOutput,
                project_id=project_id,
            )
            from src.core.utils.json_sanitizer import normalize_to_schema
            validated = normalize_to_schema(data, RequirementAnalysisOutput)
            if not validated.requirements:
                raise LLMGenerationError(
                    "AI requirement analysis returned empty requirements collection.",
                    details={"agent": self.agent_id, "project_id": project_id},
                )
            return validated
        except Exception as e:
            logger.error(f"AI Requirement Analysis failed: {e}")
            raise e
