#!/usr/bin/env pwsh
# Git hygiene helper for Windows PowerShell
# Safely fetch and rebase on main

$ErrorActionPreference = "Stop"

Write-Host "=== Git Dev Sync (Windows) ===" -ForegroundColor Cyan

# Check if we're in a git repo
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Not a git repository" -ForegroundColor Red
    exit 1
}

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "ERROR: You have uncommitted changes:" -ForegroundColor Red
    Write-Host $status
    Write-Host "`nCommit or stash your changes first:" -ForegroundColor Yellow
    Write-Host "  git add ." -ForegroundColor Cyan
    Write-Host "  git commit -m 'WIP: description'" -ForegroundColor Cyan
    Write-Host "  git stash" -ForegroundColor Cyan
    exit 1
}

# Get current branch
$current_branch = git branch --show-current
Write-Host "Current branch: $current_branch" -ForegroundColor Green

# Fetch latest from origin
Write-Host "`nFetching from origin..." -ForegroundColor Yellow
git fetch origin
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to fetch from origin" -ForegroundColor Red
    exit 1
}

# Rebase on origin/main
Write-Host "`nRebasing on origin/main..." -ForegroundColor Yellow
git rebase origin/main
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: Rebase failed with conflicts" -ForegroundColor Red
    Write-Host "To resolve:" -ForegroundColor Yellow
    Write-Host "  1. Fix conflicts in your editor" -ForegroundColor Cyan
    Write-Host "  2. git add <resolved-files>" -ForegroundColor Cyan
    Write-Host "  3. git rebase --continue" -ForegroundColor Cyan
    Write-Host "`nTo abort:" -ForegroundColor Yellow
    Write-Host "  git rebase --abort" -ForegroundColor Cyan
    exit 1
}

Write-Host "`n✓ Successfully rebased on origin/main" -ForegroundColor Green
Write-Host "Your branch is now up to date" -ForegroundColor Cyan
