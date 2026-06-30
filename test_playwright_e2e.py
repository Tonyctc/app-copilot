"""
AppCopilot - Playwright E2E Test Suite
Run: source venv/bin/activate && python3 test_playwright_e2e.py
"""
import os
import sys
import time
import subprocess
import re

APP_DIR = "/home/bonfitto/app-copilot"
PYTHON = os.path.join(APP_DIR, "venv", "bin", "python3")
BASE_URL = "http://localhost:5001"


def main():
    # Start server on port 5001
    proc = subprocess.Popen(
        [PYTHON, "-c", """
import sys
sys.path.insert(0, '.')
from backend.app import create_app
app = create_app()
app.run(host='0.0.0.0', port=5001, debug=False)
"""],
        cwd=APP_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "FLASK_ENV": "development", "SECRET_KEY": "test-secret-e2e"}
    )
    time.sleep(5)

    from playwright.sync_api import sync_playwright

    passed = 0
    total = 10

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            page = ctx.new_page()
            ts = int(time.time())

            # 1. Landing page
            page.goto(BASE_URL, wait_until="networkidle")
            title = page.title()
            print(f"[1/{total}] Title: '{title}'")
            assert "Copilot" in title or "App" in title, f"Bad title: {title}"
            print(f"[1/{total}] Landing page: ✓")
            passed += 1

            # 2. Register
            page.goto(f"{BASE_URL}/register")
            page.wait_for_load_state("networkidle")
            page.fill("#username", f"user_{ts}")
            page.fill("#email", f"user_{ts}@test.com")
            page.fill("#password", "Pass1234!")
            page.fill("#confirm_password", "Pass1234!")
            page.click("button[type='submit']")
            page.wait_for_timeout(1500)
            assert "login" in page.url, f"Register redirect fail: {page.url}"
            print(f"[2/{total}] Register: ✓")
            passed += 1

            # 3. Login
            page.goto(f"{BASE_URL}/login")
            page.wait_for_load_state("networkidle")
            page.fill("#email", f"user_{ts}@test.com")
            page.fill("#password", "Pass1234!")
            page.click("button[type='submit']")
            page.wait_for_timeout(1500)
            assert "dashboard" in page.url, f"Login redirect fail: {page.url}"
            print(f"[3/{total}] Login: ✓")
            passed += 1

            # 4. Dashboard
            page.goto(f"{BASE_URL}/dashboard")
            page.wait_for_load_state("networkidle")
            body = page.text_content("body")
            assert "Novo Projeto" in body or "Dashboard" in body
            print(f"[4/{total}] Dashboard: ✓")
            passed += 1

            # 5. Create project
            page.goto(f"{BASE_URL}/project/new")
            page.wait_for_load_state("networkidle")
            page.fill("#projectName", "Meu App E2E")
            page.click("button[type='submit']")
            page.wait_for_timeout(1500)
            assert "wizard" in page.url, f"Create project fail: {page.url}"
            print(f"[5/{total}] Create project: ✓")
            passed += 1

            # 6. Wizard Phase 1 (Discovery)
            page.wait_for_load_state("networkidle")
            body = page.text_content("body")
            assert "Descobrir" in body or "Fase 1" in body
            print(f"[6/{total}] Wizard phase 1 visible: ✓")
            passed += 1

            # 7. Upgrade page
            page.goto(f"{BASE_URL}/upgrade")
            page.wait_for_load_state("networkidle")
            body = page.text_content("body")
            assert "Premium" in body or "Upgrade" in body
            print(f"[7/{total}] Upgrade page: ✓")
            passed += 1

            # 8. Admin access denied
            page.goto(f"{BASE_URL}/admin")
            page.wait_for_load_state("networkidle")
            body = page.text_content("body")
            assert "403" in body or "Acesso Negado" in body or "não autorizado" in body.lower()
            print(f"[8/{total}] Admin access block: ✓")
            passed += 1

            # 9. Unauthenticated access (new context = no cookies)
            new_ctx = browser.new_context()
            new_page = new_ctx.new_page()
            new_page.goto(f"{BASE_URL}/dashboard")
            assert "login" in new_page.url, f"Auth check fail: {new_page.url}"
            new_ctx.close()
            print(f"[9/{total}] Auth redirect: ✓")
            passed += 1

            # 10. 404 page
            page.goto(f"{BASE_URL}/nonexistent-page-12345")
            body = page.text_content("body")
            assert "404" in body or "não encontrada" in body
            print(f"[10/{total}] 404 page: ✓")
            passed += 1

            ctx.close()
            browser.close()

    finally:
        proc.terminate()
        proc.wait(timeout=5)

    print(f"\n{'='*50}")
    print(f"RESULTS: {passed}/{total} passed")
    print(f"{'='*50}")
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
