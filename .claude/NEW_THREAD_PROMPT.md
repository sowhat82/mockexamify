# New Thread Handoff Prompt for MockExamify

**READ THIS FILE FIRST when starting work on MockExamify in a new thread.**

---

## 🎯 Project: MockExamify

A full-stack Python application for selling and hosting interactive mock exams.

**Tech Stack**: Streamlit (frontend), FastAPI (backend), Supabase (database), Stripe (payments), OpenRouter (AI)

---

## 🚨 CRITICAL: Mandatory Protocols

### 1. Testing Protocol (NON-NEGOTIABLE)

**Read the complete protocol**: [.claude_testing_protocol.md](../.claude_testing_protocol.md)

**Key Rules:**
- ✅ ALWAYS run tests after any code changes
- ✅ NEVER complete a task with failing tests
- ✅ Run appropriate test suite for the change type

**Test Commands:**
```bash
# After modifying core files (streamlit_app.py, auth_utils.py, db.py, models.py, config.py)
python run_tests.py --suite critical

# After adding new features
python run_tests.py --suite regression

# For specific components
python run_tests.py --suite auth        # Authentication changes
python run_tests.py --suite database    # Database changes
python run_tests.py --suite api         # API endpoint changes

# Before completing ANY task
python run_tests.py --suite critical
```

**Golden Rule**: If you touched the code, run the tests. If tests fail, fix them. Never complete with failing tests.

---

### 2. Development Workflow (MANDATORY)

**Read the complete workflow guide**: [CLAUDE_WORKFLOW.md](../CLAUDE_WORKFLOW.md)

**Standard Workflows:**
- **Bug Fix**: Understand → Plan (TodoWrite) → Fix → Test → Report
- **Feature Addition**: Plan → Design → Implement → Test → Document → Report
- **Refactoring**: Baseline tests → Incremental changes → Test continuously → Final validation
- **Security Fix**: Assess → Fix → Security tests → Document
- **Database Changes**: Plan → Create migration → Update code → Test → Document

**Key Principles:**
1. Use TodoWrite for complex tasks (3+ steps)
2. Test incrementally, not just at the end
3. Follow existing code patterns
4. Add proper error handling and validation
5. Reference files with line numbers in reports

---

### 3. Project Context (REQUIRED READING)

**Read the complete context**: [.claude/context_prompt.md](context_prompt.md)

**Quick Overview:**
- **Main files**: streamlit_app.py, api.py, db.py, auth_utils.py, config.py
- **Admin features**: app_pages/admin_dashboard.py, admin_utils.py
- **Testing**: run_tests.py, auto_fix_loop.js, playwright.config.ts
- **Database**: Supabase with RLS policies (use `admin_client` for admin operations)

---

## 📁 Essential Files to Know

### Core Application
- **[streamlit_app.py](../streamlit_app.py)** - Main Streamlit UI, page routing, session management
- **[api.py](../api.py)** - FastAPI REST endpoints
- **[db.py](../db.py)** - Database operations (has both `db` and `admin_client`)
- **[auth_utils.py](../auth_utils.py)** - Authentication, JWT, sessions
- **[config.py](../config.py)** - Configuration, environment variables

### Integrations
- **[stripe_utils.py](../stripe_utils.py)** - Payment processing
- **[openrouter_utils.py](../openrouter_utils.py)** - AI explanations
- **[pdf_utils.py](../pdf_utils.py)** - Report generation

### Testing
- **[run_tests.py](../run_tests.py)** - Python test runner
- **[auto_fix_loop.js](../auto_fix_loop.js)** - Self-healing E2E tests
- **[playwright.config.ts](../playwright.config.ts)** - E2E configuration
- **[tests/e2e/](../tests/e2e/)** - Playwright test files

### Documentation
- **[README.md](../README.md)** - Project overview, setup
- **[.claude_testing_protocol.md](../.claude_testing_protocol.md)** - Testing rules
- **[CLAUDE_WORKFLOW.md](../CLAUDE_WORKFLOW.md)** - Development workflows

---

## 🧪 Quick Commands Reference

### Start Development
```bash
# Start the application
python start.py

# Or manually:
# Terminal 1: Backend
uvicorn api:app --reload --port 8000

# Terminal 2: Frontend
streamlit run streamlit_app.py --server.port 8501
```

### Run Tests (MANDATORY)
```bash
# Quick validation (30s)
python run_tests.py --suite critical

# Full regression (2min)
python run_tests.py --suite regression

# Component-specific
python run_tests.py --suite auth
python run_tests.py --suite database
python run_tests.py --suite api

# Everything (5min)
python run_tests.py --suite all
```

### E2E Tests (Playwright)
```bash
npm test                           # Run all E2E tests
npx playwright test -g "test name" # Run specific test
npm run test:ui                    # UI mode
node auto_fix_loop.js              # Self-healing loop
```

### Database Health Check
```bash
python -c "from db import db; print(db.health_check())"
```

