# MockExamify - Development Workflow Guide

## 🚀 Quick Start

### First Time Setup

**Windows (PowerShell):**
```powershell
# Clone and navigate to project
git clone <repository-url>
cd MockExamify

# Run setup script
.\setup.ps1

# Copy environment template
Copy-Item .env.example .env
# Edit .env with your actual credentials

# Start both servers
.\run_all.ps1
```

**Linux/macOS/Codespaces (bash):**
```bash
# Clone and navigate to project
git clone <repository-url>
cd MockExamify

# Run setup script
bash setup.sh

# Copy environment template
cp .env.example .env
# Edit .env with your actual credentials

# Start both servers
bash run_all.sh
```

### URLs
- **Flask API:** http://localhost:5000
- **Streamlit UI:** http://localhost:8501

---

## 📋 Daily Development Routine

### 1. Start a New Task

**Option A: New Feature Branch**
```bash
# Switch to main and pull latest
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/your-feature-name
```

**Option B: Resume Existing Branch**
```bash
# Fetch and switch to branch
git fetch origin
git checkout feat/your-feature-name

# Sync with main (rebase)
./dev-sync.ps1      # Windows
bash dev-sync.sh    # Linux/macOS
```

### 2. Code and Test

**Start Servers (VS Code):**
- Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
- Type: "Tasks: Run Task"
- Select: "Run: Both Servers (Flask + Streamlit)"

**Start Servers (Terminal):**
```powershell
# Windows
.\run_all.ps1
```
```bash
# Linux/macOS/Codespaces
bash run_all.sh
```

**Run Tests:**
```bash
# Activate venv first
.\venv\Scripts\Activate.ps1    # Windows
source venv/bin/activate        # Linux/macOS

# Run tests
pytest
```

### 3. Commit Changes

```bash
# Check status
git status

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add question pool upload feature"

# Push to remote
git push origin feat/your-feature-name
```

### 4. Create Pull Request

**Using GitHub CLI (Recommended):**
```bash
gh pr create --fill
```

**Using Browser:**
See [PR_CREATION_GUIDE.md](./PR_CREATION_GUIDE.md) for detailed instructions.

---

## 🔄 Git Workflow Commands

### Branch Management

```bash
# List all branches
git branch -a

# Switch to existing branch
git checkout feat/feature-name

# Create and switch to new branch
git checkout -b feat/new-feature

# Delete local branch
git branch -d feat/old-feature
```

### Syncing with Main

**Safe Rebase (Recommended):**
```powershell
# Windows
.\dev-sync.ps1
```
```bash
# Linux/macOS/Codespaces
bash dev-sync.sh
```

**Manual Rebase:**
```bash
git fetch origin
git rebase origin/main
```

### Handling Merge Conflicts

```bash
# If rebase fails with conflicts:
# 1. Fix conflicts in your editor
# 2. Stage resolved files
git add <resolved-file>

# 3. Continue rebase
git rebase --continue

# Or abort and try merge instead
git rebase --abort
git merge origin/main
```

---

## 🐳 GitHub Codespaces

### Opening in Codespaces

1. Go to GitHub repository
2. Click green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main"

### Post-Creation

The devcontainer will automatically:
- Install Python 3.11
- Create virtual environment
- Install dependencies
- Forward ports 5000 and 8501
- Install VS Code extensions

**Start servers:**
```bash
bash run_all.sh
```

**Access URLs:**
- Codespaces will provide public URLs for both ports
- Click "Open in Browser" notification

---

## 🛠️ VS Code Tasks

Press `Ctrl+Shift+P` and search for "Tasks: Run Task", then select:

| Task | Description |
|------|-------------|
| **Setup: Install Dependencies** | Runs setup script (idempotent) |
| **Run: Flask API Only** | Starts Flask on port 5000 |
| **Run: Streamlit UI Only** | Starts Streamlit on port 8501 |
| **Run: Both Servers** | Starts both concurrently (default) |

---

## 📦 Environment Configuration

### Required Files

**`.streamlit/secrets.toml`** - Streamlit secrets
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
OPENROUTER_API_KEY = "sk-or-v1-your-key"
STRIPE_PUBLISHABLE_KEY = "pk_test_your-key"
STRIPE_SECRET_KEY = "sk_test_your-key"
DEMO_MODE = "false"
ENVIRONMENT = "development"
```

**`.env`** - Flask environment variables (copy from `.env.example`)

### Development Modes

| Mode | DEMO_MODE | ENVIRONMENT | Behavior |
|------|-----------|-------------|----------|
| Production | false | production | Real DB, no quick logins |
| Development | false | development | Real DB, quick logins |
| Demo | true | production | Mock data, no DB writes |

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest test_database.py
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Smoke Tests
See [SMOKE_TESTS.md](./SMOKE_TESTS.md) for quick validation commands.

---

## 🚨 Troubleshooting

### Setup Issues

**Problem:** `Python not found`
**Solution:** Install Python 3.10+ from [python.org](https://www.python.org/downloads/)

**Problem:** `Virtual environment creation failed`
**Solution:**
```bash
python -m pip install --upgrade pip
python -m pip install virtualenv
```

### Server Issues

**Problem:** `Port 5000/8501 already in use`
**Solution (Windows):**
```powershell
# Find process using port
Get-NetTCPConnection -LocalPort 5000 -State Listen | Select-Object OwningProcess
# Kill process
Stop-Process -Id <PID> -Force
```

**Solution (Linux/macOS):**
```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9
lsof -ti:8501 | xargs kill -9
```

### Git Issues

**Problem:** `Rebase failed with conflicts`
**Solution:** See "Handling Merge Conflicts" section above

**Problem:** `Detached HEAD state`
**Solution:**
```bash
git checkout main
git checkout feat/your-branch
```

### Import Errors

**Problem:** `ModuleNotFoundError`
**Solution:**
```powershell
# Windows
.\setup.ps1
.\venv\Scripts\Activate.ps1
```
```bash
# Linux/macOS
bash setup.sh
source venv/bin/activate
```

---

## 📚 Additional Resources

- [GIT_QUICKSTART.md](./GIT_QUICKSTART.md) - Git command reference
- [PR_CREATION_GUIDE.md](./PR_CREATION_GUIDE.md) - Pull request workflows
- [SMOKE_TESTS.md](./SMOKE_TESTS.md) - Environment validation
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Testing documentation

---

## 🔐 Security Checklist

- [ ] Never commit `.env` or `secrets.toml` files
- [ ] Use `.env.example` as template only
- [ ] Rotate API keys if accidentally committed
- [ ] Use different keys for dev/prod environments
- [ ] Enable 2FA on GitHub account
- [ ] Review `.gitignore` regularly

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feat/amazing-feature`
3. Commit changes: `git commit -m 'feat: Add amazing feature'`
4. Push to branch: `git push origin feat/amazing-feature`
5. Open Pull Request

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions
- `chore:` Maintenance tasks

---

## 📞 Support

If you encounter issues:

1. Check [Troubleshooting](#-troubleshooting) section
2. Run smoke tests: see [SMOKE_TESTS.md](./SMOKE_TESTS.md)
3. Search existing GitHub issues
4. Create new issue with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version)
   - Relevant logs

---

**Happy coding! 🎉**
