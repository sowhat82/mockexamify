# Git Quick Start Guide

## Prerequisites
Run once to configure git for this workflow:
```bash
git config pull.rebase true
git config fetch.prune true
```

---

## A. Start a New Task

### Bash/Linux/macOS
```bash
git switch main
git pull --ff-only
# Replace 'your-feature-name' with actual feature like: auth-ui, devops-setup, etc.
git switch -c feat/your-feature-name
```

**Example:**
```bash
git switch -c feat/devops-workflow-setup
```

### Windows PowerShell
```powershell
git switch main
git pull --ff-only
# Replace 'your-feature-name' with actual feature like: auth-ui, devops-setup, etc.
git switch -c feat/your-feature-name
```

**Example:**
```powershell
git switch -c feat/devops-workflow-setup
```

---

## B. Resume a Task on Another Device

### Bash/Linux/macOS
```bash
git fetch origin
git switch feat/mockexamify-auth-ui
git rebase origin/main
```

### Windows PowerShell
```powershell
git fetch origin
git switch feat/mockexamify-auth-ui
git rebase origin/main
```

---

## C. Pause and Hand Off Work

### Bash/Linux/macOS
```bash
git add .
git commit -m "WIP: describe current progress"
git push -u origin feat/mockexamify-auth-ui
```

### Windows PowerShell
```powershell
git add .
git commit -m "WIP: describe current progress"
git push -u origin feat/mockexamify-auth-ui
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Check current branch | `git branch --show-current` |
| See status | `git status` |
| View recent commits | `git log --oneline -5` |
| Undo last commit (keep changes) | `git reset --soft HEAD~1` |
| Abort rebase | `git rebase --abort` |
