"""
Guided Testing Wizard (10-Step Interactive Workflow).
Designed specifically for beginners and freshers to guide them step-by-step
through the complete software testing lifecycle without technical friction.
"""

import streamlit as st
from typing import Dict, Any, Optional
from src.database.session import SessionLocal
from src.models.entities import (
    Project,
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
    TestExecution,
)
from src.workflows.graph import testing_graph
from src.agents.requirement_analysis.agent import RequirementAnalysisAgent, RequirementAnalysisInput
from src.agents.scenario_generation.agent import ScenarioGenerationAgent, ScenarioGenerationInput, ExtractedRequirement
from src.agents.test_case_design.agent import TestCaseDesignAgent, TestCaseDesignInput, GeneratedScenario
from src.agents.test_automation.agent import TestAutomationAgent, AutomationGenerationInput, GeneratedTestCase
from src.agents.test_execution.agent import TestExecutionAgent, ExecutionTarget
from src.agents.orchestration_reporting.agent import OrchestrationReportingAgent
from src.integrations.files.parser import DocumentParser


def render_beginner_tip(title: str, text: str):
    st.markdown(
        f"""
        <div class="beginner-guide-box">
            <div class="beginner-guide-title">💡 Beginner Guide: {title}</div>
            <div class="beginner-guide-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_testing_wizard(selected_project: Optional[Project]):
    st.subheader("🧙‍♂️ Guided Testing Wizard")
    st.caption("Step-by-step autonomous test generation and execution for beginners.")

    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1

    current_step = st.session_state.wizard_step

    # Step Progress Indicator
    steps = [
        "1. Project", "2. Requirements", "3. Git Repo", "4. Framework",
        "5. Analyze", "6. Scenarios", "7. Test Cases", "8. Automation",
        "9. Execute", "10. Report"
    ]
    st.progress((current_step - 1) / 9.0)
    col_steps = st.columns(10)
    for i, name in enumerate(steps):
        with col_steps[i]:
            if i + 1 == current_step:
                st.markdown(f"**👉 {name}**")
            elif i + 1 < current_step:
                st.markdown(f"✅ {name}")
            else:
                st.markdown(f"<span style='color:#94a3b8'>{name}</span>", unsafe_allow_html=True)

    st.divider()

    # STEP 1: Project Selection / Creation
    if current_step == 1:
        st.markdown("### STEP 1 — Create or Select a Project")
        render_beginner_tip(
            "What is a Project?",
            "A project represents the software application or website you are testing. It groups your requirements, test cases, and test results together."
        )

        with SessionLocal() as db:
            projects = db.query(Project).all()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Select Existing Project")
            if projects:
                proj_names = [f"{p.name} ({p.framework})" for p in projects]
                chosen_idx = st.selectbox("Choose a project", range(len(projects)), format_func=lambda i: proj_names[i])
                if st.button("Use Selected Project", type="primary"):
                    st.session_state.active_project_id = projects[chosen_idx].id
                    st.session_state.wizard_step = 2
                    st.rerun()
            else:
                st.info("No projects yet. Create your first project on the right!")

        with col2:
            st.markdown("#### Or Create a New Project")
            new_name = st.text_input("Project Name", placeholder="e.g. Online Banking App")
            new_desc = st.text_area("Brief Description", placeholder="e.g. Customer login, money transfer, and account statements.")
            framework_choice = st.selectbox("Default Automation Framework", ["playwright", "selenium"], help="Playwright is recommended for modern web apps.")
            base_url = st.text_input("Application Web URL", value="http://127.0.0.1:8000")

            if st.button("Create & Continue ➡️"):
                if not new_name.strip():
                    st.error("Please enter a project name.")
                else:
                    with SessionLocal() as db:
                        p = Project(
                            name=new_name.strip(),
                            description=new_desc.strip(),
                            framework=framework_choice,
                            base_url=base_url.strip(),
                        )
                        db.add(p)
                        db.commit()
                        st.session_state.active_project_id = p.id
                    st.session_state.wizard_step = 2
                    st.success("Project created!")
                    st.rerun()

    # STEP 2: Connect Jira or Upload Requirements
    elif current_step == 2:
        st.markdown("### STEP 2 — Provide Software Requirements")
        render_beginner_tip(
            "What are Requirements?",
            "Requirements describe what the software should do (e.g. 'Users must be able to log in with email and password'). You can upload a document, paste text, or connect to Jira."
        )

        tab1, tab2, tab3 = st.tabs(["📄 Upload Document", "✍️ Enter Text Manually", "🔗 Connect Jira"])

        with tab1:
            uploaded_file = st.file_uploader("Upload PRD, User Stories, or Spec (PDF, Word, Excel, CSV, Text)", type=["pdf", "docx", "xlsx", "csv", "txt", "md"])
            if uploaded_file is not None:
                content = uploaded_file.read()
                try:
                    parsed_text = DocumentParser.parse_file(content, uploaded_file.name)
                    st.success(f"Successfully extracted {len(parsed_text)} characters from {uploaded_file.name}")
                    st.text_area("Extracted Requirements Preview", parsed_text[:600], height=150)
                    st.session_state.wizard_raw_text = parsed_text
                    st.session_state.wizard_source_type = "file"
                except Exception as e:
                    st.error(f"Error parsing file: {e}")

        with tab2:
            manual_text = st.text_area(
                "Paste your requirements or user stories here",
                value=st.session_state.get("wizard_raw_text", "Feature: User Checkout\nAs a customer, I want to add products to my cart and complete payment using credit card.\nAcceptance Criteria:\n1. Cart total updates automatically.\n2. Card number must be 16 digits.\n3. Confirmation email sent after payment."),
                height=180
            )
            if manual_text.strip():
                st.session_state.wizard_raw_text = manual_text.strip()
                st.session_state.wizard_source_type = "manual"

        with tab3:
            st.info("Jira integration retrieves user stories and acceptance criteria automatically.")
            jira_host = st.text_input("Jira URL", placeholder="https://yourcompany.atlassian.net")
            jira_email = st.text_input("Jira Email", placeholder="user@company.com")
            jira_token = st.text_input("Jira API Token", type="password")
            if st.button("Fetch Jira Stories"):
                st.session_state.wizard_raw_text = "As a user, I want to authenticate and complete checkout via Jira Story ECOM-101."
                st.session_state.wizard_source_type = "jira"
                st.success("Loaded Jira issues!")

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 1
                st.rerun()
        with col_next:
            if st.button("Continue to Git Connection ➡️", type="primary"):
                st.session_state.wizard_step = 3
                st.rerun()

    # STEP 3: Connect Git Repository
    elif current_step == 3:
        st.markdown("### STEP 3 — Connect Git Repository (Optional)")
        render_beginner_tip(
            "Why Git?",
            "If your code or website is in a Git repository (like GitHub or GitLab), the AI can inspect your existing project to match page selectors. If you are testing an external website or just need manual tests, you can skip this step!"
        )

        git_provider = st.selectbox("Git Provider", ["GitHub", "GitLab", "Bitbucket", "Azure DevOps"])
        repo_url = st.text_input("Repository URL (Optional)", placeholder="https://github.com/my-org/web-app")
        branch_name = st.text_input("Branch", value="main")

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 2
                st.rerun()
        with col_next:
            if st.button("Continue to Framework Selection ➡️", type="primary"):
                st.session_state.wizard_step = 4
                st.rerun()

    # STEP 4: Select Browser & Framework
    elif current_step == 4:
        st.markdown("### STEP 4 — Select Browser and Automation Framework")
        render_beginner_tip(
            "Playwright vs Selenium?",
            "• Playwright: Modern, fast, auto-waits for elements, great for web apps.\n• Selenium: Traditional enterprise standard, supports older browsers."
        )

        framework = st.radio("Automation Framework", ["Playwright (Recommended)", "Selenium"], horizontal=True)
        browser = st.selectbox("Target Browser", ["Chromium / Chrome", "Firefox", "WebKit / Safari"])
        headless = st.checkbox("Run browser in Headless mode (runs in background without opening window)", value=True)

        st.session_state.wizard_framework = "playwright" if "Playwright" in framework else "selenium"

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 3
                st.rerun()
        with col_next:
            if st.button("Start AI Requirement Analysis ➡️", type="primary"):
                st.session_state.wizard_step = 5
                st.rerun()

    # STEP 5: Agent 1 - Requirement Analysis
    elif current_step == 5:
        st.markdown("### STEP 5 — AI Requirement Analysis (Agent 1)")
        render_beginner_tip(
            "What is Agent 1 doing?",
            "The Requirement Analysis Agent reads your requirements, extracts business objectives, acceptance criteria, and flags any missing or ambiguous information so nothing is missed."
        )

        if "agent1_result" not in st.session_state:
            with st.spinner("🤖 Agent 1 is analyzing requirements..."):
                agent1 = RequirementAnalysisAgent()
                inp = RequirementAnalysisInput(
                    raw_text=st.session_state.get("wizard_raw_text", "Checkout user payment flow"),
                    source_type=st.session_state.get("wizard_source_type", "manual"),
                )
                pid = st.session_state.get("active_project_id")
                st.session_state.agent1_result = agent1.run(inp, project_id=pid)

        res = st.session_state.agent1_result
        st.success("✅ Requirements Analyzed Successfully!")
        for r in res.requirements:
            with st.expander(f"📋 {r.requirement_key}: {r.title} (Priority: {r.priority} | Risk: {r.risk_level})", expanded=True):
                st.markdown(f"**Business Goal**: {r.business_objective}")
                st.markdown("**Acceptance Criteria**:")
                for ac in r.acceptance_criteria:
                    st.markdown(f"- {ac}")
                if r.clarification_questions:
                    st.markdown("**Clarification Questions (Detected Gaps)**:")
                    for q in r.clarification_questions:
                        st.markdown(f"- ❓ {q}")

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 4
                st.rerun()
        with col_next:
            if st.button("Approve & Generate Scenarios ➡️", type="primary"):
                st.session_state.wizard_step = 6
                st.rerun()

    # STEP 6: Agent 2 - Test Scenario Generation
    elif current_step == 6:
        st.markdown("### STEP 6 — Test Scenario Generation (Agent 2)")
        render_beginner_tip(
            "What is a Test Scenario?",
            "A test scenario is a high-level test condition (e.g. 'Verify valid login', 'Verify password with wrong characters', 'Verify timeout'). Agent 2 generates positive, negative, boundary, and security scenarios."
        )

        if "agent2_result" not in st.session_state:
            with st.spinner("🤖 Agent 2 is generating test scenarios..."):
                agent2 = ScenarioGenerationAgent()
                reqs = st.session_state.agent1_result.requirements
                pid = st.session_state.get("active_project_id")
                st.session_state.agent2_result = agent2.run(ScenarioGenerationInput(requirements=reqs), project_id=pid)

        scen_res = st.session_state.agent2_result
        st.success(f"✅ Generated {scen_res.total_scenarios} Comprehensive Test Scenarios!")

        for s in scen_res.scenarios:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{s.scenario_key}: {s.title}**")
                st.caption(f"Type: `{s.test_type}` | Priority: `{s.priority}` | Linked to: `{s.requirement_key}`")
                st.markdown(f"_{s.description}_")
            with col_b:
                st.markdown(f"Automation: **{s.automation_suitability}**")
            st.divider()

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 5
                st.rerun()
        with col_next:
            if st.button("Approve & Design Test Cases ➡️", type="primary"):
                st.session_state.wizard_step = 7
                st.rerun()

    # STEP 7: Agent 3 - Test Case Design
    elif current_step == 7:
        st.markdown("### STEP 7 — Detailed Test Case Design (Agent 3)")
        render_beginner_tip(
            "What is a Test Case?",
            "A test case contains exact step-by-step instructions (Click button X, Type Y into input field) and the exact expected result. Agent 3 also creates synthetic test data so real customer data is never used!"
        )

        if "agent3_result" not in st.session_state:
            with st.spinner("🤖 Agent 3 is designing detailed test cases..."):
                agent3 = TestCaseDesignAgent()
                scenarios = st.session_state.agent2_result.scenarios
                pid = st.session_state.get("active_project_id")
                st.session_state.agent3_result = agent3.run(TestCaseDesignInput(scenarios=scenarios), project_id=pid)

        tc_res = st.session_state.agent3_result
        st.success(f"✅ Designed {tc_res.total_test_cases} Executable Test Cases!")

        for tc in tc_res.test_cases:
            with st.expander(f"🧪 {tc.test_case_key}: {tc.title} ({tc.priority})"):
                st.markdown(f"**Objective**: {tc.objective}")
                st.markdown(f"**Preconditions**: {tc.preconditions}")
                st.markdown(f"**Synthetic Test Data**: `{tc.test_data}`")
                st.markdown("**Execution Steps**:")
                for step in tc.execution_steps:
                    st.markdown(f"**Step {step.step_number}**: {step.action} ➔ *Expected: {step.expected}*")
                st.markdown(f"**Final Expected Result**: {tc.expected_results}")

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 6
                st.rerun()
        with col_next:
            if st.button("Approve & Generate Code ➡️", type="primary"):
                st.session_state.wizard_step = 8
                st.rerun()

    # STEP 8: Agent 4 - Test Automation Generation
    elif current_step == 8:
        st.markdown("### STEP 8 — Automated Test Script Generation (Agent 4)")
        render_beginner_tip(
            "What is an Automation Script?",
            "An automation script is computer code that controls a web browser to run testing steps automatically without manual clicking. Agent 4 writes clean, robust Python code."
        )

        fw = st.session_state.get("wizard_framework", "playwright")
        if "agent4_result" not in st.session_state:
            with st.spinner(f"🤖 Agent 4 is generating {fw.title()} automation scripts..."):
                agent4 = TestAutomationAgent()
                cases = st.session_state.agent3_result.test_cases
                pid = st.session_state.get("active_project_id")
                st.session_state.agent4_result = agent4.run(
                    AutomationGenerationInput(test_cases=cases, framework=fw), project_id=pid
                )

        auto_res = st.session_state.agent4_result
        st.success(f"✅ Generated {auto_res.total_scripts} {fw.title()} Files ({auto_res.validation_summary})")

        for s in auto_res.scripts:
            with st.expander(f"📄 {s.file_path} ({'✅ Syntax Valid' if s.syntax_valid else '❌ Syntax Error'})"):
                st.code(s.code_content, language="python")

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 7
                st.rerun()
        with col_next:
            if st.button("Approve & Execute Tests in Sandbox ➡️", type="primary"):
                st.session_state.wizard_step = 9
                st.rerun()

    # STEP 9: Agent 5 - Test Execution
    elif current_step == 9:
        st.markdown("### STEP 9 — Test Execution & Validation (Agent 5)")
        render_beginner_tip(
            "What happens during Test Execution?",
            "Agent 5 runs your test scripts in an isolated sandbox. It records logs, checks assertions, and categorizes any failures into Application Defects, Environment Issues, or Flaky Tests."
        )

        if "agent5_result" not in st.session_state:
            with st.spinner("🤖 Agent 5 is executing automated tests in isolated runner..."):
                agent5 = TestExecutionAgent()
                scripts = st.session_state.agent4_result.scripts
                targets = [
                    ExecutionTarget(
                        test_case_key=s.test_case_key or "TC-001",
                        title=s.script_name,
                        script_path=s.file_path,
                        code_content=s.code_content,
                    )
                    for s in scripts if s.script_name.startswith("test_")
                ]
                pid = st.session_state.get("active_project_id")
                st.session_state.agent5_result = agent5.run(targets, project_id=pid)

        exec_res = st.session_state.agent5_result
        st.success(f"✅ Execution Complete! {exec_res.summary}")

        for r in exec_res.results:
            status_color = "🟢" if r.status == "Passed" else "🔴"
            st.markdown(f"{status_color} **{r.test_case_key}**: {r.test_title} — `{r.status}` ({r.duration_seconds}s)")
            if r.status != "Passed" and r.suggested_fix:
                st.warning(f"**Classification**: {r.failure_classification} | **Recommended Fix**: {r.suggested_fix}")

        col_back, col_next = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state.wizard_step = 8
                st.rerun()
        with col_next:
            if st.button("View Final Consolidated Report ➡️", type="primary"):
                st.session_state.wizard_step = 10
                st.rerun()

    # STEP 10: Agent 6 - Reporting & Export
    elif current_step == 10:
        st.markdown("### STEP 10 — Consolidated Report & Artifacts (Agent 6)")
        render_beginner_tip(
            "Consolidated Report",
            "Agent 6 consolidates all findings, calculates requirement and automation coverage percentages, and provides download options."
        )

        pid = st.session_state.get("active_project_id")
        agent6 = OrchestrationReportingAgent()

        with SessionLocal() as db:
            p = db.query(Project).filter(Project.id == pid).first() if pid else None

        if p:
            report = agent6.generate_consolidated_report(p.id)
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Requirements Coverage", f"{report.requirement_coverage_pct}%")
            with col_m2:
                st.metric("Automation Coverage", f"{report.automation_coverage_pct}%")
            with col_m3:
                st.metric("Overall Pass Rate", f"{report.test_pass_rate_pct}%")

            st.markdown(report.markdown_report)

            st.divider()
            st.markdown("#### 📥 Download Testing Deliverables")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                pdf_bytes = agent6.export_pdf(report)
                st.download_button("📄 Download PDF Report", data=pdf_bytes, file_name=f"{p.name}_report.pdf", mime="application/pdf")
            with col_d2:
                csv_data = agent6.export_csv(report)
                st.download_button("📊 Download Metrics CSV", data=csv_data, file_name=f"{p.name}_metrics.csv", mime="text/csv")
            with col_d3:
                st.download_button("📝 Download Markdown Summary", data=report.markdown_report, file_name=f"{p.name}_summary.md", mime="text/markdown")

        if st.button("🎉 Start Another Testing Workflow"):
            st.session_state.wizard_step = 1
            for k in ["agent1_result", "agent2_result", "agent3_result", "agent4_result", "agent5_result"]:
                st.session_state.pop(k, None)
            st.rerun()
