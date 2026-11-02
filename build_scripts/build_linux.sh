#!/usr/bin/env bash
# ==============================================================================
# ClassPlanner - Linux Application & Package Build Script
# Compiles binary with PyInstaller and builds .deb & .AppImage packages.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Building ClassPlanner for Linux ==="
cd "${ROOT_DIR}"

if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller & Pillow..."
    pip install pyinstaller Pillow
fi

echo "Cleaning previous build artifacts..."
rm -rf build dist

echo "Compiling Linux binary with PyInstaller..."
pyinstaller --clean build_scripts/ClassPlanner.spec

echo "Building Linux .deb and .AppImage packages..."
bash "${SCRIPT_DIR}/build_linux_packages.sh"

echo "=== Linux Build Completed Successfully! ==="
