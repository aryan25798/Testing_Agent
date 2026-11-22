import os
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:4200")
OUTPUT_DIR = Path(__file__).parent / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Required Viewports from Specification
VIEWPORTS = [
    {"name": "large_desktop", "width": 1920, "height": 1080},
    {"name": "desktop_1600", "width": 1600, "height": 900},
    {"name": "standard_desktop", "width": 1440, "height": 900},
    {"name": "laptop", "width": 1366, "height": 768},
    {"name": "small_laptop", "width": 1280, "height": 720},
    {"name": "tablet_landscape", "width": 1024, "height": 768},
    {"name": "tablet_portrait", "width": 768, "height": 1024},
    {"name": "large_mobile", "width": 430, "height": 932},
    {"name": "mobile_414", "width": 414, "height": 896},
    {"name": "mobile_390", "width": 390, "height": 844},
    {"name": "small_mobile_375", "width": 375, "height": 812},
    {"name": "very_small_mobile_360", "width": 360, "height": 800},
    {"name": "min_supported_320", "width": 320, "height": 568},
]

ROUTES = [
    {"path": "/dashboard", "name": "Dashboard"},
    {"path": "/projects", "name": "Projects"},
    {"path": "/agents", "name": "Agents"},
    {"path": "/workflows", "name": "Workflows"},
    {"path": "/test-cases", "name": "Test Cases"},
    {"path": "/automation", "name": "Automation"},
    {"path": "/executions", "name": "Executions"},
    {"path": "/reports", "name": "Reports"},
    {"path": "/models", "name": "Model Settings"},
    {"path": "/integrations", "name": "MCP Integrations"},
    {"path": "/settings", "name": "Settings"},
]

