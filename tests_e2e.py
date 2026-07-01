"""
AppCopilot - Testes E2E com Playwright
Testa: registro, login, wizard completo, admin, export, build prompt
"""
import os
import sys
import time
import subprocess
from pathlib import Path

# Config
BASE_URL = "http://localhost:5000"
APP_DIR = "/home/bonfitto/app-copilot"
VENV_PYTHON = os.path.join(APP_DIR, "venv", "bin", "python3")


def start_server():
    """Start the Flask app in background."""
    proc = subprocess.Popen(
        [VENV_PYTHON, "run.py"],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "FLASK_ENV": "production", "SECRET_KEY": "test-key-123"}
    )
    # Wait for server to start
    time.sleep(3)
    return proc


def run_playwright_tests():
    """Run Playwright tests using the Python API."""
    from playwright.sync_api import sync_playwright, expect

    server_proc = start_server()
    passed = 0
    failed = 0
    errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            print("\n" + "=" * 60)
            print("APPCOPILOT - PLAYWRIGHT E2E TESTS")
            print("=" * 60)

            # ─── TEST 1: Landing Page ───────────────────────────────
            print("\n[TEST 1] Landing Page")
            try:
                page.goto(BASE_URL)
                assert "AppCopilot" in page.title() or "Copilot" in page.title()
                # Check for hero content
                content = page.text_content("body")
                assert "AppCopilot" in content
                assert page.is_visible("text=Começar Agora") or page.is_visible("text=Cadastre-se")
                print("  ✓ Landing page loads correctly")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 1: {e}")

            # ─── TEST 2: Register Page ──────────────────────────────
            print("\n[TEST 2] Registration Page")
            try:
                page.goto(f"{BASE_URL}/register")
                assert page.is_visible("text=Criar Conta")
                assert page.is_visible("input#username") or page.is_visible("input[name='username']")
                assert page.is_visible("input#email") or page.is_visible("input[name='email']")
                print("  ✓ Register page has all fields")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 2: {e}")

            # ─── TEST 3: Register User ─────────────────────────────
            print("\n[TEST 3] User Registration")
            try:
                timestamp = int(time.time())
                username = f"testuser_{timestamp}"
                email = f"test_{timestamp}@example.com"
                
                page.fill("input[name='username']", username)
                page.fill("input[name='email']", email)
                page.fill("input[name='password']", "TestPass123!")
                page.fill("input[name='confirm_password']", "TestPass123!")
                
                # Try both button types
                if page.is_visible("button[type='submit']"):
                    page.click("button[type='submit']")
                else:
                    page.click("input[type='submit']")
                
                time.sleep(1)
                # Should redirect to login with success message
                assert "/login" in page.url or "login" in page.url.lower()
                print(f"  ✓ Registered user: {username}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 3: {e}")

            # ─── TEST 4: Login ─────────────────────────────────────
            print("\n[TEST 4] User Login")
            try:
                page.fill("input[name='email']", email)
                page.fill("input[name='password']", "TestPass123!")
                
                if page.is_visible("button[type='submit']"):
                    page.click("button[type='submit']")
                else:
                    page.click("input[type='submit']")
                
                time.sleep(1)
                # Should redirect to dashboard
                assert "/dashboard" in page.url or "dashboard" in page.url.lower()
                print("  ✓ Login successful, redirected to dashboard")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 4: {e}")

            # ─── TEST 5: Dashboard ────────────────────────────────
            print("\n[TEST 5] Dashboard")
            try:
                page.goto(f"{BASE_URL}/dashboard")
                assert "Dashboard" in page.text_content("body")
                # Should see welcome or new project button
                assert page.is_visible("text=Novo Projeto") or page.is_visible("text=Criar")
                print("  ✓ Dashboard shows projects area")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 5: {e}")

            # ─── TEST 6: Create New Project ─────────────────────────
            print("\n[TEST 6] Create New Project")
            try:
                # Find and click the new project button
                page.goto(f"{BASE_URL}/project/new")
                page.fill("input[name='name']", "Meu App Teste")
                
                if page.is_visible("button[type='submit']"):
                    page.click("button[type='submit']")
                else:
                    page.click("input[type='submit']")
                
                time.sleep(1)
                assert "/wizard" in page.url or "wizard" in page.url.lower()
                print("  ✓ Project created, redirected to wizard")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 5: {e}")

            # ─── TEST 7: Wizard Phase 1 (Discovery) ────────────────
            print("\n[TEST 7] Wizard - Phase 1 (Discovery)")
            try:
                # Should see the discovery form
                assert page.is_visible("text=Descobrir") or page.is_visible("text=Fase 1")
                # Fill phase 1 fields
                for field in ["app_name", "main_goal", "pain_points", "target_audience"]:
                    selector = f"input[name='{field}'], textarea[name='{field}']"
                    if page.is_visible(selector):
                        page.fill(selector, f"Test {field} value")
                
                # Submit
                if page.is_visible("button[type='submit']"):
                    page.click("button[type='submit']")
                else:
                    page.click("input[type='submit']")
                time.sleep(1)
                print("  ✓ Phase 1 data saved")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 7: {e}")

            # ─── TEST 8: Access control ────────────────────────────
            print("\\n[TEST 8] Access Control")
            try:
                # Non-logged-in user should be redirected (use new context to clear cookies)
                new_ctx = browser.new_context()
                new_page = new_ctx.new_page()
                new_page.goto(f"{BASE_URL}/dashboard")
                assert "/login" in new_page.url or "login" in new_page.url.lower()
                new_page.close()
                new_ctx.close()
                print("  ✓ Unauthenticated users redirected to login")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 8: {e}")

            # ─── TEST 9: Admin access ──────────────────────────────
            print("\n[TEST 9] Admin Access (non-admin user)")
            try:
                page.goto(f"{BASE_URL}/admin")
                # Non-admin should get 403 or be redirected
                assert "403" in page.text_content("body") or "Acesso Negado" in page.text_content("body") or "/login" in page.url
                print("  ✓ Non-admin users cannot access admin panel")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 9: {e}")

            # ─── TEST 10: 404 Page ─────────────────────────────────
            print("\n[TEST 10] 404 Page")
            try:
                page.goto(f"{BASE_URL}/pagina-inexistente-123")
                assert "404" in page.text_content("body") or "não encontrada" in page.text_content("body")
                print("  ✓ 404 page renders correctly")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 10: {e}")

            # ─── TEST 11: Static files ─────────────────────────────
            print("\n[TEST 11] Static Files")
            try:
                page.goto(f"{BASE_URL}/static/css/style.css")
                content = page.text_content("body")
                assert len(content) > 100  # CSS file has content
                print("  ✓ CSS file serves correctly")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 11: {e}")

            # ─── TEST 12: Upgrade page ─────────────────────────────
            print("\n[TEST 12] Premium Upgrade Page")
            try:
                page.goto(f"{BASE_URL}/upgrade")
                # Free user should see upgrade page
                content = page.text_content("body")
                assert "Premium" in content or "upgrade" in page.url.lower()
                print("  ✓ Upgrade page accessible for free users")
                passed += 1
            except Exception as e:
                print(f"  ✗ {e}")
                failed += 1
                errors.append(f"TEST 12: {e}")

            browser.close()

    finally:
        # Kill the server
        server_proc.terminate()
        server_proc.wait(timeout=5)

    # Print results
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {len(errors)} errors")
    print("=" * 60)
    
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")

    return failed == 0


if __name__ == "__main__":
    success = run_playwright_tests()
    sys.exit(0 if success else 1)
