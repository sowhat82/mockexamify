#!/bin/bash
# Safe deployment script - checks for active users before pushing to production

set -e  # Exit on error

echo "🔒 Safe Push to Production"
echo "=========================="
echo ""

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "⚠️  You have uncommitted changes:"
    git status -s
    echo ""
    read -p "Do you want to commit these changes first? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Please commit your changes first, then run this script again."
        exit 1
    fi
fi

# Check for active users
echo "Checking for active users in production..."
echo ""

source venv/bin/activate
python check_active_users.py
CHECK_RESULT=$?

echo ""

# Handle different exit codes
if [ $CHECK_RESULT -eq 0 ]; then
    # Safe to deploy
    echo "✅ All checks passed. Proceeding with git push..."
    git push origin main
    echo ""
    echo "🎉 Successfully pushed to main!"
elif [ $CHECK_RESULT -eq 1 ]; then
    # Active users found - do not deploy
    echo "❌ Active users detected. Deployment blocked."
    echo ""
    read -p "Do you want to force push anyway? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "⚠️  Force pushing despite active users..."
        git push origin main
        echo "🎉 Pushed to main (forced)"
    else
        echo "Deployment cancelled. Try again later."
        exit 1
    fi
elif [ $CHECK_RESULT -eq 2 ]; then
    # Caution - some recent activity
    echo "⚠️  Some recent activity detected."
    echo ""
    read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Proceeding with git push..."
        git push origin main
        echo "🎉 Successfully pushed to main!"
    else
        echo "Deployment cancelled."
        exit 1
    fi
else
    echo "❓ Unknown error occurred during user check."
    exit 1
fi
