"""
Streamlit Web Application Entrypoint for Testing Agent Platform.
Matches the clean, modern SaaS layout of the reference dashboard screenshot.
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.database.session import SessionLocal, init_db
from src.models.entities import (
    Project,
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
    TestExecution,
)
from src.llm.registry.model_registry import model_registry
from src.llm.router.agent_model_router import agent_model_router
from src.integrations.jira.jira_client import JiraClient
from src.integrations.git.git_client import GitClient
from src.integrations.files.parser import DocumentParser

from ui.style import get_custom_css
from ui.components.header import render_top_header
from ui.components.kpi_cards import render_kpi_cards
from ui.components.charts import create_results_donut_chart, create_execution_trend_chart
from ui.components.suites_table import render_suites_table
from ui.components.activity_feed import render_activity_feed
from ui.components.wizard import render_testing_wizard

# Page configuration
st.set_page_config(
    page_title="AI Testing Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Ensure Database Tables Exist
init_db()


def seed_demo_data_if_empty():
    """Initializes sample projects and test suites if the database is fresh."""
    with SessionLocal() as db:
        if db.query(Project).count() == 0:
            demo_proj = Project(
                name="E-Commerce Checkout Suite",
                description="End-to-end testing suite for shopping cart, checkout, payment gateway, and order confirmation.",
                framework="playwright",
                jira_project_key="ECOM",
                base_url="https://demo.ecom.test",
            )
            db.add(demo_proj)
            db.commit()
            db.refresh(demo_proj)

            # Add demo requirements
            r1 = Requirement(
                project_id=demo_proj.id,
                requirement_key="REQ-101",
                title="Credit Card Payment Processing",
                description="Customer can complete checkout with Visa, MasterCard, or Amex.",
                business_objective="Frictionless checkout experience with PCI-DSS compliance.",
                functional_requirements=["16-digit card validation", "CVV verification", "3D Secure auth"],
                acceptance_criteria=["Immediate payment receipt", "Auto-clear shopping cart"],
                is_approved=True,
            )
            db.add(r1)
            db.commit()
            db.refresh(r1)

            # Add demo scenarios
            s1 = TestScenario(
                project_id=demo_proj.id,
                requirement_id=r1.id,
                scenario_key="SCEN-001",
                title="Checkout Completion Flow",
                description="Valid card payment with standard billing address.",
                test_type="Positive",
                expected_outcome="Order ID generated and confirmation screen rendered.",
                is_approved=True,
            )
            s2 = TestScenario(
                project_id=demo_proj.id,
                requirement_id=r1.id,
                scenario_key="SCEN-002",
                title="Lead Management Flow",
                description="Capture incomplete checkouts as lead recovery opportunities.",
                test_type="Functional",
                expected_outcome="Cart abandonment lead logged in CRM.",
                is_approved=True,
            )
            s3 = TestScenario(
                project_id=demo_proj.id,
                requirement_id=r1.id,
                scenario_key="SCEN-003",
                title="API Integration Suite",
                description="Payment gateway webhook listener response times.",
                test_type="API",
                expected_outcome="HTTP 200 within 500ms.",
                is_approved=True,
            )
            db.add_all([s1, s2, s3])
            db.commit()

            # Add demo execution run
            exec1 = TestExecution(
                project_id=demo_proj.id,
                execution_key="RUN-247",
                runner_type="playwright",
                total_tests=247,
                passed_tests=181,
                failed_tests=50,
                skipped_tests=16,
                execution_duration_seconds=42.5,
                status="Completed",
            )
            db.add(exec1)
            db.commit()


seed_demo_data_if_empty()


# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:0.6rem; padding-bottom:1rem; border-bottom:1px solid #f1f5f9;">
            <div style="background:#0f172a; color:white; font-size:0.8rem; font-weight:700; width:32px; height:32px; border-radius:6px; display:flex; align-items:center; justify-content:center;">
                MP
            </div>
            <div>
                <div style="font-weight:700; font-size:0.95rem; color:#0f172a;">My Project</div>
                <div style="font-size:0.75rem; color:#64748b;">Enterprise Workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Project Selector
    with SessionLocal() as db:
        all_projects = db.query(Project).all()

    proj_map = {p.id: p.name for p in all_projects}
    if all_projects:
        selected_id = st.selectbox(
            "Active Project",
            options=list(proj_map.keys()),
            format_func=lambda pid: proj_map[pid],
            label_visibility="collapsed",
        )
        current_project = next((p for p in all_projects if p.id == selected_id), None)
    else:
        current_project = None

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

    # Sidebar Navigation Radios
    st.markdown("<div style='font-size:0.7rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em;'>Main</div>", unsafe_allow_html=True)
    nav_main = st.radio(
        "Main Navigation",
        ["Dashboard", "Test Suites", "Test Plans"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='font-size:0.7rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-top:1rem;'>Agents</div>", unsafe_allow_html=True)
    nav_agents = st.radio(
        "Agents Navigation",
        [
            "1. Requirement Analysis",
            "2. Scenario Generation",
            "3. Test Case Design",
            "4. Test Automation",
            "5. Test Execution",
            "6. Orchestration & Reporting",
        ],
        label_visibility="collapsed",
        index=None,
    )

    st.markdown("<div style='font-size:0.7rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-top:1rem;'>Execution</div>", unsafe_allow_html=True)
    nav_exec = st.radio(
        "Execution Navigation",
        ["Start Testing (Wizard)", "Test Runs"],
        label_visibility="collapsed",
        index=None,
    )

    st.markdown("<div style='font-size:0.7rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-top:1rem;'>Settings</div>", unsafe_allow_html=True)
    nav_settings = st.radio(
        "Settings Navigation",
        ["AI Model Engine", "Integrations", "Environments"],
        label_visibility="collapsed",
        index=None,
    )

    # Determine Active View
    if nav_settings:
        active_view = nav_settings
    elif nav_exec:
        active_view = nav_exec
    elif nav_agents:
        active_view = nav_agents
    else:
        active_view = nav_main

    # Bottom User Pill
    st.markdown(
        """
        <div style="position:fixed; bottom:1rem; left:1rem; width:16rem; display:flex; align-items:center; gap:0.6rem; padding:0.5rem; background:#f8fafc; border-radius:8px;">
            <div style="background:#ef4444; color:white; font-size:0.75rem; font-weight:700; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center;">
                AH
            </div>
            <div>
                <div style="font-weight:600; font-size:0.85rem; color:#0f172a;">Abdul Hameed</div>
                <div style="font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase;">ENTERPRISE PLAN</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- TOP BAR ---
