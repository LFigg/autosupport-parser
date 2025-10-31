#!/bin/bash

# GitHub Repository Setup Script
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username

echo "=== Data Domain Autosupport Parser - GitHub Setup ==="
echo ""
echo "Please follow these steps:"
echo ""
echo "1. Go to https://github.com and sign in"
echo "2. Click '+' > 'New repository'"
echo "3. Repository name: autosupport-parser"
echo "4. Description: Data Domain Autosupport Parser - Extract and analyze autosupport data from .tar.gz bundles and .eml email files"
echo "5. Set to Public"
echo "6. DO NOT initialize with README, .gitignore, or license"
echo "7. Click 'Create repository'"
echo ""
echo "8. After creating, run these commands (replace YOUR_GITHUB_USERNAME):"
echo ""
echo "git remote add origin https://github.com/YOUR_GITHUB_USERNAME/autosupport-parser.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "Repository is ready to push!"

# Check current status
echo "Current Git status:"
git status