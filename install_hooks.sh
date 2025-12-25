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
echo "  • Use 'git push --no-verify' to bypass (emergencies only)"
echo ""
echo "To install on your laptop:"
echo "  1. Pull the latest code: git pull origin main"
echo "  2. Run: ./install_hooks.sh"
echo ""
