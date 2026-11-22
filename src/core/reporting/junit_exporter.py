"""
JUnit XML Exporter for Test Executions.
Generates standard JUnit XML (Ant/Jenkins/GitHub Actions compliant) from execution records.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from src.models.entities import TestExecution


def generate_junit_xml(execution: TestExecution) -> str:
    """Generates standard JUnit XML format from a TestExecution entity."""
    total_tests = execution.total_tests or len(execution.results)
    failed_tests = execution.failed_tests or sum(1 for r in execution.results if r.status in ("Failed", "Error"))
    skipped_tests = execution.skipped_tests or sum(1 for r in execution.results if r.status == "Skipped")
    duration = f"{execution.execution_duration_seconds or 0.0:.2f}"
    timestamp = execution.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if execution.created_at else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Root element: <testsuites>
    testsuites = ET.Element(
        "testsuites",
        attrib={
            "id": execution.id,
            "name": f"TestingAgent_{execution.execution_key}",
            "tests": str(total_tests),
            "failures": str(failed_tests),
            "errors": "0",
            "skipped": str(skipped_tests),
            "time": duration,
        },
    )

    # Suite element: <testsuite>
    suite_name = execution.project.name if execution.project else execution.execution_key
    testsuite = ET.SubElement(
        testsuites,
        "testsuite",
        attrib={
            "id": execution.id,
            "name": suite_name,
            "tests": str(total_tests),
            "failures": str(failed_tests),
            "errors": "0",
            "skipped": str(skipped_tests),
            "time": duration,
            "timestamp": timestamp,
            "hostname": "testing-agent-runner",
        },
    )

    # Properties
    properties = ET.SubElement(testsuite, "properties")
    ET.SubElement(properties, "property", attrib={"name": "runner", "value": execution.runner_type or "playwright"})
    ET.SubElement(properties, "property", attrib={"name": "environment", "value": execution.target_environment or "QA"})
    ET.SubElement(properties, "property", attrib={"name": "base_url", "value": execution.base_url or ""})

    # Individual Test Cases: <testcase>
    for result in execution.results:
        tc_elem = ET.SubElement(
            testsuite,
            "testcase",
            attrib={
                "id": result.id,
                "name": result.test_title or "Untitled Test",
                "classname": f"{suite_name}.{result.test_title.replace(' ', '_')}",
                "time": f"{result.execution_duration_seconds or 0.0:.2f}",
            },
        )

        if result.status in ("Failed", "Error"):
            failure_elem = ET.SubElement(
                tc_elem,
                "failure",
                attrib={
                    "message": result.error_message or "Test assertion failed",
                    "type": result.failure_classification or "ApplicationDefect",
                },
            )
            # Content of failure: stack trace or diagnostic details
            body_parts = []
            if result.failing_step:
                body_parts.append(f"Failing Step: {result.failing_step}")
            if result.expected_result:
                body_parts.append(f"Expected: {result.expected_result}")
            if result.actual_result:
                body_parts.append(f"Actual: {result.actual_result}")
            if result.stack_trace:
                body_parts.append(f"Stack Trace:\n{result.stack_trace}")
            elif result.log_output:
                body_parts.append(f"Console Output:\n{result.log_output}")
            failure_elem.text = "\n\n".join(body_parts) if body_parts else (result.error_message or "Assertion failed")

        elif result.status == "Skipped":
            skipped_elem = ET.SubElement(
                tc_elem,
                "skipped",
                attrib={"message": "Test marked as skipped"},
            )
            if result.log_output:
                skipped_elem.text = result.log_output

        # Add system-out if logs exist
        if result.log_output and result.status == "Passed":
            system_out = ET.SubElement(tc_elem, "system-out")
            system_out.text = result.log_output

    # Format into XML string with XML declaration
    xml_str = ET.tostring(testsuites, encoding="utf-8", method="xml")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str.decode("utf-8")}'
