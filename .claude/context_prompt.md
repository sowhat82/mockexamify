# MockExamify Development Context

You are working on **MockExamify**, a comprehensive full-stack Python application for selling and hosting interactive mock exams. This prompt provides all the context you need to work effectively on this project.

---

## 🎯 Project Overview

**MockExamify** is an interactive mock exam platform with:
- Credit-based payment system (Stripe integration)
- AI-powered answer explanations (OpenRouter/GPT-4)
- PDF report generation
- Admin dashboard with analytics
- Support ticket system
- Secure authentication and user management

**Tech Stack:**
- **Frontend**: Streamlit (Python web framework)
- **Backend**: FastAPI (REST API)
- **Database**: Supabase (PostgreSQL with built-in auth)
- **Payments**: Stripe
- **AI**: OpenRouter API (GPT-4 models)
- **PDF**: ReportLab
- **Testing**: Pytest + Playwright (E2E)

---

## 📋 CRITICAL: Always Follow These Protocols

### 1. Testing Protocol (MANDATORY)

**You MUST run tests after any code changes. This is non-negotiable.**

Read the complete testing protocol: [.claude_testing_protocol.md](.claude_testing_protocol.md)

Quick reference:
```bash
# After modifying core files (streamlit_app.py, auth_utils.py, db.py, models.py, config.py)
python run_tests.py --suite critical

# After adding new features
python run_tests.py --suite regression

# Before completing any task
python run_tests.py --suite critical

# For specific components
python run_tests.py --suite auth        # Authentication changes
python run_tests.py --suite database    # Database changes
python run_tests.py --suite api         # API changes
```

**Golden Rule**: Never complete a task with failing tests. If tests fail, fix them first.

### 2. Development Workflow (MANDATORY)

**You MUST follow standard workflows for different task types.**

Read the complete workflow guide: [CLAUDE_WORKFLOW.md](CLAUDE_WORKFLOW.md)

Quick reference:
- **Bug fixes**: Understand → Plan → Fix → Test → Report
- **Features**: Plan → Design → Implement → Test → Document → Report
- **Refactoring**: Baseline → Incremental changes → Test continuously
- **Security**: Assess → Fix → Security test → Document

### 3. TodoWrite Usage (MANDATORY)

**You MUST use TodoWrite for complex tasks (3+ steps).**

Create comprehensive task lists at the start:
```javascript
[
  {"content": "Analyze current implementation", "status": "in_progress", "activeForm": "Analyzing..."},
  {"content": "Design solution", "status": "pending", "activeForm": "Designing..."},
  {"content": "Implement changes", "status": "pending", "activeForm": "Implementing..."},
  {"content": "Run tests", "status": "pending", "activeForm": "Running tests"},
  {"content": "Report results", "status": "pending", "activeForm": "Reporting results"}
]
```

Mark tasks complete IMMEDIATELY after finishing each one.

---

## 📁 Codebase Structure

### Core Application Files

**Main Application:**
- **[streamlit_app.py](streamlit_app.py)** - Main Streamlit UI, page routing, session state
- **[api.py](api.py)** - FastAPI backend with REST endpoints
- **[db.py](db.py)** - Database operations, Supabase client, all queries
- **[models.py](models.py)** - Pydantic models, data schemas
- **[config.py](config.py)** - Configuration, environment variables

**Authentication & Security:**
- **[auth_utils.py](auth_utils.py)** - Login, registration, JWT tokens, sessions
- **[security_utils.py](security_utils.py)** - Input validation, sanitization

**Integrations:**
- **[stripe_utils.py](stripe_utils.py)** - Payment processing, webhooks
- **[openrouter_utils.py](openrouter_utils.py)** - AI explanations, GPT-4 calls
- **[pdf_utils.py](pdf_utils.py)** - Report generation with ReportLab

**Admin Features:**
- **[app_pages/admin_dashboard.py](app_pages/admin_dashboard.py)** - Analytics, metrics
- **[app_pages/admin_tickets.py](app_pages/admin_tickets.py)** - Support ticket management
- **[admin_utils.py](admin_utils.py)** - Admin operations, user management

**Testing Infrastructure:**
- **[run_tests.py](run_tests.py)** - Python test runner (multiple suites)
- **[auto_fix_loop.js](auto_fix_loop.js)** - Self-healing E2E test loop
- **[playwright.config.ts](playwright.config.ts)** - E2E test configuration
- **[tests/e2e/](tests/e2e/)** - Playwright E2E tests

### Database Schema

**Main Tables:**
- **users** - User accounts (id, email, password_hash, credits_balance, role, created_at)
- **mocks** - Exam definitions (id, title, description, questions_json, created_by)
- **attempts** - Exam submissions (id, user_id, mock_id, score, answers_json, completed_at)
- **tickets** - Support tickets (id, user_id, subject, description, status, created_at)
- **pool_questions** - Question pools for exam generation
- **question_pools** - Pool metadata and organization

