# Claude Code Agent Workflow for MockExamify

This document defines the standard operating procedures for Claude Code when working on MockExamify. Follow these workflows to ensure consistency, quality, and reliability across all development sessions.

---

## 🎯 Core Principles

1. **Always use TodoWrite** for complex tasks (3+ steps)
2. **Test before completing** any task
3. **Read context first** before making changes
4. **Follow existing patterns** in the codebase
5. **Document as you go** when adding new features

---

## 📋 Standard Workflows by Task Type

### 1. Bug Fix Workflow

```
✓ STEP 1: Understand the Bug
  - Read user description carefully
  - Locate relevant files using Grep/Glob
  - Read the affected code sections
  - Identify root cause

✓ STEP 2: Create Todo List
  - Break down the fix into steps
  - Mark first task as in_progress

✓ STEP 3: Implement Fix
  - Make minimal changes to fix the issue
  - Follow existing code patterns
  - Add error handling if needed
  - Update each todo as completed

✓ STEP 4: Test the Fix
  - Run: python run_tests.py --suite [component]
  - Run: python run_tests.py --suite critical
  - Fix any test failures

✓ STEP 5: Report Results
  - Summarize what was fixed
  - Include test results
  - Reference files changed with line numbers
```

**Example:**
```markdown
## Bug Fixed: Login authentication timeout

### Changes Made
- Fixed session timeout logic in [auth_utils.py:142](auth_utils.py#L142)
- Updated JWT expiration handling in [config.py:67](config.py#L67)

### Testing Performed
- ✅ Auth tests: 15/15 passed
- ✅ Critical tests: 19/19 passed
- ✅ Manual login test successful

### Files Modified
- [auth_utils.py](auth_utils.py) - Session timeout logic
- [config.py](config.py) - JWT configuration
```

---

### 2. Feature Addition Workflow

```
✓ STEP 1: Plan the Feature
  - Read user requirements
  - Review existing similar features
  - Check database schema if needed
  - Create comprehensive todo list

✓ STEP 2: Design Approach
  - Identify files to modify/create
  - Plan database changes if any
  - Consider security implications
  - Outline testing strategy

✓ STEP 3: Implement Feature
  - Follow existing code patterns
  - Add proper error handling
  - Include input validation
  - Add logging where appropriate
  - Update each todo as completed

✓ STEP 4: Add Tests
  - Write unit tests for new functions
  - Add integration tests if needed
  - Test edge cases

✓ STEP 5: Run Comprehensive Tests
  - Run: python run_tests.py --suite regression
  - Run: python run_tests.py --suite critical
  - Fix any failures

✓ STEP 6: Update Documentation
  - Add docstrings to new functions
  - Update README if user-facing
  - Add comments for complex logic

✓ STEP 7: Report Completion
  - Summarize feature added
  - Include test results
  - Provide usage examples
```

---

### 3. Refactoring Workflow

```
✓ STEP 1: Establish Baseline
  - Run: python run_tests.py --suite all
  - Document current test status
  - Review code to be refactored

✓ STEP 2: Create Todo List
  - Break refactoring into small steps
  - Plan to test after each step

✓ STEP 3: Refactor Incrementally
  - Make small, testable changes
  - Maintain existing behavior
  - Test after each change
  - Run: python run_tests.py --suite critical

✓ STEP 4: Final Validation
  - Run: python run_tests.py --suite all
  - Ensure no regressions
  - Compare with baseline

✓ STEP 5: Report Changes
  - Explain what was refactored and why
  - Show before/after comparisons
  - Include test results
```

---

### 4. Database Changes Workflow

```
✓ STEP 1: Plan Database Changes
  - Review existing schema
  - Design new tables/columns
  - Consider migration strategy
  - Plan rollback if needed

✓ STEP 2: Create Migration
  - Write SQL migration script
  - Save to migrations/ directory
  - Include both up and down migrations

✓ STEP 3: Update Code
  - Modify db.py functions
  - Update models.py if needed
  - Update API endpoints
  - Add database validation

✓ STEP 4: Test Database Changes
  - Run: python run_tests.py --suite database
  - Test manual operations
  - Verify data integrity
  - Run: python run_tests.py --suite critical

✓ STEP 5: Document Changes
  - Update database schema docs
  - Add migration notes
  - Document new fields/tables
```

---

### 5. Security Fix Workflow

```
✓ STEP 1: Assess Security Issue
  - Understand the vulnerability
  - Identify affected components
  - Determine severity level
  - Review security best practices

✓ STEP 2: Create Fix Plan
  - Plan secure implementation
  - Consider edge cases
  - Review auth_utils.py and security_utils.py

✓ STEP 3: Implement Security Fix
  - Apply fix with minimal changes
  - Add input validation
  - Add security logging
  - Follow OWASP guidelines

✓ STEP 4: Security Testing
  - Run: python run_tests.py --suite security
  - Test attack vectors
  - Verify fix effectiveness
  - Run: python run_tests.py --suite critical

✓ STEP 5: Document Security Update
  - Document the vulnerability (privately)
  - Explain the fix
  - Add security notes in code
```

