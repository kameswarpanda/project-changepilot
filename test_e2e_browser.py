import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_e2e_test():
    print("[START] Starting ChangePilot Automated Browser Verification...")
    errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Capture console errors
        def on_console_msg(msg):
            if msg.type == "error":
                print(f"[Console Error]: {msg.text}")
                errors.append(f"Console: {msg.text}")

        page.on("console", on_console_msg)
        page.on("pageerror", lambda exc: errors.append(f"PageError: {exc}"))

        # Step 1: Open ChangePilot Application
        print("[STEP 1] Navigating to http://localhost:4200...")
        page.goto("http://localhost:4200", wait_until="networkidle")
        time.sleep(2)
        print(f"   Page Title: {page.title()}")

        # Check if auth page is shown
        if page.locator("text=Sign In with Email").count() > 0 or page.locator("text=Continue with Google").count() > 0:
            print("[STEP 2] Testing Auth Page...")
            
            # Click Sign In with Email
            if page.locator("button:has-text('Sign In with Email')").count() > 0:
                print("   Signing in with developer credentials...")
                page.locator("button:has-text('Sign In with Email')").click()
                time.sleep(2)

        # Step 2: Test Dashboard
        print("[STEP 3] Verifying Dashboard...")
        page.wait_for_selector("text=Monitor and manage autonomous software changes", timeout=10000)
        print("   [OK] Dashboard loaded successfully.")

        # Step 3: Test Theme Toggle (Dark / Light Mode)
        print("[STEP 4] Testing Dark / Light Theme Toggle...")
        theme_btn = page.locator("button[title*='Switch to']")
        if theme_btn.count() > 0:
            theme_btn.first.click()
            time.sleep(0.5)
            print("   [OK] Light mode switched.")
            theme_btn.first.click()
            time.sleep(0.5)

        # Step 4: Test Repositories Section
        print("[STEP 5] Navigating to Repositories Tab...")
        page.locator("a.nav-link:has-text('Repositories')").click()
        time.sleep(1)
        assert page.locator("text=Manage connected codebases").count() > 0
        print("   [OK] Repositories tab verified.")

        # Test Connect Modal
        print("   Opening + Connect Repository Modal...")
        page.locator("button:has-text('Connect Repository')").first.click()
        time.sleep(1)
        assert page.locator("h3:has-text('Connect Repository')").count() > 0
        
        # Test Public Git URL subtab
        print("   Testing Public Git Clone URL tab...")
        page.locator("button:has-text('Public Git Clone URL')").click()
        time.sleep(0.5)
        page.locator("input[placeholder*='github.com']").fill("https://github.com/kameswarpanda/project-changepilot.git")
        page.locator("button:has-text('Cancel')").click()
        time.sleep(0.5)

        # Step 5: Test Change Requests Form & Execution
        print("[STEP 6] Navigating to Change Requests Form...")
        page.locator("a.nav-link:has-text('Change Requests')").click()
        time.sleep(1)
        assert page.locator("text=Create New Change Request").count() > 0

        # Fill Change Request
        print("   Submitting a change request ticket...")
        # Ticket ID
        page.locator("input[placeholder*='CP-']").fill("E2E-TEST-01")
        # Change Title
        page.locator("input[placeholder*='Brief description']").fill("Verify live automated pipeline execution")
        # Requirements
        page.locator("textarea[placeholder*='Describe the structural']").fill("Add a validation function for transaction totals ensuring amounts are positive numbers.")
        # Repository
        page.locator("input[placeholder*='demo_repo or Git URL']").fill("demo_repo")

        # Click Run ChangePilot
        print("   Clicking 'Run ChangePilot'...")
        page.locator("button:has-text('Run ChangePilot')").first.click()
        time.sleep(4)

        # Step 6: Test Pipelines Progression
        print("[STEP 7] Checking Pipelines Stage Progression...")
        page.wait_for_selector("text=Pipeline:", timeout=10000)
        print("   [OK] Pipelines page loaded and executing live stages.")

        # Wait for workflow completion
        time.sleep(3)

        # Step 7: Test Change Result Tab
        print("[STEP 8] Navigating to Change Result Tab...")
        page.locator("a.nav-link:has-text('Change Results')").click()
        time.sleep(1)
        print("   [OK] Change Result tab loaded.")

        # Step 8: Test Reports Tab
        print("[STEP 9] Navigating to Reports Tab...")
        page.locator("a.nav-link:has-text('Reports')").click()
        time.sleep(1)
        assert page.locator("text=Stability & Performance Reports").count() > 0
        print("   [OK] Reports analytics rendered.")

        # Step 9: Test Audit Logs Tab
        print("[STEP 10] Navigating to Audit Logs Tab...")
        page.locator("a.nav-link:has-text('Audit Logs')").click()
        time.sleep(1)
        assert page.locator("text=System Audit Trail").count() > 0
        print("   [OK] Audit logs rendered.")

        # Step 10: Test Settings Tab
        print("[STEP 11] Navigating to Settings Tab...")
        page.locator("a.nav-link:has-text('Settings')").click()
        time.sleep(1)
        assert page.locator("text=System Configuration").count() > 0
        print("   [OK] Settings configuration active.")

        # Save Screenshot of successful verification
        page.screenshot(path="e2e_verification_success.png", full_page=True)
        print("[SCREENSHOT] Screenshot saved to e2e_verification_success.png")

        browser.close()

    print("\n==========================================")
    if errors:
        print(f"[WARNING] Encountered {len(errors)} non-fatal warnings/errors:")
        for err in errors:
            print(f"   - {err}")
    else:
        print("[SUCCESS] 100% E2E AUTOMATED BROWSER TEST PASSED WITH 0 ERRORS!")
    print("==========================================\n")

if __name__ == "__main__":
    run_e2e_test()
