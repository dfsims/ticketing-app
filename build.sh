#!/bin/bash

# Build script for Ticketing System App
# This script builds the React frontend and prepares it for Databricks Apps deployment

set -e  # Exit on error

echo "======================================"
echo "Ticketing System - Build Script"
echo "======================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $PWD"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm is not installed or not in PATH"
    echo ""
    echo "This script requires Node.js and npm to build the frontend."
    echo ""
    echo "Options:"
    echo "  1. Install Node.js locally from: https://nodejs.org/"
    echo "  2. Run this script on your local machine (not in Databricks)"
    echo "  3. Use GitHub Actions or CI/CD to build automatically"
    echo ""
    echo "After building, sync the backend/static/ directory to Databricks."
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"
echo ""

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ ERROR: package.json not found"
    echo "Make sure you're running this script from the ticketing-app directory"
    exit 1
fi

# Install dependencies
echo "[1/3] Installing npm dependencies..."
echo "--------------------------------------"
if [ ! -d "node_modules" ]; then
    npm install
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed (run 'npm install' to update)"
fi
echo ""

# Build frontend
echo "[2/3] Building React frontend..."
echo "--------------------------------------"
npm run build
echo "✓ Frontend built successfully"
echo ""

# Verify build output
echo "[3/3] Verifying build output..."
echo "--------------------------------------"

if [ ! -d "backend/static" ]; then
    echo "❌ ERROR: backend/static directory not created"
    exit 1
fi

if [ ! -f "backend/static/index.html" ]; then
    echo "❌ ERROR: index.html not found in backend/static"
    exit 1
fi

# Count files in backend/static
FILE_COUNT=$(find backend/static -type f | wc -l)
echo "✓ Build output verified"
echo "✓ Generated $FILE_COUNT files in backend/static/"
echo ""

# Check for assets
if [ -d "backend/static/assets" ]; then
    ASSET_COUNT=$(find backend/static/assets -type f | wc -l)
    echo "✓ Generated $ASSET_COUNT asset files (JS, CSS, etc.)"
fi

echo ""
echo "======================================"
echo "✅ BUILD SUCCESSFUL!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Review the built files in backend/static/"
echo "  2. Sync this directory to your Databricks workspace"
echo "  3. Deploy or redeploy your Databricks App"
echo ""
echo "The app will now serve the compiled frontend."
echo ""