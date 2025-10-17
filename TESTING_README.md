# MockExamify Testing Guide

## Overview
This document explains the comprehensive testing setup for MockExamify, including how to run tests, what tests cover, and how to maintain test quality.

## Quick Start

### Run All Critical Tests
```bash
python run_tests.py --suite critical
```

### Run Tests Before Committing
```bash
python run_tests.py --suite pre-commit
```

### Validate App Works
```bash
python run_tests.py --suite validate
```

## Test Suites

### 1. Critical Tests (`--suite critical`)
These are the **must-pass** tests that verify core functionality:
- Admin login works
- User login works
- Password validation works
- Email validation works
- Admin has 0 credits
- Session management works
- Security measures are in place

**When to run:** Before every commit, after any bug fix, before deployment

### 2. Regression Tests (`--suite regression`)
Tests that ensure previously working features don't break:
- Authentication flows
- Admin role detection
- Database operations
- Navigation structure
- Security checks
- Data integrity

**When to run:** After adding new features, before major releases

### 3. Quick Tests (`--suite quick`)
Fast-running unit tests for immediate feedback:
- Validation functions
- Basic database operations
- Configuration checks

**When to run:** During development, frequently

### 4. Authentication Tests (`--suite auth`)
Comprehensive auth testing:
- Login/logout flows
- Password hashing
- Email validation
- Session management
- Admin detection

### 5. Database Tests (`--suite database`)
Database operations:
- User CRUD operations
- Mock exam management
- Attempt tracking
- Credit management

### 6. All Tests (`--suite all`)
Runs the entire test suite

## Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.critical` - Must pass for app to work
- `@pytest.mark.regression` - Prevents breaking existing features
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.db` - Database tests
- `@pytest.mark.ui` - UI tests
- `@pytest.mark.admin` - Admin functionality tests
- `@pytest.mark.slow` - Tests that take longer to run

### Run Specific Markers
```bash
# Run only critical tests
pytest -m critical

# Run auth and db tests
pytest -m "auth or db"

# Run everything except slow tests
pytest -m "not slow"
```

## Pre-commit Hooks

### Setup
```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install
```

### What Happens on Commit
1. Code formatting (black)
2. Import sorting (isort)
3. Linting (flake8)
4. Security checks (bandit)
5. **Critical tests run**
6. **Regression tests run**

If any step fails, the commit is blocked until fixed.

### Skip Hooks (Emergency Only)
```bash
git commit --no-verify -m "Emergency fix"
```

## Test File Structure

```
test_critical_regression.py - Critical tests that must always pass
test_regression.py         - Regression tests for all features
test_auth.py              - Authentication tests
test_database.py          - Database operation tests
test_ui.py                - User interface tests
test_integration.py       - Integration tests
conftest.py               - Test fixtures and configuration
pytest.ini                - Pytest configuration
```

## Writing New Tests

### Critical Test Template
```python
@pytest.mark.regression
@pytest.mark.critical
class TestNewFeatureRegression:
    """Critical tests for new feature"""

    def test_feature_works(self):
        """REGRESSION: New feature must work"""
        # Test code here
        assert feature_works == True
```

### Best Practices
1. **Always mark critical tests** with `@pytest.mark.critical`
2. **Use descriptive names** like `test_admin_login_works`
3. **Add regression tests** for every bug fix
4. **Include docstrings** explaining what the test validates
5. **Keep tests independent** - don't rely on test execution order

## Continuous Integration

### Before Each Commit
```bash
python run_tests.py --suite pre-commit
```

### Before Pushing
```bash
python run_tests.py --suite all
```

### Before Deployment
```bash
# Validate app works
python run_tests.py --suite validate

# Run full test suite
python run_tests.py --suite all
```

## Troubleshooting

### Tests Failing After Changes
1. Run critical tests first: `python run_tests.py --suite critical`
2. Identify which test failed
3. Fix the code or update the test (if requirements changed)
4. Re-run to verify fix

### Pre-commit Hook Fails
1. Read the error message
2. Run the specific test: `pytest test_file.py::test_name -v`
3. Fix the issue
4. Try committing again

### Install Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-mock
```

## Test Coverage

### View Test Coverage
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Coverage Goals
- **Critical paths:** 100% coverage
- **Authentication:** 100% coverage
- **Database operations:** 90%+ coverage
- **UI components:** 70%+ coverage
- **Overall:** 80%+ coverage

## Common Test Scenarios

### Test Admin Cannot Purchase Credits
```python
def test_admin_no_purchase_credits(mock_admin_auth):
    """Admin navigation should not show purchase credits"""
    # Verify admin is detected
    assert mock_admin_auth.is_admin() == True

    # Verify admin has 0 credits
    user = mock_admin_auth.get_current_user()
    assert user["credits_balance"] == 0
```

### Test User Authentication
```python
@pytest.mark.asyncio
async def test_user_can_login():
    """User with correct credentials can login"""
    db = DatabaseManager()
    user = await db.authenticate_user("user@demo.com", "user123")

    assert user is not None
    assert user.role == "user"
```

## Automated Testing Workflow

```
Developer writes code
    ↓
Runs quick tests (fast feedback)
    ↓
Runs critical tests (verify core works)
    ↓
Commits code
    ↓
Pre-commit hooks run automatically
    ↓
If tests pass: Commit succeeds
If tests fail: Commit blocked, fix issues
    ↓
Push to repository
    ↓
CI/CD runs full test suite
```

## Questions?

If you encounter issues with tests:
1. Check this README
2. Look at existing tests for examples
3. Run with verbose output: `pytest -vv`
4. Check test logs in the output

## Maintenance

### Add New Critical Test
1. Add test to `test_critical_regression.py`
2. Mark with `@pytest.mark.critical`
3. Run to verify: `pytest -m critical`
4. Commit and push

### Update Test Fixtures
Edit `conftest.py` to add new fixtures or modify existing ones.

### Modify Test Configuration
Edit `pytest.ini` to change test discovery, markers, or behavior.

---

**Remember:** Tests are your safety net. If a test fails, it's protecting you from deploying broken code!
