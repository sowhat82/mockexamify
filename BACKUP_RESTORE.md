# Backup & Restore Guide

## Quick Restore

If you discover a broken feature that was working before, you can restore the last known good state:

### Option 1: Using Git Tag (Recommended)
```bash
# View the backup point
git show backup-working-state-2025-10-11

# Restore the entire codebase to the backup point
git checkout backup-working-state-2025-10-11

# Or restore specific files only
git checkout backup-working-state-2025-10-11 -- streamlit_app.py
git checkout backup-working-state-2025-10-11 -- db.py
git checkout backup-working-state-2025-10-11 -- models.py
git checkout backup-working-state-2025-10-11 -- pages/admin_dashboard.py
```

### Option 2: Using Backup Branch
```bash
# Switch to the backup branch
git checkout backup/working-state-2025-10-11

# Or cherry-pick specific commits
git checkout main
git cherry-pick <commit-hash>
```

### Option 3: Using Commit Hash Directly
```bash
# Restore from the rollback commit
git checkout 5e86f44

# Or restore specific files
git checkout 5e86f44 -- path/to/file.py
```

## What's Backed Up

**Backup Date:** October 11, 2025
**Commit Hash:** `5e86f44c0a7edf006b9bec5268deb45b74aa40bd`
**Git Tag:** `backup-working-state-2025-10-11`
**Git Branch:** `backup/working-state-2025-10-11`

### Backed Up State Includes:
- ✅ Working admin dashboard with comprehensive analytics
- ✅ User management functionality
- ✅ Original working streamlit_app.py with admin navigation
- ✅ Stable db.py with all database operations
- ✅ Working models.py with all data models
- ✅ All core features functioning correctly

### What Was Working:
- Admin dashboard analytics
- User management
- Question pool management
- All navigation and UI elements
- Database operations
- Authentication and authorization

## Checking Available Backups

```bash
# List all backup tags
git tag -l "backup-*"

# List all backup branches
git branch -a | grep backup

# View backup commit details
git show backup-working-state-2025-10-11
```

## Creating New Backups

When making significant changes, create a new backup:

```bash
# Create a tag for current state
git tag -a "backup-working-state-$(date +%Y-%m-%d)" -m "Backup before [description]"

# Create a backup branch
git branch backup/working-state-$(date +%Y-%m-%d)

# Push backups to remote (if needed)
git push origin backup-working-state-$(date +%Y-%m-%d)
git push origin backup/working-state-$(date +%Y-%m-%d)
```

## Emergency Recovery

If the entire application is broken:

```bash
# 1. Stash any current changes
git stash

# 2. Return to last known good state
git checkout backup-working-state-2025-10-11

# 3. Create a new branch from the backup
git checkout -b fix/restore-from-backup

# 4. Test to confirm everything works
streamlit run streamlit_app.py

# 5. If working, merge back to main
git checkout main
git merge fix/restore-from-backup
```

## Notes

- The backup preserves the state before the "production upgrade" that removed admin functionality
- File `db_with_auth.py` contains enhanced authentication features that can be referenced
- All backup points are stored in git history and cannot be lost unless the repository is deleted
- Always test after restoring to ensure compatibility with current database schema

## Support

If you need help restoring or have questions about the backup, check the commit message:

```bash
git log --oneline | grep -i "rollback\|backup"
```

The rollback commit: `5e86f44 Rollback: Restore original working admin dashboard and UI`
