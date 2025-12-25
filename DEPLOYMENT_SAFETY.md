# Deployment Safety Guide

This project includes automatic safety checks to prevent disrupting students during deployments.

## 🔒 Automatic Pre-Push Checks

When you push to `main` branch from **anywhere** (Codespaces, laptop, CI/CD), the system automatically:

1. ✅ Checks for students currently taking exams
2. ✅ Checks for recently active users
3. ✅ Blocks push if exams are in progress
4. ⚠️  Prompts for confirmation if recent activity detected

## 📦 Setup (One-Time)

### In This Codespace (Already Installed)
The hooks are already installed and active in this environment.

### On Your Laptop (First Time Only)
After pulling the latest code:

```bash
git pull origin main
./install_hooks.sh
```

This installs both hooks into your local `.git/hooks/` directory:
- `pre-push` - Checks for active users before push
- `post-merge` - Auto-updates hooks after future pulls

### On Other Machines
Same as laptop - just run `./install_hooks.sh` **once** after cloning/pulling.

### Automatic Updates
After the first-time setup, the hooks **automatically update** when you run `git pull`:

```bash
git pull origin main

# Output:
🔄 Post-merge: Checking if hooks need updating...
🆕 Hook updates detected. Reinstalling...
✅ Hooks installed/updated successfully!
```

You never need to run `./install_hooks.sh` again on that machine!

## 🚀 How It Works

### Normal Push (Safe)
```bash
git push origin main

# Output:
🔒 Pre-push hook: Checking for active users before pushing to main...

🔍 Checking for active users in production...

📝 Checking for active in-progress exams...
✅ No active in-progress exams

👥 Checking for users active in last 30 minutes...
✅ No recently active users

============================================================
✅ SAFE TO DEPLOY
   No active users detected in the last 30 minutes

✅ All checks passed. Proceeding with push...
```

### Push Blocked (Students Taking Exams)
```bash
git push origin main

# Output:
⚠️  WARNING: 3 active in-progress exam(s) found!
   - User ID: abc-123, Started: 2025-12-25T08:15:00Z
   ...

============================================================
❌ DEPLOYMENT NOT RECOMMENDED
   Reason: 3 user(s) currently taking exams

❌ PUSH BLOCKED: Active users detected.

Students are currently taking exams. Pushing now could disrupt their experience.

Options:
  1. Wait a few minutes and try again
  2. Deploy during off-peak hours
  3. Use 'git push --no-verify' to bypass this check (NOT recommended)
```

### Push with Recent Activity (User Decision)
```bash
git push origin main

# Output:
⚠️  CAUTION ADVISED
   2 user(s) recently active

⚠️  Recent activity detected. Push with caution.

Do you want to proceed with the push? [y/N]
```

## 🛠️ Manual Check

Check for active users without pushing:

```bash
python check_active_users.py          # Default: 30 min threshold
python check_active_users.py 60       # Custom: 60 min threshold
```

## 🚨 Emergency Override

If you absolutely must push despite active users:

```bash
git push --no-verify origin main
```

⚠️ **Warning**: This bypasses all safety checks. Only use in emergencies!

## ⚙️ Configuration

Edit `check_active_users.py` to adjust thresholds:

- `minutes_threshold`: How far back to check for recent activity (default: 30 min)
- `max_exam_duration_hours`: How old before an exam is considered stale (default: 2 hours)

## 📋 What Gets Checked

### 1. In-Progress Exams
- Exams with status `in_progress` started within last 2 hours
- Blocks push if found (students mid-exam)

### 2. Recently Active Users
- Users with `updated_at` within threshold (default 30 min)
- Prompts for confirmation if found

### 3. Recently Completed Exams
- Exams completed within threshold
- Informational only (doesn't block)

### 4. Stale Attempts
- In-progress exams older than 2 hours
- Informational only (likely abandoned sessions)

## 🔄 How Claude Code Uses This

When you ask Claude Code to "push to git main", it will:

1. Run `python check_active_users.py` first
2. Review the results
3. Only proceed with push if safe
4. Inform you if active users are detected
5. Ask for confirmation if needed

## 🎯 Best Practices

1. **Deploy during off-peak hours** when possible
2. **Check manually** before large deployments: `python check_active_users.py`
3. **Never force push** during peak hours (9 AM - 10 PM local time)
4. **Communicate** with users about planned maintenance if needed

## 🐛 Troubleshooting

### Hook not running?
```bash
# Reinstall hooks
./install_hooks.sh

# Verify installation
ls -la .git/hooks/pre-push
```

### Hook giving errors?
```bash
# Check Python environment
source venv/bin/activate
python check_active_users.py

# Check database connection
python -c "from db import DatabaseManager; db = DatabaseManager(); print('✅ DB connected')"
```

### Need to disable temporarily?
```bash
# Option 1: Use --no-verify for one push
git push --no-verify origin main

# Option 2: Remove hook temporarily
mv .git/hooks/pre-push .git/hooks/pre-push.disabled

# Option 3: Re-enable
mv .git/hooks/pre-push.disabled .git/hooks/pre-push
```

## 📁 Files

- `hooks/pre-push` - Git hook that runs before push
- `install_hooks.sh` - Installation script
- `check_active_users.py` - Active user checker
- `safe_push.sh` - Interactive safe push wrapper (alternative to hook)
- `DEPLOYMENT_SAFETY.md` - This file

## 🎓 Why This Matters

Deploying while students are taking exams can cause:
- App restarts mid-exam
- Lost progress
- Confused/frustrated students
- Potential data loss
- Poor user experience

These checks ensure deployments happen at safe times! 🛡️
