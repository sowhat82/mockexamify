# Git Commands Quick Reference

## Basic Git Workflow

### 1. Check Status
See what files have changed:
```bash
git status
```

### 2. Stage Changes
Add specific files:
```bash
git add filename.py
git add app_pages/admin_upload.py
```

Add all changed files:
```bash
git add -A
```
or
```bash
git add .
```

### 3. Commit Changes
Commit with a message:
```bash
git commit -m "Your commit message here"
```

Commit with multi-line message:
```bash
git commit -m "$(cat <<'EOF'
First line of commit message

- Bullet point 1
- Bullet point 2
- Bullet point 3
EOF
)"
```

Bypass pre-commit hooks (if tests are failing):
```bash
git commit --no-verify -m "Your commit message"
```

### 4. Push to Remote
Push to main branch:
```bash
git push
```
or explicitly:
```bash
git push origin main
```

Force push (use with caution!):
```bash
git push --force
```

## Complete Workflow Example

```bash
# 1. Check what changed
git status

# 2. Stage all changes
git add -A

# 3. Commit with message
git commit -m "fix: Description of what was fixed"

# 4. Push to remote
git push
```

## Common Operations

### View Recent Commits
```bash
git log
```

Recent commits (one line each):
```bash
git log --oneline -10
```

### Undo Last Commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Undo Last Commit (discard changes)
```bash
git reset --hard HEAD~1
```

### Pull Latest Changes
```bash
git pull
```

### View Differences
See what changed (unstaged):
```bash
git diff
```

See what changed (staged):
```bash
git diff --cached
```

### Stash Changes
Save changes temporarily:
```bash
git stash
```

Restore stashed changes:
```bash
git stash pop
```

## Branch Operations

### Create New Branch
```bash
git checkout -b feature-name
```

### Switch Branch
```bash
git checkout main
git checkout feature-name
```

### Merge Branch
```bash
# Switch to main first
git checkout main

# Merge feature branch
git merge feature-name
```

## Troubleshooting

### If pre-commit hooks fail:
```bash
# Option 1: Fix the issues and commit again
git commit -m "Your message"

# Option 2: Bypass hooks (use sparingly!)
git commit --no-verify -m "Your message"
```

### If push is rejected:
```bash
# Pull first, then push
git pull
git push
```

### Remove file from staging:
```bash
git restore --staged filename.py
```

### Discard local changes to a file:
```bash
git restore filename.py
```

## Typical MockExamify Workflow

```bash
# 1. Check status
git status

# 2. Stage modified files
git add app_pages/admin_upload.py question_pool_manager.py

# 3. Commit with descriptive message
git commit -m "fix: Handle API rate limits gracefully during question upload"

# 4. Push to main
git push

# If tests fail in pre-commit hooks:
git commit --no-verify -m "fix: Your message here"
git push
```

## Notes

- Always check `git status` before committing to see what will be included
- Use descriptive commit messages (prefix with `fix:`, `feat:`, `refactor:`, etc.)
- The project has pre-commit hooks that run tests and linting - they may fail even if your code is correct
- Use `--no-verify` to bypass hooks if needed, but make sure your changes are actually correct first
- Never force push to main unless you're absolutely sure - it can overwrite others' work
