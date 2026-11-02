#!/usr/bin/env bash
# ==============================================================================
# ClassPlanner - macOS Standalone Application Build Script
# Creates ClassPlanner.app in the dist/ directory.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Building ClassPlanner for macOS ==="
cd "${ROOT_DIR}"

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous build artifacts
echo "Cleaning old builds..."
rm -rf build dist

# Run PyInstaller build
echo "Compiling application bundle..."
pyinstaller --clean build_scripts/ClassPlanner.spec

echo "=== Build Successful! ==="
echo "Application bundle created at: ${ROOT_DIR}/dist/ClassPlanner.app"
echo "You can launch it by running: open dist/ClassPlanner.app"

