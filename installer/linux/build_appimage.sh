#!/bin/bash
# Linux AppImage Build Script for YT Stream 24/7 — Reencoder
# This script builds an AppImage for portable Linux distribution

set -e

APP_NAME="YTStream247Reencoder"
APPIMAGE_NAME="${APP_NAME}.AppImage"
BUILD_DIR="dist"
APPIMAGE_DIR="appimage_build"
STAGED_FFMPEG_DIR=""

echo "Building Linux application..."

# Build with PyInstaller
pyinstaller pyinstaller.spec --clean

echo "Creating AppImage structure..."

# Clean up previous build
rm -rf "${APPIMAGE_DIR}"
rm -f "${APPIMAGE_NAME}"

# Create AppDir structure
mkdir -p "${APPIMAGE_DIR}/AppDir/usr/bin"
mkdir -p "${APPIMAGE_DIR}/AppDir/usr/share/applications"
mkdir -p "${APPIMAGE_DIR}/AppDir/usr/share/icons/hicolor/256x256/apps"

# Copy executable
if [ -f "${BUILD_DIR}/${APP_NAME}" ]; then
    cp "${BUILD_DIR}/${APP_NAME}" "${APPIMAGE_DIR}/AppDir/usr/bin/"
    chmod +x "${APPIMAGE_DIR}/AppDir/usr/bin/${APP_NAME}"
fi

# Copy FFmpeg sidecar binaries (required for official installer builds)
if [ -d "${BUILD_DIR}/ffmpeg-apps" ]; then
    STAGED_FFMPEG_DIR="${BUILD_DIR}/ffmpeg-apps"
elif [ -d "ffmpeg-apps" ]; then
    STAGED_FFMPEG_DIR="ffmpeg-apps"
else
    echo "Error: FFmpeg binaries not found."
    echo "Expected either ${BUILD_DIR}/ffmpeg-apps or ./ffmpeg-apps"
    exit 1
fi

mkdir -p "${APPIMAGE_DIR}/AppDir/usr/bin/ffmpeg-apps"
cp -r "${STAGED_FFMPEG_DIR}/." "${APPIMAGE_DIR}/AppDir/usr/bin/ffmpeg-apps/"
chmod +x "${APPIMAGE_DIR}/AppDir/usr/bin/ffmpeg-apps/"* || true

# Copy assets
if [ -d "${BUILD_DIR}/assets" ]; then
    mkdir -p "${APPIMAGE_DIR}/AppDir/usr/share/${APP_NAME}"
    cp -r "${BUILD_DIR}/assets" "${APPIMAGE_DIR}/AppDir/usr/share/${APP_NAME}/"
fi

# Create desktop entry
cat > "${APPIMAGE_DIR}/AppDir/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Name=YT Stream 24/7 — Reencoder
Comment=Re-encode videos for YouTube Live streaming
Exec=${APP_NAME}
Icon=${APP_NAME}
Type=Application
Categories=AudioVideo;Video;
EOF

# Copy icon if exists
if [ -f "assets/icons/icon.png" ]; then
    cp "assets/icons/icon.png" "${APPIMAGE_DIR}/AppDir/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
elif [ -f "icon.png" ]; then
    cp "icon.png" "${APPIMAGE_DIR}/AppDir/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
fi

# Create AppRun script
cat > "${APPIMAGE_DIR}/AppDir/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/YTStream247Reencoder" "$@"
EOF
chmod +x "${APPIMAGE_DIR}/AppDir/AppRun"

# Download and use appimagetool if not available
if ! command -v appimagetool &> /dev/null; then
    echo "appimagetool not found. Downloading..."
    APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    wget -q "${APPIMAGETOOL_URL}" -O appimagetool.AppImage
    chmod +x appimagetool.AppImage
    APPIMAGETOOL="./appimagetool.AppImage"
else
    APPIMAGETOOL="appimagetool"
fi

# Build AppImage
echo "Building AppImage..."
${APPIMAGETOOL} "${APPIMAGE_DIR}/AppDir" "${APPIMAGE_NAME}"

# Clean up
rm -rf "${APPIMAGE_DIR}"
if [ -f "appimagetool.AppImage" ]; then
    rm -f appimagetool.AppImage
fi

echo "AppImage created: ${APPIMAGE_NAME}"