### Git Commands
```bash
git status                 # Check current state
git log --oneline -5       # Recent commits
git pull origin main       # Pull latest
```

---

## ✅ Task Completion Checklist

Before marking ANY task as complete:

### Planning Phase
- [ ] Read user's request carefully
- [ ] Review appropriate workflow in CLAUDE_WORKFLOW.md
- [ ] Create TodoWrite list if task is complex (3+ steps)
- [ ] Read relevant files before modifying

### Implementation Phase
- [ ] Follow existing code patterns
- [ ] Add proper error handling
- [ ] Validate all inputs
- [ ] Add logging where appropriate
- [ ] Update todos as tasks complete

### Testing Phase (MANDATORY)
- [ ] Run appropriate test suite for the change type
- [ ] Fix any test failures immediately
- [ ] Verify no regressions introduced
- [ ] Test edge cases

### Completion Phase
- [ ] All requested changes implemented
- [ ] All tests passing (no exceptions)
- [ ] Documentation updated if needed
- [ ] Clear summary report prepared with:
  - What was changed
  - Files modified (with line numbers)
  - Test results
  - Usage examples (for new features)

---

## 🎨 Code Style Guidelines

### Python Standards
```python
# ✅ Good: Type hints, docstrings, error handling
def get_user_by_id(user_id: int) -> dict | None:
    """
    Fetch user by ID.

    Args:
        user_id: The user's ID

    Returns:
        User dict or None if not found
    """
    try:
        result = db.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

# ✅ Good: Input validation
if not email or not isinstance(email, str):
    raise ValueError("Invalid email format")

# ❌ Bad: No error handling, SQL injection risk
def bad_example(user_id):
    return db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### Security Requirements
- ✅ Use parameterized queries (Supabase handles this)
- ✅ Validate all inputs
- ✅ Check authentication before operations
- ✅ Use `admin_client` for admin operations (bypasses RLS)
- ❌ Never use string interpolation for queries
- ❌ Never skip input validation

### Naming Conventions
- **Functions**: `snake_case` - `calculate_score()`
- **Classes**: `PascalCase` - `ExamManager`
- **Constants**: `UPPER_SNAKE_CASE` - `MAX_ATTEMPTS`
- **Private**: `_leading_underscore` - `_internal_helper()`

---

## 🚨 Common Issues & Solutions

### Issue: Tests Failing
```bash
# Isolate the issue
python run_tests.py --suite critical

# Fix failures one at a time
# Re-run tests until passing
# NEVER complete task with failing tests
```

### Issue: Database Connection Error
```bash
# Check health
python -c "from db import db; print(db.health_check())"

# Verify .env has correct credentials
# SUPABASE_URL and SUPABASE_KEY must be set
```

### Issue: RLS Blocking Admin Operations
```python
# Use admin_client for admin operations
from db import admin_client

# Regular client (has RLS policies)
result = db.table('users').select('*').execute()

# Admin client (bypasses RLS)
result = admin_client.table('pool_questions').select('*').execute()
```

### Issue: Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 💡 Best Practices Summary

### Always Do:
✅ Use TodoWrite for complex tasks (3+ steps)
✅ Run tests after code changes
✅ Read existing code before modifying
✅ Follow established patterns
✅ Add error handling and validation
✅ Log errors appropriately
✅ Reference files with line numbers
✅ Mark todos complete immediately
✅ Test incrementally during development

### Never Do:
❌ Complete tasks without running tests
❌ Skip error handling
❌ Use string interpolation for SQL
❌ Ignore security implications
❌ Modify code without understanding it
❌ Leave failing tests
❌ Skip input validation
❌ Assume tests pass without running them

---

## 🎯 Your Immediate Next Steps

1. **Read the three key documents:**
   - [.claude_testing_protocol.md](../.claude_testing_protocol.md)
   - [CLAUDE_WORKFLOW.md](../CLAUDE_WORKFLOW.md)
   - [.claude/context_prompt.md](context_prompt.md)

2. **Understand the current git state:**
   ```bash
   git status
   git log --oneline -5
   ```

3. **Check the environment:**
   ```bash
   python -c "from db import db; print(db.health_check())"
   ```

4. **Review the user's request carefully**

5. **Create a TodoWrite list if the task is complex**

6. **Follow the appropriate workflow from CLAUDE_WORKFLOW.md**

7. **Test thoroughly before completing**

---

## ✅ Success Criteria

A task is ONLY complete when:
- ✅ All requested changes implemented correctly
- ✅ Code follows existing patterns
- ✅ Proper error handling and validation added
- ✅ Appropriate tests run and **ALL PASSING**
- ✅ No test regressions introduced
- ✅ Documentation updated (if needed)
- ✅ Clear summary report provided

**Remember**: This is a production application with real users and payments. Quality, security, and testing are non-negotiable.

---

## 🚀 You're Ready!

You now have all the context and protocols needed to work effectively on MockExamify.

**Golden Rule**: If you touched the code, run the tests. If tests fail, fix them. Never complete with failing tests.

**Now proceed with the user's request, following the protocols above.**
