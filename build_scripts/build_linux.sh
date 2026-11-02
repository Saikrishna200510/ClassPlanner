#!/usr/bin/env bash
# ==============================================================================
# ClassPlanner - Linux Standalone Binary Build Script
# Creates standalone ELF binary in dist/ClassPlanner
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Building ClassPlanner for Linux ==="
cd "${ROOT_DIR}"

if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

echo "Cleaning previous build artifacts..."
rm -rf build dist

echo "Compiling Linux binary..."
pyinstaller --clean build_scripts/ClassPlanner.spec

echo "=== Build Successful! ==="
echo "Standalone Linux binary created at: ${ROOT_DIR}/dist/ClassPlanner"
echo "You can launch it by running: ./dist/ClassPlanner"

