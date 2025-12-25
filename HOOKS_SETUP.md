# Quick Setup for Deployment Safety Hooks

## First Time on Any Machine

After cloning or pulling the repo, run this **one command**:

```bash
git config core.hooksPath hooks
```

Or use the setup script:
```bash
./setup_hooks.sh
```

## That's It!

From now on:
- ✅ `git push origin main` automatically checks for active users
- ✅ `git pull` automatically updates the hooks
- ✅ No reinstallation ever needed
- ✅ Works on all machines after running once

## What Gets Checked

Before every push to main:
- 🔍 Students currently taking exams (last 2 hours)
- 👥 Recently active users (last 30 minutes)
- 📊 Recently completed exams (informational)

If students are taking exams, the push is **blocked** to protect their experience.

## See Full Documentation

📖 [DEPLOYMENT_SAFETY.md](DEPLOYMENT_SAFETY.md) - Complete guide with examples and troubleshooting
