#!/bin/bash
# Git hygiene helper for bash
# Safely fetch and rebase on main

set -e

echo -e "\033[0;36m=== Git Dev Sync (bash) ===\033[0m"

# Check if we're in a git repo
if [ ! -d ".git" ]; then
    echo -e "\033[0;31mERROR: Not a git repository\033[0m"
    exit 1
fi

# Check for uncommitted changes
STATUS=$(git status --porcelain)
if [ -n "$STATUS" ]; then
    echo -e "\033[0;31mERROR: You have uncommitted changes:\033[0m"
    echo "$STATUS"
    echo -e "\n\033[0;33mCommit or stash your changes first:\033[0m"
    echo -e "\033[0;36m  git add .\033[0m"
    echo -e "\033[0;36m  git commit -m 'WIP: description'\033[0m"
    echo -e "\033[0;36m  git stash\033[0m"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "\033[0;32mCurrent branch: $CURRENT_BRANCH\033[0m"

# Fetch latest from origin
echo -e "\n\033[0;33mFetching from origin...\033[0m"
git fetch origin

# Rebase on origin/main
echo -e "\n\033[0;33mRebasing on origin/main...\033[0m"
if ! git rebase origin/main; then
    echo -e "\n\033[0;31mERROR: Rebase failed with conflicts\033[0m"
    echo -e "\033[0;33mTo resolve:\033[0m"
    echo -e "\033[0;36m  1. Fix conflicts in your editor\033[0m"
    echo -e "\033[0;36m  2. git add <resolved-files>\033[0m"
    echo -e "\033[0;36m  3. git rebase --continue\033[0m"
    echo -e "\n\033[0;33mTo abort:\033[0m"
    echo -e "\033[0;36m  git rebase --abort\033[0m"
    exit 1
fi

echo -e "\n\033[0;32m✓ Successfully rebased on origin/main\033[0m"
echo -e "\033[0;36mYour branch is now up to date\033[0m"
