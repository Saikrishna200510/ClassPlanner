#!/usr/bin/env bash
# ==============================================================================
# ClassPlanner - macOS Standalone DMG Installer Creation Script
# Packages dist/ClassPlanner.app into dist/ClassPlanner-v1.0.0-macOS.dmg
# with drag-and-drop /Applications shortcut.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

VERSION="${RELEASE_VERSION:-1.0.1}"
DMG_NAME="ClassPlanner-v${VERSION}-macOS.dmg"
APP_NAME="ClassPlanner.app"
DIST_DIR="${ROOT_DIR}/dist"
STAGING_DIR="${DIST_DIR}/dmg_staging"

echo "=== Creating macOS DMG Installer for ClassPlanner v${VERSION} ==="
cd "${ROOT_DIR}"

if [ ! -d "${DIST_DIR}/${APP_NAME}" ]; then
    echo "ClassPlanner.app not found in ${DIST_DIR}. Building with PyInstaller first..."
    pyinstaller --clean build_scripts/ClassPlanner.spec
fi

# Clean up previous staging and DMG
rm -rf "${STAGING_DIR}" "${DIST_DIR}/${DMG_NAME}"
mkdir -p "${STAGING_DIR}"

echo "Preparing DMG contents..."
cp -R "${DIST_DIR}/${APP_NAME}" "${STAGING_DIR}/"

# Ad-hoc codesign app bundle
echo "Applying ad-hoc code signature to ${APP_NAME}..."
codesign --force --deep --sign - "${STAGING_DIR}/${APP_NAME}" || true

# Create Applications shortcut
echo "Creating /Applications symlink..."
ln -s /Applications "${STAGING_DIR}/Applications"

# Include README in DMG
if [ -f "${ROOT_DIR}/README.md" ]; then
    cp "${ROOT_DIR}/README.md" "${STAGING_DIR}/"
fi

# Build compressed DMG image
echo "Building compressed disk image: ${DIST_DIR}/${DMG_NAME}..."
hdiutil create \
    -volname "ClassPlanner" \
    -srcfolder "${STAGING_DIR}" \
    -ov \
    -format UDZO \
    "${DIST_DIR}/${DMG_NAME}"

# Clean up staging directory
rm -rf "${STAGING_DIR}"

echo "=== macOS DMG Installer Successfully Created! ==="
echo "Installer location: ${DIST_DIR}/${DMG_NAME}"
hdiutil verify "${DIST_DIR}/${DMG_NAME}"

