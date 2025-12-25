#!/bin/bash
# One-time setup: Configure Git to use hooks directory directly
# After this, hooks work automatically - no copying needed!

set -e

echo "🔧 Configuring Git to use hooks directory..."
echo ""

# Configure this repository to use hooks/ directory for Git hooks
git config core.hooksPath hooks

echo "✅ Done! Git hooks are now active."
echo ""
echo "What this means:"
echo "  • Hooks run automatically from the hooks/ directory"
echo "  • No copying to .git/hooks/ needed"
echo "  • Updates are instant when you git pull"
echo "  • Works on any machine after running this once"
echo ""
echo "Safety checks now active:"
echo "  🛡️  git push to main - checks for active users"
echo "  🔄  git pull - updates are automatic"
echo ""