---

## 🧪 Testing Strategy

### Test Suite Selection Guide

| Change Type | Command | When to Use |
|-------------|---------|-------------|
| **Quick validation** | `python run_tests.py --suite quick` | Small changes, syntax fixes |
| **Critical systems** | `python run_tests.py --suite critical` | Core functionality changes |
| **Authentication** | `python run_tests.py --suite auth` | Auth-related changes |
| **Database** | `python run_tests.py --suite database` | Database operations |
| **API endpoints** | `python run_tests.py --suite api` | API changes |
| **Full regression** | `python run_tests.py --suite regression` | New features, major changes |
| **All tests** | `python run_tests.py --suite all` | Before major releases |

### E2E Testing (Playwright)

For frontend testing:
```bash
# Run specific E2E test
npx playwright test -g "test name"

# Run all E2E tests
npm test

# Run with UI mode
npm run test:ui

# Run auto-fix loop
node auto_fix_loop.js
```

### When to Run Tests

1. **Before starting** - Establish baseline
2. **After core file changes** - Immediate validation
3. **After feature completion** - Regression testing
4. **Before completing task** - Final validation
5. **If hook triggers** - When system reminds you

---

## 📁 Key Files Reference

### Core Application Files
- **[streamlit_app.py](streamlit_app.py)** - Main Streamlit application
- **[api.py](api.py)** - FastAPI backend endpoints
- **[db.py](db.py)** - Database operations and queries
- **[models.py](models.py)** - Data models and schemas
- **[config.py](config.py)** - Configuration and environment

### Authentication & Security
- **[auth_utils.py](auth_utils.py)** - Authentication logic, JWT, sessions
- **[security_utils.py](security_utils.py)** - Security utilities, validation

### Integrations
- **[stripe_utils.py](stripe_utils.py)** - Payment processing
- **[openrouter_utils.py](openrouter_utils.py)** - AI explanations
- **[pdf_utils.py](pdf_utils.py)** - PDF report generation

### Testing & Automation
- **[run_tests.py](run_tests.py)** - Test runner with multiple suites
- **[auto_fix_loop.js](auto_fix_loop.js)** - Self-healing E2E tests
- **[playwright.config.ts](playwright.config.ts)** - E2E test configuration
- **[.claude_testing_protocol.md](.claude_testing_protocol.md)** - Testing rules

### Admin Features
- **[app_pages/admin_dashboard.py](app_pages/admin_dashboard.py)** - Admin analytics
- **[app_pages/admin_tickets.py](app_pages/admin_tickets.py)** - Support tickets
- **[admin_utils.py](admin_utils.py)** - Admin operations

---

## 🔍 Code Search Strategies

### Finding Code
```bash
# Search for function definitions
Glob: **/*.py
Grep: "def function_name"

# Search for specific text
Grep: "search term" (pattern)
Options: -i (case insensitive), -n (line numbers)

# Find all files of type
Glob: app_pages/**/*.py
Glob: tests/**/*.ts
```

### Reading Context
Before modifying code:
1. Read the specific file you'll change
2. Search for similar patterns in codebase
3. Check related files (imports, callers)
4. Review recent git history for context

---

## 🎨 Code Style Guidelines

### Python Code Standards
```python
# Good: Clear function with docstring and type hints
def calculate_score(answers: dict, correct_answers: dict) -> float:
    """
    Calculate exam score based on user answers.

    Args:
        answers: User's submitted answers
        correct_answers: Correct answer key

    Returns:
        Score as percentage (0-100)
    """
    # Implementation
    pass

# Good: Error handling
try:
    result = db.get_user(user_id)
    if not result:
        raise ValueError("User not found")
except Exception as e:
    logger.error(f"Failed to get user: {e}")
    return None

# Good: Input validation
if not email or not isinstance(email, str):
    raise ValueError("Invalid email format")
```

### Naming Conventions
- **Functions**: `snake_case` - `get_user_by_id()`
- **Classes**: `PascalCase` - `UserManager`
- **Constants**: `UPPER_SNAKE_CASE` - `MAX_ATTEMPTS`
- **Private**: `_leading_underscore` - `_internal_helper()`

---

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Do This
```python
# Don't skip error handling
def get_user(user_id):
    return db.execute(f"SELECT * FROM users WHERE id = {user_id}")  # SQL injection!

# Don't modify without testing
# Made a change? Run tests!

# Don't ignore existing patterns
# If the codebase uses async, follow that pattern
```

