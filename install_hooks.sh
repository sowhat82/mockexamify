#!/bin/bash
# Install Git hooks for safe deployment

set -e

echo "🔧 Installing Git hooks..."
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository root directory"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install pre-push hook
if [ -f "hooks/pre-push" ]; then
    cp hooks/pre-push .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
    echo "✅ Installed pre-push hook"
else
    echo "❌ Error: hooks/pre-push not found"
    exit 1
fi

# Install post-merge hook (auto-updates hooks after git pull)
if [ -f "hooks/post-merge" ]; then
    cp hooks/post-merge .git/hooks/post-merge
    chmod +x .git/hooks/post-merge
    echo "✅ Installed post-merge hook (auto-updates on git pull)"
else
    echo "⚠️  Warning: hooks/post-merge not found (optional)"
fi

# Make check_active_users.py executable
if [ -f "check_active_users.py" ]; then
    chmod +x check_active_users.py
    echo "✅ Made check_active_users.py executable"
fi

echo ""
echo "🎉 Git hooks installed successfully!"
echo ""
echo "What this means:"
echo "  • Every 'git push origin main' will check for active users first"
echo "  • Push will be blocked if students are taking exams"
echo "  • You'll be prompted if there's recent activity"
echo "  • Hooks auto-update after 'git pull' (no need to reinstall)"
echo "  • Use 'git push --no-verify' to bypass (emergencies only)"
echo ""
echo "First-time setup on new machines:"
echo "  1. Pull the code: git pull origin main"
echo "  2. Run once: ./install_hooks.sh"
echo "  3. Future updates: Automatic on git pull!"
echo ""