**Access Patterns:**
- Regular users: RLS policies restrict to own data
- Admins: Use `admin_client` in db.py to bypass RLS
- Service role key: For admin operations (SUPABASE_SERVICE_KEY)

---

## 🔧 Development Environment

### Running the Application

**Start the app:**
```bash
# Recommended: Use start script
python start.py

# Or manually:
# Terminal 1: Backend
uvicorn api:app --reload --port 8000

# Terminal 2: Frontend
streamlit run streamlit_app.py --server.port 8501
```

**Access URLs:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Environment Variables

Required in `.env`:
```env
# Database & Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key  # For admin operations

# Payments
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# AI
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o-mini

# Security
SECRET_KEY=your_jwt_secret
ENVIRONMENT=development
```

### Testing Commands

**Python Tests:**
```bash
python run_tests.py --suite critical       # Core functionality (30s)
python run_tests.py --suite regression     # Full validation (2min)
python run_tests.py --suite auth           # Auth-specific
python run_tests.py --suite database       # Database-specific
python run_tests.py --suite all            # Everything (5min)
```

**E2E Tests (Playwright):**
```bash
npm test                    # Run all E2E tests
npx playwright test -g "test name"  # Run specific test
npm run test:ui            # UI mode
node auto_fix_loop.js      # Self-healing loop
```

---

## 🎨 Code Style & Patterns

### Python Style

**Good Patterns (Follow These):**
```python
# Type hints and docstrings
def get_user_by_email(email: str) -> dict | None:
    """
    Fetch user by email address.

    Args:
        email: User's email address

    Returns:
        User dict or None if not found
    """
    try:
        result = db.table('users').select('*').eq('email', email).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None

# Input validation
if not email or not isinstance(email, str):
    raise ValueError("Invalid email format")

# Proper error handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return error_response
```

**Security Patterns:**
```python
# ✅ Use parameterized queries (Supabase handles this)
db.table('users').select('*').eq('id', user_id).execute()

# ❌ Never use string interpolation for queries
# query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection!

# ✅ Validate all inputs
from security_utils import sanitize_input, validate_email

# ✅ Check authentication
if not is_authenticated(session):
    raise UnauthorizedException()
```

### Naming Conventions
- Functions: `snake_case` - `calculate_exam_score()`
- Classes: `PascalCase` - `ExamManager`
- Constants: `UPPER_SNAKE_CASE` - `MAX_ATTEMPTS = 3`
- Private: `_leading_underscore` - `_internal_helper()`

---

## 🚨 Common Issues & Solutions

### Issue: Database Connection Errors
```bash
# Check connection
python -c "from db import db; print(db.health_check())"

# Verify .env has correct SUPABASE_URL and SUPABASE_KEY
```

### Issue: Tests Failing
```bash
# Run specific suite to isolate issue
python run_tests.py --suite critical

# Check if server is running (some tests need it)
# Fix the failing test before proceeding
```

### Issue: Import Errors
```bash
# Install dependencies
pip install -r requirements.txt

# Check if in virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Issue: RLS (Row Level Security) Blocking Admin
```python
# Use admin_client for admin operations
from db import admin_client

# Regular client (has RLS)
result = db.table('users').select('*').execute()

# Admin client (bypasses RLS)
result = admin_client.table('pool_questions').select('*').execute()
```

---

## 📊 Git Workflow

**Current Branch:**
```bash
# Check with
git status
```

**Recent Commits Show:**
- Password reset system implemented
- Admin ticket system working
- RLS policies for security
- Question pool management

**Commit Message Format:**
```
feat: Add feature description

- Detailed change 1
- Detailed change 2
- Test results: All passed

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 🎯 Common Tasks Quick Reference

### Add New Streamlit Page
1. Create file in `app_pages/` (e.g., `new_feature.py`)
2. Follow pattern from existing pages
3. Add to navigation in `streamlit_app.py`
4. Test with `streamlit run streamlit_app.py`

### Add API Endpoint
1. Define in `api.py` following FastAPI patterns
2. Use dependency injection for db access
3. Add authentication decorator if needed
4. Test with API docs at http://localhost:8000/docs

### Add Database Query
1. Add function to `db.py`
2. Use existing Supabase client patterns
3. Add error handling
4. Test with `python run_tests.py --suite database`

### Fix Security Issue
1. Follow Security Fix Workflow in CLAUDE_WORKFLOW.md
2. Update affected files (usually auth_utils.py or security_utils.py)
3. Run `python run_tests.py --suite security`
4. Document the fix

---

