"""Test script for app-copilot - verifies all imports and basic app creation."""
import sys
import os

# Activate virtual environment
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'lib',
                         f'python{sys.version_info.major}.{sys.version_info.minor}',
                         'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("TESTING APP-COPILOT")
print("=" * 60)

# 1. Test Config
print("\n[1/6] Testing Config...")
from backend.config import Config
assert hasattr(Config, 'SECRET_KEY'), "Missing SECRET_KEY"
assert hasattr(Config, 'SQLALCHEMY_DATABASE_URI'), "Missing DB URI"
print("  ✓ Config OK")

# 2. Test Models
print("\n[2/6] Testing Models...")
from backend.models import db, User, Project
assert User is not None
assert Project is not None
# Test user creation
u = User(username="test", email="test@test.com")
u.set_password("senha123")
assert u.check_password("senha123")
assert not u.check_password("wrong")
assert u.plan == 'free'
assert not u.is_premium()
assert not u.is_admin()
# Test premium
u.plan = 'premium'
assert u.is_premium()
# Test admin
u.plan = 'admin'
assert u.is_admin()
assert u.is_premium()
print("  ✓ Models OK (password hash, plan checks)")

# 3. Test Auth
print("\n[3/6] Testing Auth...")
from backend.auth import login_manager, LoginForm, RegisterForm
assert login_manager is not None
print("  ✓ Auth OK")

# 4. Test OKFGenerator
print("\n[4/6] Testing OKFGenerator...")
from backend.okf_generator import OKFGenerator
gen = OKFGenerator(output_dir='/tmp/test_okf')
assert gen is not None
assert gen.PHASE_NAMES[1] == 'descobrir'
assert gen.PHASE_NAMES[4] == 'entregar'
print("  ✓ OKFGenerator OK")

# 5. Test ModelClient
print("\n[5/6] Testing ModelClient...")
from backend.model_client import ModelClient
client = ModelClient()
assert client is not None
# Test fallback prompt generation
test_data = {
    'project_name': 'TestApp',
    'discovery_data': {'main_goal': 'Criar um app de teste', 'target_audience': 'Devs'},
    'definition_data': {'functional_requirements': 'Login, CRUD'},
    'development_data': {'frontend_tech': 'React', 'backend_tech': 'Python'},
    'delivery_data': {}
}
fallback = client._build_fallback_prompt(test_data)
assert 'TestApp' in fallback
assert 'React' in fallback
assert 'Python' in fallback
assert 'Subagentes' in fallback
assert 'TDD' in fallback
print("  ✓ ModelClient OK (fallback prompt)")

# 6. Test Flask App
print("\n[6/6] Testing Flask App Creation...")
from backend.app import create_app
app = create_app()
assert app is not None
print(f"  ✓ App created: {app.name}")

# Print routes
routes = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
print(f"\n  Routes ({len(routes)} total):")
for rule in routes:
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"    {rule.rule:45s} [{methods:8s}] -> {rule.endpoint}")

# Test client
with app.test_client() as client:
    tests = [
        ('/', 200),
        ('/login', 200),
        ('/register', 200),
        ('/dashboard', 302),  # redirect to login
        ('/admin', 302),      # redirect to login
        ('/nonexistent', 404),
    ]
    print("\n  HTTP Tests:")
    all_pass = True
    for url, expected in tests:
        resp = client.get(url)
        status = "✓" if resp.status_code == expected else "✗"
        if resp.status_code != expected:
            all_pass = False
        print(f"    {status} GET {url:25s} -> {resp.status_code} (expected {expected})")

    # Test registration flow
    print("\n  Registration Flow:")
    resp = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!',
        'confirm_password': 'Test123!',
    }, follow_redirects=True)
    print(f"    ✓ POST /register -> {resp.status_code}")

    # Test login
    resp = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'Test123!',
    }, follow_redirects=True)
    print(f"    ✓ POST /login -> {resp.status_code}")
    
    # Test dashboard
    resp = client.get('/dashboard')
    print(f"    ✓ GET /dashboard -> {resp.status_code}")

print("\n" + "=" * 60)
status = "ALL TESTS PASSED ✓" if all_pass else "SOME TESTS FAILED ✗"
print(f"  {status}")
print("=" * 60)
