# ⚠️ IMPORTANT: First Time Setup

If this is your first time pulling this repo on a new machine, run this **one command**:

```bash
git config core.hooksPath hooks
```

This enables automatic deployment safety checks that prevent pushing while students are taking exams.

## What This Does
- Blocks `git push` if students are mid-exam
- Auto-updates on every `git pull`
- One command, works forever

## Quick Setup
```bash
./setup_hooks.sh
```

---

**Only need to run once per machine. After that, everything is automatic.**

See [HOOKS_SETUP.md](HOOKS_SETUP.md) for details.
