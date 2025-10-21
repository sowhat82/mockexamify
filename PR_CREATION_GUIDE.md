# Pull Request Creation Guide

## Using GitHub CLI (Recommended)

### Prerequisites
```bash
# Install GitHub CLI if not already installed
# Windows (using winget):
winget install --id GitHub.cli

# Or download from: https://cli.github.com/

# Authenticate (one-time setup)
gh auth login
```

### Create PR from Current Branch

```bash
# Push your branch first
git push origin feat/mockexamify-auth-ui

# Create PR with title and body
gh pr create --title "Add authentication and UI improvements" \
  --body "Implements user authentication, admin dashboard, and question pool upload feature" \
  --base main \
  --head feat/mockexamify-auth-ui

# Or use interactive mode (prompts for details)
gh pr create --fill

# After PR is created, view it in browser
gh pr view --web
```

### Advanced Options

```bash
# Create draft PR (for work in progress)
gh pr create --draft --title "WIP: Feature implementation"

# Add reviewers
gh pr create --title "Ready for review" --reviewer username1,username2

# Add labels
gh pr create --title "Bug fix" --label bug,high-priority

# Link to issue
gh pr create --title "Fix login bug" --body "Closes #123"
```

## Using GitHub Web Interface (Fallback)

If GitHub CLI is not available:

1. **Push your branch:**
   ```bash
   git push origin feat/mockexamify-auth-ui
   ```

2. **Navigate to repository:**
   - Go to: https://github.com/YOUR_USERNAME/YOUR_REPO

3. **Create PR:**
   - Click "Pull requests" tab
   - Click green "New pull request" button
   - Set base: `main`, compare: `feat/mockexamify-auth-ui`
   - Click "Create pull request"
   - Fill in title and description
   - Click "Create pull request"

## PowerShell Quick Commands

```powershell
# Create and push branch, then create PR
git push origin feat/mockexamify-auth-ui
gh pr create --fill

# View PR status
gh pr status

# Check PR checks/tests
gh pr checks

# Merge PR after approval
gh pr merge --squash
```

## Bash Quick Commands

```bash
# Create and push branch, then create PR
git push origin feat/mockexamify-auth-ui
gh pr create --fill

# View PR status
gh pr status

# Check PR checks/tests
gh pr checks

# Merge PR after approval
gh pr merge --squash
```

## Common PR Templates

### Feature PR
```
## Description
Brief description of what this PR does

## Changes
- Added user authentication system
- Implemented admin dashboard
- Created question pool upload feature

## Testing
- [ ] Manual testing completed
- [ ] All tests passing
- [ ] No console errors

## Screenshots (if applicable)
[Add screenshots here]
```

### Bug Fix PR
```
## Problem
Description of the bug

## Solution
How this PR fixes it

## Closes
Closes #123
```

## Best Practices

1. **Before creating PR:**
   - Ensure all commits have clear messages
   - Run tests: `pytest` or `python -m pytest`
   - Check for merge conflicts: `./dev-sync.ps1` or `./dev-sync.sh`
   - Review your changes: `git diff main...HEAD`

2. **PR title format:**
   - `feat: Add user authentication` (new feature)
   - `fix: Resolve login redirect issue` (bug fix)
   - `docs: Update README` (documentation)
   - `refactor: Simplify database queries` (code improvement)
   - `test: Add integration tests` (test additions)

3. **PR description checklist:**
   - What problem does this solve?
   - What are the key changes?
   - How was it tested?
   - Any breaking changes?
   - Screenshots/demos (if UI changes)

4. **After PR created:**
   - Respond to review comments promptly
   - Keep PR focused and small when possible
   - Rebase if main has moved ahead: `./dev-sync.ps1`
   - Mark resolved conversations
