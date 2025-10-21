#!/bin/bash
# Post-creation script for devcontainer
# Runs automatically after container is created

echo "=== MockExamify DevContainer Setup ==="

# Run main setup script
bash setup.sh

# Install development tools
pip install pytest pytest-cov black flake8 ipython --quiet

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env 2>/dev/null || echo "No .env.example found, skipping"
fi

# Set git config
git config --global pull.rebase true
git config --global init.defaultBranch main

echo "✓ DevContainer setup complete"
echo "Run './run_all.sh' to start both servers"