### ✅ Do This Instead
```python
# Do add error handling
def get_user(user_id: int) -> dict:
    try:
        result = db.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

# Do test after changes
# Run: python run_tests.py --suite critical

# Do follow existing patterns
# Check similar functions first
```

---

## 💡 Best Practices

### 1. Always Use TodoWrite for Complex Tasks
```python
# Create comprehensive task list
todos = [
    {"content": "Analyze current implementation", "status": "in_progress"},
    {"content": "Design solution", "status": "pending"},
    {"content": "Implement changes", "status": "pending"},
    {"content": "Write tests", "status": "pending"},
    {"content": "Run test suite", "status": "pending"},
    {"content": "Update documentation", "status": "pending"},
]
```

### 2. Progressive Testing
- Test early, test often
- Don't wait until the end
- Fix failures immediately
- Never complete with failing tests

### 3. Clear Communication
- Reference files with line numbers
- Show before/after for changes
- Include test results
- Explain reasoning for decisions

### 4. Security First
- Validate all inputs
- Use parameterized queries
- Check authentication
- Log security events
- Follow principle of least privilege

### 5. Performance Awareness
- Use database indexes
- Cache when appropriate
- Avoid N+1 queries
- Profile before optimizing

---

## 🔄 Git Workflow

### Before Starting Work
```bash
# Check current status
git status

# Check recent commits
git log --oneline -5

# Pull latest changes
git pull origin main
```

### After Completing Work
```bash
# Stage relevant files
git add <files>

# Commit with descriptive message
git commit -m "feat: Add feature description

- Detailed change 1
- Detailed change 2
- Test results: All passed

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin <branch>
```

---

## 📊 Reporting Checklist

When completing any task, include:

✅ **Summary** - What was done
✅ **Files Changed** - With line number references
✅ **Test Results** - Which suites passed
✅ **Usage Examples** - If new feature
✅ **Next Steps** - If applicable
✅ **Breaking Changes** - If any

---

## 🎯 Quick Reference

### Most Common Commands
```bash
# Testing
python run_tests.py --suite critical
python run_tests.py --suite regression
node auto_fix_loop.js

# Development
streamlit run streamlit_app.py --server.port 8501
uvicorn api:app --reload --port 8000

# Database
python -c "from db import db; print(db.health_check())"

# Git
git status
git log --oneline -5
```

### Emergency Procedures

**Tests Failing?**
1. Read error messages carefully
2. Check recent changes
3. Run specific test suite
4. Fix issues one at a time
5. Re-run tests until passing

**Database Issues?**
1. Check connection in .env
2. Verify Supabase status
3. Test with health check
4. Check RLS policies

**API Not Responding?**
1. Check if server is running
2. Verify environment variables
3. Check logs for errors
4. Test with curl/httpie

---

## 📝 Documentation Standards

### Function Documentation
```python
def process_exam_submission(user_id: int, exam_id: int, answers: dict) -> dict:
    """
    Process a user's exam submission and calculate results.

    This function validates answers, calculates the score, saves the attempt
    to the database, and generates a PDF report.

    Args:
        user_id: The ID of the user submitting the exam
        exam_id: The ID of the exam being submitted
        answers: Dictionary mapping question IDs to selected answers

    Returns:
        dict: Contains 'score', 'passed', 'report_url', and 'attempt_id'

    Raises:
        ValueError: If exam or user not found
        DatabaseError: If database operation fails

    Example:
        >>> result = process_exam_submission(123, 456, {'q1': 'A', 'q2': 'C'})
        >>> print(result['score'])
        85.5
    """
    pass
```

---

## 🎓 Learning Resources

### Understanding the Codebase
1. Start with [README.md](README.md) - Project overview
2. Read [.claude_testing_protocol.md](.claude_testing_protocol.md) - Testing rules
3. Review [streamlit_app.py](streamlit_app.py) - Main application flow
4. Study [db.py](db.py) - Database patterns
5. Check [api.py](api.py) - API endpoints

### Common Tasks
- **Add new exam page**: See `app_pages/` for examples
- **Add API endpoint**: Follow patterns in `api.py`
- **Database query**: Use functions in `db.py`
- **Add admin feature**: Check `admin_utils.py`

---

## ✅ Success Checklist

Before marking any task as complete:

- [ ] All requested changes implemented
- [ ] Code follows existing patterns
- [ ] Error handling added
- [ ] Input validation included
- [ ] Appropriate tests run and passed
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced
- [ ] Performance considered
- [ ] Git commit made (if applicable)
- [ ] User notified with clear summary

---

**Remember**: Quality over speed. A well-tested, documented change is worth more than a quick fix that breaks later.

**Golden Rule**: If you touched the code, run the tests. If tests fail, fix them. Never complete a task with failing tests.

---

*This workflow ensures consistency, reliability, and maintainability across all development sessions.*
