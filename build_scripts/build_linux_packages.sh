#!/usr/bin/env bash
# ==============================================================================
# ClassPlanner - Linux Packaging Script (.deb and .AppImage)
# Builds classplanner_1.0.0_amd64.deb and ClassPlanner-v1.0.0-x86_64.AppImage
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

VERSION="1.0.0"
DIST_DIR="${ROOT_DIR}/dist"
BINARY="${DIST_DIR}/ClassPlanner"

echo "=== Building Linux Packages for ClassPlanner v${VERSION} ==="
cd "${ROOT_DIR}"

if [ ! -f "${BINARY}" ]; then
    echo "Linux binary not found in ${DIST_DIR}. Building with PyInstaller first..."
    pyinstaller --clean build_scripts/ClassPlanner.spec
fi

# ==============================================================================
# 1. Build Debian (.deb) Package
# ==============================================================================
echo "--- 1. Building Debian (.deb) Package ---"
DEB_DIR="${DIST_DIR}/deb_staging"
rm -rf "${DEB_DIR}"

mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/opt/classplanner"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/scalable/apps"

# Control file
cat <<EOF > "${DEB_DIR}/DEBIAN/control"
Package: classplanner
Version: ${VERSION}
Section: education
Priority: optional
Architecture: amd64
Maintainer: SL IT Solutions <support@slit.edu>
Installed-Size: 150000
Depends: libc6 (>= 2.31), libgl1, libxkbcommon-x11-0
Homepage: https://github.com/Saikrishna200510/ClassPlanner
Description: ClassPlanner - Automated Multi-College Timetable Management System
 ClassPlanner is a standalone desktop application for automated timetable
 generation, conflict resolution, faculty workload balancing, and multi-college
 institutional administration.
EOF

# Post-install script
cat <<'EOF' > "${DEB_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q /usr/share/applications || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "${DEB_DIR}/DEBIAN/postinst"

# Post-remove script (for clean uninstallation)
cat <<'EOF' > "${DEB_DIR}/DEBIAN/postrm"
#!/bin/sh
set -e
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q /usr/share/applications || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "${DEB_DIR}/DEBIAN/postrm"

# Copy binary and resources
cp "${BINARY}" "${DEB_DIR}/opt/classplanner/ClassPlanner"
chmod 755 "${DEB_DIR}/opt/classplanner/ClassPlanner"

# Copy icons
if [ -f "${ROOT_DIR}/classplanner/resources/icon.png" ]; then
    cp "${ROOT_DIR}/classplanner/resources/icon.png" "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/classplanner.png"
    cp "${ROOT_DIR}/classplanner/resources/icon.png" "${DEB_DIR}/usr/share/icons/hicolor/scalable/apps/classplanner.png"
fi

# Launcher script
cat <<'EOF' > "${DEB_DIR}/usr/bin/classplanner"
#!/bin/sh
exec /opt/classplanner/ClassPlanner "$@"
EOF
chmod 755 "${DEB_DIR}/usr/bin/classplanner"

# Desktop entry
cat <<EOF > "${DEB_DIR}/usr/share/applications/classplanner.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=ClassPlanner
GenericName=Timetable Generator
Comment=Automated Multi-College Timetable Management System
Exec=/usr/bin/classplanner
Icon=classplanner
Terminal=false
Categories=Education;Office;
Keywords=timetable;schedule;college;planner;faculty;
StartupWMClass=ClassPlanner
EOF

# Build DEB package
DEB_PACKAGE="${DIST_DIR}/classplanner_${VERSION}_amd64.deb"
dpkg-deb --build --root-owner-group "${DEB_DIR}" "${DEB_PACKAGE}"
rm -rf "${DEB_DIR}"
echo "Debian package created: ${DEB_PACKAGE}"

# ==============================================================================
# 2. Build Universal AppImage (.AppImage)
# ==============================================================================
echo "--- 2. Building AppImage Package ---"
APPDIR="${DIST_DIR}/AppDir"
rm -rf "${APPDIR}"

mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

cp "${BINARY}" "${APPDIR}/usr/bin/ClassPlanner"
chmod 755 "${APPDIR}/usr/bin/ClassPlanner"

if [ -f "${ROOT_DIR}/classplanner/resources/icon.png" ]; then
    cp "${ROOT_DIR}/classplanner/resources/icon.png" "${APPDIR}/classplanner.png"
    cp "${ROOT_DIR}/classplanner/resources/icon.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/classplanner.png"
fi

cat <<EOF > "${APPDIR}/classplanner.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=ClassPlanner
GenericName=Timetable Generator
Comment=Automated Multi-College Timetable Management System
Exec=ClassPlanner
Icon=classplanner
Terminal=false
Categories=Education;Office;
Keywords=timetable;schedule;college;planner;faculty;
StartupWMClass=ClassPlanner
EOF

cat <<'EOF' > "${APPDIR}/AppRun"
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/ClassPlanner" "$@"
EOF
chmod 755 "${APPDIR}/AppRun"

# Download and run appimagetool if not available
APPIMAGE_OUTPUT="${DIST_DIR}/ClassPlanner-v${VERSION}-x86_64.AppImage"
if ! command -v appimagetool &> /dev/null; then
    echo "Downloading appimagetool..."
    curl -sL "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" -o /tmp/appimagetool
    chmod +x /tmp/appimagetool
    # Extract appimagetool if running in container without FUSE
    (cd /tmp && ./appimagetool --appimage-extract > /dev/null 2>&1) || true
    if [ -d "/tmp/squashfs-root" ]; then
        APPIMAGETOOL="/tmp/squashfs-root/AppRun"
    else
        APPIMAGETOOL="/tmp/appimagetool"
    fi
else
    APPIMAGETOOL="appimagetool"
fi

echo "Running appimagetool..."
ARCH=x86_64 ${APPIMAGETOOL} --no-appstream "${APPDIR}" "${APPIMAGE_OUTPUT}" || ARCH=x86_64 ${APPIMAGETOOL} "${APPDIR}" "${APPIMAGE_OUTPUT}"
chmod +x "${APPIMAGE_OUTPUT}"
rm -rf "${APPDIR}"

echo "=== Linux Packages Successfully Created! ==="
echo "1. Debian Package: ${DEB_PACKAGE}"
echo "2. Universal AppImage: ${APPIMAGE_OUTPUT}"

