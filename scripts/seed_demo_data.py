"""
Script to seed rich real database records for E-Commerce Checkout Suite.
"""

from datetime import datetime, timedelta
from src.database.session import SessionLocal, init_db
from src.models.entities import (
    Project,
    Requirement,
    TestScenario,
    TestCase,
    AutomationScript,
    TestExecution,
    TestExecutionResult,
)


def seed():
    init_db()
    with SessionLocal() as db:
        # Check if project already exists
        existing = db.query(Project).filter(Project.name == "E-Commerce Checkout Suite").first()
        if existing:
            demo_proj = existing
        else:
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

        # Ensure requirement
        r1 = db.query(Requirement).filter(Requirement.project_id == demo_proj.id).first()
        if not r1:
            r1 = Requirement(
                project_id=demo_proj.id,
                requirement_key="REQ-101",
                source_type="jira",
                title="Credit Card Payment Processing",
                description="Customer can complete checkout with Visa, MasterCard, or Amex with 3DS verification.",
                business_objective="Frictionless checkout experience with PCI-DSS compliance.",
                functional_requirements=["16-digit card validation", "CVV verification", "3D Secure auth"],
                acceptance_criteria=["Immediate payment receipt", "Auto-clear shopping cart"],
                is_approved=True,
            )
            db.add(r1)
            db.commit()
            db.refresh(r1)

        # Scenarios
        s1 = db.query(TestScenario).filter(TestScenario.project_id == demo_proj.id, TestScenario.scenario_key == "SCEN-001").first()
        if not s1:
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
                is_approved=False,
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
            db.refresh(s1)
            db.refresh(s2)
            db.refresh(s3)
        else:
            s2 = db.query(TestScenario).filter(TestScenario.project_id == demo_proj.id, TestScenario.scenario_key == "SCEN-002").first()
            s3 = db.query(TestScenario).filter(TestScenario.project_id == demo_proj.id, TestScenario.scenario_key == "SCEN-003").first()

        # Seed Test Cases if empty
        if db.query(TestCase).filter(TestCase.project_id == demo_proj.id).count() == 0:
            for i in range(1, 27):
                tc = TestCase(
                    project_id=demo_proj.id,
                    scenario_id=s1.id,
                    requirement_id=r1.id,
                    test_case_key=f"TC-1{i:02d}",
                    title=f"Checkout Step {i}: Validate Payment Field {i}",
                    objective=f"Ensure checkout card validation step {i} conforms to card specifications.",
                    test_type="Functional" if i % 2 == 0 else "Positive",
                    priority="High" if i < 10 else "Medium",
                    test_data={"card_type": "Visa" if i % 2 == 0 else "Mastercard", "amount": 99.0 + i},
                    execution_steps=[{"step_number": 1, "action": f"Enter card field {i}", "expected": "Input accepted"}],
                    expected_results="Checkout flow completes successfully.",
                    status="Approved",
                    is_approved=True,
                )
                db.add(tc)

            for i in range(1, 21):
                tc = TestCase(
                    project_id=demo_proj.id,
                    scenario_id=s2.id,
                    requirement_id=r1.id,
                    test_case_key=f"TC-2{i:02d}",
                    title=f"Lead Recovery Step {i}: Cart Abandonment Capture",
                    objective="Ensure incomplete checkouts trigger email recovery reminders.",
                    test_type="Functional",
                    priority="Medium",
                    test_data={"cart_id": f"CART-{1000+i}"},
                    execution_steps=[{"step_number": 1, "action": "Leave cart idle", "expected": "Lead registered in DB"}],
                    expected_results="Lead generated in CRM without data loss.",
                    status="Draft",
                    is_approved=False,
                )
                db.add(tc)

            for i in range(1, 15):
                tc = TestCase(
                    project_id=demo_proj.id,
                    scenario_id=s3.id,
                    requirement_id=r1.id,
                    test_case_key=f"TC-3{i:02d}",
                    title=f"API Integration Webhook {i}",
                    objective="Verify payment gateway webhook latency and signature check.",
                    test_type="API",
                    priority="High" if i < 5 else "Medium",
                    test_data={"webhook_id": f"WH-{i:03d}"},
                    execution_steps=[{"step_number": 1, "action": "Send webhook POST", "expected": "HTTP 200 returned"}],
                    expected_results="Webhook payload processed successfully.",
                    status="Approved",
                    is_approved=True,
                )
                db.add(tc)
            db.commit()

        # Seed Execution Runs if empty
        if db.query(TestExecution).filter(TestExecution.project_id == demo_proj.id).count() == 0:
            trend_history = [
                (datetime.now() - timedelta(days=6), "RUN-241", 28, 21, 7, 0),
                (datetime.now() - timedelta(days=5), "RUN-242", 35, 27, 8, 0),
                (datetime.now() - timedelta(days=4), "RUN-243", 42, 34, 8, 0),
                (datetime.now() - timedelta(days=3), "RUN-244", 30, 24, 6, 0),
                (datetime.now() - timedelta(days=2), "RUN-245", 48, 41, 7, 0),
                (datetime.now() - timedelta(days=1), "RUN-246", 22, 17, 5, 0),
                (datetime.now(), "RUN-247", 42, 17, 9, 16),
            ]
            for run_date, run_key, total, passed, failed, skipped in trend_history:
                e_record = TestExecution(
                    project_id=demo_proj.id,
                    execution_key=run_key,
                    runner_type="playwright",
                    total_tests=total,
                    passed_tests=passed,
                    failed_tests=failed,
                    skipped_tests=skipped,
                    execution_duration_seconds=38.5,
                    status="Completed" if failed == 0 else "Failed",
                    created_at=run_date,
                )
                db.add(e_record)
            db.commit()

        print(f"Seeding completed for: {demo_proj.name} ({demo_proj.id})")


if __name__ == "__main__":
    seed()