def run_responsive_audit():
    results = []
    print(f"Starting Playwright Responsive Audit against {BASE_URL}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Warm up by navigating to home
        try:
            page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"Initial navigation failed: {e}")

        # 2. Iterate each route and each viewport
        for route in ROUTES:
            url = f"{BASE_URL}{route['path']}"
            print(f"\n--- Auditing Route: {route['name']} ({route['path']}) ---")
            
            for vp in VIEWPORTS:
                page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(300)

                # Check Document Overflow
                overflow_info = page.evaluate("""() => {
                    const docEl = document.documentElement;
                    const body = document.body;
                    const scrollW = Math.max(docEl.scrollWidth, body.scrollWidth);
                    const clientW = Math.max(docEl.clientWidth, body.clientWidth);
                    const hasHorizontalScroll = scrollW > clientW + 2;
                    return {
                        scrollW,
                        clientW,
                        diff: scrollW - clientW,
                        hasHorizontalScroll
                    };
                }""")

                # Check Elements Exceeding Viewport (excluding those inside intentional scroll containers)
                exceeding_elements = page.evaluate("""(vpWidth) => {
                    const elements = Array.from(document.querySelectorAll('header, main, h1, h2, .grid, .flex'));
                    const exceeding = [];
                    for (const el of elements) {
                        let isScrollable = false;
                        let curr = el;
                        while (curr && curr !== document.body) {
                            const style = window.getComputedStyle(curr);
                            if (style.overflowX === 'auto' || style.overflowX === 'scroll') {
                                isScrollable = true;
                                break;
                            }
                            curr = curr.parentElement;
                        }
                        if (isScrollable) continue;

                        const rect = el.getBoundingClientRect();
                        if (rect.width > vpWidth + 5) {
                            exceeding.push({
                                tag: el.tagName,
                                class: (el.className || '').toString().slice(0, 50),
                                width: Math.round(rect.width)
                            });
                            if (exceeding.length >= 3) break;
                        }
                    }
                    return exceeding;
                }""", vp["width"])

                passed = not overflow_info["hasHorizontalScroll"] and len(exceeding_elements) == 0

                # Capture screenshots for key representative breakpoints
                screenshot_path = ""
                if vp["name"] in ["standard_desktop", "tablet_portrait", "mobile_390", "min_supported_320"]:
                    clean_route = route["path"].replace("/", "").replace("-", "_") or "home"
                    filename = f"{clean_route}_{vp['name']}.png"
                    filepath = OUTPUT_DIR / filename
                    page.screenshot(path=str(filepath))
                    screenshot_path = str(filepath)

                status_str = "PASS" if passed else "FAIL"
                print(f"  [{status_str}] {vp['name']} ({vp['width']}x{vp['height']}): diff={overflow_info['diff']}px")

                results.append({
                    "route": route["path"],
                    "routeName": route["name"],
                    "viewport": vp["name"],
                    "width": vp["width"],
                    "height": vp["height"],
                    "passed": passed,
                    "overflowDiff": overflow_info["diff"],
                    "screenshot": screenshot_path,
                    "exceedingElements": exceeding_elements
                })

        # 3. Interactive Tests on MCP Integrations Page
        print("\n--- Running Interactive Tests: MCP Integrations ---")
        page.goto(f"{BASE_URL}/integrations", wait_until="networkidle", timeout=15000)
        
        # Test Tab Switching at 1280x720, 768x1024, and 375x812
        for vp in [
            {"name": "desktop_1280", "width": 1280, "height": 720},
            {"name": "tablet_768", "width": 768, "height": 1024},
            {"name": "mobile_375", "width": 375, "height": 812}
        ]:
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            page.wait_for_timeout(200)

            # Click Discovered Tools
            page.locator("button").filter(has_text="Discovered Tools").first.click()
            page.wait_for_timeout(300)
            tools_visible = page.locator("text=Dynamically Discovered MCP Tools").first.is_visible()
            
            # Click Filter Buttons (GitHub, Atlassian, All)
            page.locator("button").filter(has_text="GitHub").first.click()
            page.wait_for_timeout(150)
            page.locator("button").filter(has_text="Atlassian").first.click()
            page.wait_for_timeout(150)
            page.locator("button").filter(has_text="All").first.click()
            page.wait_for_timeout(150)

            # Click Project Resource Mapping
            page.locator("button").filter(has_text="Project Resource Mapping").first.click()
            page.wait_for_timeout(200)
            mapping_visible = page.locator("text=Project-Level Integration Mapping").first.is_visible()

            # Click MCP Server Connections
            page.locator("button").filter(has_text="MCP Server Connections").first.click()
            page.wait_for_timeout(200)
            servers_visible = page.locator("text=Official GitHub MCP Server").first.is_visible()

            # Test GitHub Modal Open & Close
            page.locator("button").filter(has_text="Connect GitHub MCP").first.click()
            page.wait_for_timeout(300)
            modal_visible = page.locator("text=Connect Official GitHub MCP").first.is_visible()
            page.locator("button[aria-label='Close dialog']").click()
            page.wait_for_timeout(200)

            print(f"  Interactive MCP test at {vp['name']} ({vp['width']}x{vp['height']}): "
                  f"tools={tools_visible}, mapping={mapping_visible}, servers={servers_visible}, modal={modal_visible}")

        # 4. Interactive Test: Mobile Sidebar Drawer
        print("\n--- Running Interactive Tests: Mobile Sidebar Drawer ---")
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(300)

        # Open Drawer
        mobile_menu_btn = page.locator("button[aria-label='Open mobile drawer']").first
        if mobile_menu_btn.is_visible():
            mobile_menu_btn.click()
            page.wait_for_timeout(300)
            aside = page.locator("aside")
            drawer_open = aside.is_visible()
            # Close Drawer
            close_btn = page.locator("button[aria-label='Close navigation']").first
            if close_btn.is_visible():
                close_btn.click()
                page.wait_for_timeout(300)
            print(f"  Mobile drawer toggle test: opened={drawer_open}")

        browser.close()

    # Summarize Results
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r["passed"])
    failed_checks = total_checks - passed_checks
    pass_rate = (passed_checks / total_checks) * 100 if total_checks else 0

    print(f"\n==========================================")
    print(f"RESPONSIVE AUDIT COMPLETE")
    print(f"Total Checks: {total_checks} | Passed: {passed_checks} | Failed: {failed_checks}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print(f"==========================================")

    # Save Results JSON
    report_file = OUTPUT_DIR / "responsive_audit_summary.json"
    with open(report_file, "w") as f:
        json.dump({
            "totalChecks": total_checks,
            "passedChecks": passed_checks,
            "failedChecks": failed_checks,
            "passRate": pass_rate,
            "results": results
        }, f, indent=2)
    print(f"Summary saved to: {report_file}")

if __name__ == "__main__":
    run_responsive_audit()