## 💡 Best Practices Summary

### Always Do:
✅ Use TodoWrite for complex tasks (3+ steps)
✅ Run tests after code changes
✅ Read existing code before modifying
✅ Follow established patterns
✅ Add error handling
✅ Validate inputs
✅ Log errors
✅ Update documentation
✅ Reference files with line numbers in reports
✅ Mark todos complete immediately

### Never Do:
❌ Complete tasks without running tests
❌ Skip error handling
❌ Use string interpolation for SQL
❌ Ignore security implications
❌ Modify code without understanding it
❌ Leave failing tests
❌ Commit without testing
❌ Skip input validation

---

## 📚 Key Documentation Files

**Read These First:**
1. **[README.md](README.md)** - Project overview, setup instructions
2. **[.claude_testing_protocol.md](.claude_testing_protocol.md)** - Testing requirements (CRITICAL)
3. **[CLAUDE_WORKFLOW.md](CLAUDE_WORKFLOW.md)** - Standard workflows (CRITICAL)

**Reference Documentation:**
- **[BACKUP_RESTORE.md](BACKUP_RESTORE.md)** - Restore previous versions
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Production deployment
- **[DEV_SETUP_README.md](DEV_SETUP_README.md)** - Development setup
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing strategies

**Admin & Features:**
- **[QUESTION_POOL_ADMIN_GUIDE.md](QUESTION_POOL_ADMIN_GUIDE.md)** - Question pool management
- **[ADMIN_DASHBOARD_GUIDE.md](if exists)** - Admin features

---

## 🎯 Your Task Checklist

When starting work on this project, follow this checklist:

### Before Making Changes:
- [ ] Read the user's request carefully
- [ ] Review [CLAUDE_WORKFLOW.md](CLAUDE_WORKFLOW.md) for the appropriate workflow
- [ ] Check [.claude_testing_protocol.md](.claude_testing_protocol.md) for testing requirements
- [ ] Create TodoWrite list for complex tasks (3+ steps)
- [ ] Read relevant files before modifying them
- [ ] Understand existing patterns in the codebase

### While Making Changes:
- [ ] Follow established code patterns
- [ ] Add proper error handling
- [ ] Validate all inputs
- [ ] Add logging where appropriate
- [ ] Update todos as you complete tasks
- [ ] Test incrementally if possible

### After Making Changes:
- [ ] Run appropriate test suite:
  - `python run_tests.py --suite critical` (minimum)
  - `python run_tests.py --suite regression` (for features)
  - `python run_tests.py --suite [component]` (for specific changes)
- [ ] Fix any test failures before proceeding
- [ ] Update documentation if needed
- [ ] Commit with descriptive message (if appropriate)

### Before Completing Task:
- [ ] Verify all requested changes are complete
- [ ] Run final test validation
- [ ] Ensure no tests are failing
- [ ] Prepare clear summary report including:
  - What was changed
  - Files modified (with line numbers)
  - Test results
  - Usage examples (if new feature)

---

## 🚀 Quick Start Commands

```bash
# Start development
python start.py

# Run tests
python run_tests.py --suite critical

# Check database
python -c "from db import db; print(db.health_check())"

# Run E2E tests
npm test

# View API docs
# Navigate to http://localhost:8000/docs

# Check git status
git status
git log --oneline -5
```

---

## 📞 Emergency Procedures

**If Tests Are Failing:**
1. Read error messages carefully
2. Run specific test suite to isolate issue
3. Fix one failure at a time
4. Re-run tests until passing
5. Never complete task with failing tests

**If Database Won't Connect:**
1. Check .env file has correct credentials
2. Verify Supabase project is active
3. Test with health check command
4. Check RLS policies if admin operations failing

**If Imports Are Broken:**
1. Verify virtual environment is activated
2. Run `pip install -r requirements.txt`
3. Check for circular import issues
4. Restart Python interpreter

---

## ✅ Success Criteria

A task is only complete when ALL of these are true:
- ✅ All requested changes implemented correctly
- ✅ Code follows existing patterns and style
- ✅ Proper error handling added
- ✅ Input validation included
- ✅ Appropriate tests run and PASSED
- ✅ No test regressions introduced
- ✅ Documentation updated if needed
- ✅ No security vulnerabilities introduced
- ✅ Clear summary report provided to user

---

## 🎓 Remember

**You are working on a production application with real users and payments.**

- Quality and security are paramount
- Testing is mandatory, not optional
- Follow established patterns
- When in doubt, ask the user
- Never rush or skip steps
- Document as you go

**Golden Rule**: If you touched the code, run the tests. If tests fail, fix them. Never complete with failing tests.

---

**Now you have everything you need to work effectively on MockExamify. Follow the workflows, run the tests, and build great features!**