render_top_header()


# --- VIEW ROUTING ---

# 1. MAIN DASHBOARD VIEW (Exact Replica of Reference Screenshot)
if active_view == "Dashboard":
    # 4 KPI Cards
    render_kpi_cards(
        test_suites=2,
        scenarios=3,
        schedules=0,
        run_history=247,
        passed=181,
        failed=50,
        success_rate=73.0,
    )

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    # Analytics Middle Row (Donut Chart & Trend Chart)
    col_donut, col_trend = st.columns([1, 1])

    with col_donut:
        st.markdown(
            """
            <div class="content-card">
                <div class="card-header-row">
                    <div class="card-title">Test Results Overview</div>
                    <div style="font-size:0.8rem; color:#64748b;">Distribution</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        donut_fig = create_results_donut_chart(passed=181, failed=50, pending=6)
        st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_trend:
        st.markdown(
            """
            <div class="content-card">
                <div class="card-header-row">
                    <div class="card-title">Execution Trend</div>
                    <div style="font-size:0.8rem; color:#64748b;">Last 7 days</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        trend_fig = create_execution_trend_chart()
        st.plotly_chart(trend_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Bottom Row (Suites Overview & Recent Activity)
    col_suites, col_activity = st.columns([1.6, 1.0])

    with col_suites:
        sample_suites = [
            {"suite_name": "Checkout Completion Flow", "scenarios": 3, "cases": 26, "status": "Active"},
            {"suite_name": "Lead Management Flow", "scenarios": 2, "cases": 20, "status": "Inactive"},
            {"suite_name": "API Integration Suite", "scenarios": 5, "cases": 14, "status": "Active"},
        ]
        render_suites_table(sample_suites)

    with col_activity:
        sample_activities = [
            {"type": "success", "title": "Checkout test updated", "description": "Status updated to success", "timestamp": "2m ago"},
            {"type": "error", "title": "API Payload Mapping failed", "description": "3 cases returned errors", "timestamp": "14m ago"},
            {"type": "info", "title": "70 AI test cases generated", "description": "Added to Lead Management", "timestamp": "1h ago"},
            {"type": "schedule", "title": "Schedule triggered", "description": "Shopify — 14 cases queued", "timestamp": "3h ago"},
        ]
        render_activity_feed(sample_activities)


# 2. GUIDED TESTING WIZARD
elif active_view == "Start Testing (Wizard)":
    render_testing_wizard(selected_project=current_project)


# 3. AI MODEL ENGINE (Runtime Model Discovery & Switching)
elif active_view == "AI Model Engine":
    st.subheader("⚙️ Universal Dynamic AI Model Engine")
    st.caption("Dynamically discover models and independently assign Gemini or OpenAI models to each of the 6 testing agents.")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🔄 Refresh Discovered Models"):
            with st.spinner("Connecting to provider APIs..."):
                discovered = model_registry.refresh_models()
                st.success(f"Discovered {len(discovered)} available models.")

    with col_t2:
        if st.button("🔌 Test Provider Connections"):
            status_map = model_registry.test_providers()
            for prov, reachable in status_map.items():
                if reachable:
                    st.success(f"✅ {prov.title()} API: Connected")
                else:
                    st.info(f"ℹ️ {prov.title()} API: Offline / Mock Mode")

    st.divider()

    st.markdown("### Independent Per-Agent Model Assignment")
    configs = agent_model_router.get_all_configurations()

    for agent_id, data in configs.items():
        with st.container():
            col_a, col_b, col_c, col_d = st.columns([2.5, 1.2, 2, 1])
            with col_a:
                st.markdown(f"**{data['name']}**")
                st.caption(data["description"])
            with col_b:
                provider_choice = st.selectbox(
                    "Provider",
                    ["gemini", "openai"],
                    index=0 if data["provider"] == "gemini" else 1,
                    key=f"prov_{agent_id}",
                )
            with col_c:
                models_for_prov = (
                    ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
                    if provider_choice == "gemini"
                    else ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"]
                )
                model_idx = models_for_prov.index(data["model_id"]) if data["model_id"] in models_for_prov else 0
                selected_model = st.selectbox("Model", models_for_prov, index=model_idx, key=f"mod_{agent_id}")
            with col_d:
                if st.button("Save", key=f"save_{agent_id}"):
                    agent_model_router.set_agent_model(agent_id, provider_choice, selected_model)
                    st.success("Updated!")
            st.divider()


# 4. INTEGRATIONS (Jira, Git, File Uploads)
elif active_view == "Integrations":
    st.subheader("🔗 Enterprise Integrations")
    tab_jira, tab_git, tab_files = st.tabs(["Jira Integration", "Git Repository", "Document Uploads"])

    with tab_jira:
        st.markdown("#### Jira REST API Connection Wizard")
        j_host = st.text_input("Jira Instance URL", placeholder="https://yourcompany.atlassian.net")
        j_email = st.text_input("Account Email", placeholder="user@company.com")
        j_token = st.text_input("Atlassian API Token", type="password")

        if st.button("Test Jira Connection"):
            jc = JiraClient(host_url=j_host, email=j_email, api_token=j_token)
            res = jc.test_connection()
            if res.get("connected"):
                st.success(f"Connected as {res.get('display_name')}")
            else:
                st.error(f"Connection failed: {res.get('error')}")

    with tab_git:
        st.markdown("#### Git Repository Explorer")
        g_prov = st.selectbox("Provider", ["GitHub", "GitLab", "Bitbucket", "Azure DevOps"])
        g_token = st.text_input("Personal Access Token (PAT)", type="password")
        if st.button("List Repositories"):
            gc = GitClient(provider=g_prov, token=g_token)
            repos = gc.list_repositories()
            st.write(repos)

    with tab_files:
        st.markdown("#### Requirement Document Parser")
        f = st.file_uploader("Upload PDF, Word, Excel, CSV, or Text", type=["pdf", "docx", "xlsx", "csv", "txt", "md"])
        if f:
            txt = DocumentParser.parse_file(f.read(), f.name)
            st.success(f"Extracted {len(txt)} characters")
            st.text_area("Parsed Text", txt[:1000], height=200)


# 5. TEST SUITES & TEST CASES
elif active_view in ["Test Suites", "3. Test Case Design", "Test Plans"]:
    st.subheader("🧪 Test Case & Suite Repository")
    with SessionLocal() as db:
        cases = db.query(TestCase).all()
        if cases:
            for c in cases:
                with st.expander(f"📌 {c.test_case_key}: {c.title} ({c.priority} - {c.test_type})"):
                    st.markdown(f"**Objective**: {c.objective}")
                    st.markdown(f"**Preconditions**: {c.preconditions}")
                    st.markdown(f"**Test Data**: `{c.test_data}`")
                    st.markdown(f"**Expected**: {c.expected_results}")
        else:
            st.info("No test cases generated yet. Run the Guided Testing Wizard to create test cases!")


# 6. REPORTS & EXPORTS
elif active_view in ["Reports", "6. Orchestration & Reporting"]:
    st.subheader("📊 Consolidated Testing & Quality Reports")
    if current_project:
        from src.agents.orchestration_reporting.agent import OrchestrationReportingAgent
        rep_agent = OrchestrationReportingAgent()
        report = rep_agent.generate_consolidated_report(current_project.id)

        c1, c2, c3 = st.columns(3)
        c1.metric("Requirements Coverage", f"{report.requirement_coverage_pct}%")
        c2.metric("Automation Coverage", f"{report.automation_coverage_pct}%")
        c3.metric("Pass Rate", f"{report.test_pass_rate_pct}%")

        st.markdown(report.markdown_report)

        st.divider()
        cd1, cd2 = st.columns(2)
        with cd1:
            st.download_button("📄 Download PDF Report", data=rep_agent.export_pdf(report), file_name=f"{current_project.name}_report.pdf", mime="application/pdf")
        with cd2:
            st.download_button("📊 Download CSV Metrics", data=rep_agent.export_csv(report), file_name=f"{current_project.name}_metrics.csv", mime="text/csv")
    else:
        st.info("Select or create a project to view consolidated reports.")

else:
    st.subheader(f"📌 {active_view}")
    st.info("Module active. Use the sidebar to navigate to Dashboard or Start Testing (Wizard).")
