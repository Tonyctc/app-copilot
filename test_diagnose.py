"""
AppCopilot - Diagnostic test to verify page structure
"""
import os
import sys
import time
import subprocess

BASE_URL = "http://localhost:5000"
APP_DIR = "/home/bonfitto/app-copilot"
VENV_PYTHON = os.path.join(APP_DIR, "venv", "bin", "python3")


def start_server():
    proc = subprocess.Popen(
        [VENV_PYTHON, "run.py"],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "FLASK_ENV": "production", "SECRET_KEY": "test-key-123"}
    )
    time.sleep(3)
    return proc


server = start_server()
try:
    import requests

    pages = ["/", "/login", "/register", "/dashboard", "/admin", "/project/new", "/upgrade"]
    
    session = requests.Session()
    
    # First verify pages load
    for path in pages:
        resp = session.get(f"{BASE_URL}{path}")
        status = "✓" if resp.status_code in (200, 302) else "✗"
        print(f"{status} GET {path:25s} -> {resp.status_code}")
    
    # Register a user
    print("\n--- Registering user ---")
    register_url = f"{BASE_URL}/register"
    resp = session.get(register_url)
    print(f"GET /register -> {resp.status_code}")
    
    # Extract CSRF token from the page
    import re
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', resp.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"CSRF Token found: {csrf_token[:20]}...")
    else:
        csrf_token = ""
        print("NO CSRF TOKEN FOUND")
    
    # Also try to find input field names
    input_patterns = re.findall(r'name="([^"]+)"', resp.text)
    print(f"Form fields: {input_patterns}")
    
    class_patterns = re.findall(r'class="([^"]*form-input[^"]*)"', resp.text)
    print(f"Found {len(class_patterns)} form-input elements")
    
    # Check for type="submit"
    submit_count = resp.text.count('type="submit"')
    print(f"Submit buttons: {submit_count}")
    
    # Check for button[type=submit]
    button_submit = resp.text.count('<button')
    print(f"Button tags: {button_submit}")
    
    # Try login page
    print("\n--- Login Page ---")
    resp = session.get(f"{BASE_URL}/login")
    print(f"GET /login -> {resp.status_code}")
    
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', resp.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"CSRF Token: {csrf_token[:20]}...")
    
    input_patterns = re.findall(r'name="([^"]+)"', resp.text)
    print(f"Form fields: {input_patterns}")
    
    # Check for text "Entrar"  
    if "entrar" in resp.text.lower() or "Entrar" in resp.text:
        print("'Entrar' found on login page")
    
    # Now use Playwright for visual verification
    print("\n--- Playwright Page Structure ---")
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Check register page structure
        page = browser.new_page()
        page.goto(f"{BASE_URL}/register")
        html = page.content()
        
        # Find all input elements
        inputs = page.query_selector_all("input, textarea, button")
        for inp in inputs:
            name = inp.get_attribute("name") or ""
            inp_type = inp.get_attribute("type") or ""
            inp_id = inp.get_attribute("id") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            tag = inp.evaluate("el => el.tagName")
            print(f"  <{tag}> name='{name}' type='{inp_type}' id='{inp_id}' placeholder='{placeholder[:30]}'")
        
        # Check button text
        buttons = page.query_selector_all("button[type='submit'], input[type='submit']")
        for btn in buttons:
            text = btn.text_content().strip() or btn.get_attribute("value") or ""
            print(f"  Submit button: '{text[:50]}'")
        
        browser.close()

finally:
    server.terminate()
    server.wait(timeout=5)
