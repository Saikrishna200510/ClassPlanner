#!/usr/bin/env bash
# ==============================================================================
# ClassPlanner - macOS Standalone Application & DMG Installer Build Script
# Creates ClassPlanner.app and ClassPlanner-v1.0.0-macOS.dmg in the dist/ directory.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Building ClassPlanner for macOS ==="
cd "${ROOT_DIR}"

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller & Pillow..."
    pip install pyinstaller Pillow
fi

# Clean previous build artifacts
echo "Cleaning old builds..."
rm -rf build dist

# Run PyInstaller build
echo "Compiling application bundle with PyInstaller..."
pyinstaller --clean build_scripts/ClassPlanner.spec

echo "Application bundle created at: ${ROOT_DIR}/dist/ClassPlanner.app"

# Build DMG installer
echo "Building DMG installer..."
bash "${SCRIPT_DIR}/build_macos_dmg.sh"

echo "=== macOS Build Completed Successfully! ==="
