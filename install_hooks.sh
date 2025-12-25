#!/bin/bash
# Legacy wrapper - just runs setup_hooks.sh
# Use setup_hooks.sh or "git config core.hooksPath hooks" instead

echo "ℹ️  This script is deprecated. Please use:"
echo "   ./setup_hooks.sh"
echo ""
echo "Running setup_hooks.sh for you..."
echo ""

./setup_hooks.sh
