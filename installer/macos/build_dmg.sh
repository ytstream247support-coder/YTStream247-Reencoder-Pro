#!/bin/bash
# macOS Universal DMG Build Script for YT Stream 24/7 - Reencoder
# Builds one app bundle and one DMG that works on Intel + Apple Silicon.

set -euo pipefail

APP_NAME="YT Stream 247 — Reencoder"
APP_BUNDLE="${APP_NAME}.app"
BUILD_DIR="dist"
DMG_DIR="dmg_build"
DMG_NAME="${DMG_NAME:-YT-FFmpeg-Stream-Reencoder-macOS}"
PYI_TARGET_ARCH="${PYI_TARGET_ARCH:-universal2}"
FFMPEG_ZIP_DIR="${FFMPEG_ZIP_DIR:-mac-ffmpeg}"

cleanup() {
    if [ -n "${STAGE_DIR:-}" ] && [ -d "${STAGE_DIR}" ]; then
        rm -rf "${STAGE_DIR}"
    fi
}
trap cleanup EXIT

require_file() {
    local file_path="$1"
    if [ ! -f "${file_path}" ]; then
        echo "Error: Missing required file: ${file_path}"
        exit 1
    fi
}

check_binary_arch() {
    local binary_path="$1"
    local target_arch="$2"
    local file_out

    require_file "${binary_path}"
    file_out="$(file "${binary_path}")"

    if [ "${target_arch}" = "arm64" ]; then
        if [[ "${file_out}" != *"arm64"* && "${file_out}" != *"universal"* ]]; then
            echo "Error: ${binary_path} is not arm64/universal."
            echo "Detected: ${file_out}"
            exit 1
        fi
    else
        if [[ "${file_out}" != *"x86_64"* && "${file_out}" != *"universal"* ]]; then
            echo "Error: ${binary_path} is not x86_64/universal."
            echo "Detected: ${file_out}"
            exit 1
        fi
    fi
}

generate_icns_from_png() {
    local source_png="$1"
    local output_icns="$2"

    if [ ! -f "${source_png}" ]; then
        echo "Warning: No PNG source at ${source_png}, skipping icon generation."
        return 1
    fi

    local iconset_dir="${STAGE_DIR}/icon.iconset"
    mkdir -p "${iconset_dir}"

    sips -z 16 16     "${source_png}" --out "${iconset_dir}/icon_16x16.png"       >/dev/null
    sips -z 32 32     "${source_png}" --out "${iconset_dir}/icon_16x16@2x.png"    >/dev/null
    sips -z 32 32     "${source_png}" --out "${iconset_dir}/icon_32x32.png"       >/dev/null
    sips -z 64 64     "${source_png}" --out "${iconset_dir}/icon_32x32@2x.png"    >/dev/null
    sips -z 128 128   "${source_png}" --out "${iconset_dir}/icon_128x128.png"     >/dev/null
    sips -z 256 256   "${source_png}" --out "${iconset_dir}/icon_128x128@2x.png"  >/dev/null
    sips -z 256 256   "${source_png}" --out "${iconset_dir}/icon_256x256.png"     >/dev/null
    sips -z 512 512   "${source_png}" --out "${iconset_dir}/icon_256x256@2x.png"  >/dev/null
    sips -z 512 512   "${source_png}" --out "${iconset_dir}/icon_512x512.png"     >/dev/null
    sips -z 1024 1024 "${source_png}" --out "${iconset_dir}/icon_512x512@2x.png"  >/dev/null

    iconutil -c icns "${iconset_dir}" -o "${output_icns}"
    rm -rf "${iconset_dir}"
    echo "Generated icon: ${output_icns}"
}

stage_dual_ffmpeg_binaries() {
    local destination_dir="$1"

    mkdir -p "${destination_dir}"
    rm -f "${destination_dir}/ffmpeg-arm64" "${destination_dir}/ffprobe-arm64" \
          "${destination_dir}/ffmpeg-x86_64" "${destination_dir}/ffprobe-x86_64"

    if [ -f "${FFMPEG_ZIP_DIR}/ffmpeg-mac-arm64.zip" ] && [ -f "${FFMPEG_ZIP_DIR}/ffprobe-mac-arm64.zip" ] && \
       [ -f "${FFMPEG_ZIP_DIR}/ffmpeg-mac-intel.zip" ] && [ -f "${FFMPEG_ZIP_DIR}/ffprobe-mac-intel.zip" ]; then
        echo "Staging dual FFmpeg binaries from ${FFMPEG_ZIP_DIR}..."
        unzip -oq "${FFMPEG_ZIP_DIR}/ffmpeg-mac-arm64.zip" -d "${STAGE_DIR}"
        mv "${STAGE_DIR}/ffmpeg" "${destination_dir}/ffmpeg-arm64"

        unzip -oq "${FFMPEG_ZIP_DIR}/ffprobe-mac-arm64.zip" -d "${STAGE_DIR}"
        mv "${STAGE_DIR}/ffprobe" "${destination_dir}/ffprobe-arm64"

        unzip -oq "${FFMPEG_ZIP_DIR}/ffmpeg-mac-intel.zip" -d "${STAGE_DIR}"
        mv "${STAGE_DIR}/ffmpeg" "${destination_dir}/ffmpeg-x86_64"

        unzip -oq "${FFMPEG_ZIP_DIR}/ffprobe-mac-intel.zip" -d "${STAGE_DIR}"
        mv "${STAGE_DIR}/ffprobe" "${destination_dir}/ffprobe-x86_64"
    elif [ -f "ffmpeg-apps/ffmpeg-arm64" ] && [ -f "ffmpeg-apps/ffprobe-arm64" ] && \
         [ -f "ffmpeg-apps/ffmpeg-x86_64" ] && [ -f "ffmpeg-apps/ffprobe-x86_64" ]; then
        echo "Staging dual FFmpeg binaries from local ffmpeg-apps/..."
        cp "ffmpeg-apps/ffmpeg-arm64" "${destination_dir}/ffmpeg-arm64"
        cp "ffmpeg-apps/ffprobe-arm64" "${destination_dir}/ffprobe-arm64"
        cp "ffmpeg-apps/ffmpeg-x86_64" "${destination_dir}/ffmpeg-x86_64"
        cp "ffmpeg-apps/ffprobe-x86_64" "${destination_dir}/ffprobe-x86_64"
    else
        echo "Error: Could not find macOS FFmpeg inputs."
        echo "Expected either:"
        echo "  - ${FFMPEG_ZIP_DIR}/ffmpeg-mac-arm64.zip, ffprobe-mac-arm64.zip, ffmpeg-mac-intel.zip, ffprobe-mac-intel.zip"
        echo "  - or pre-extracted binaries in ffmpeg-apps/ with *-arm64 and *-x86_64 names"
        exit 1
    fi

    check_binary_arch "${destination_dir}/ffmpeg-arm64" "arm64"
    check_binary_arch "${destination_dir}/ffprobe-arm64" "arm64"
    check_binary_arch "${destination_dir}/ffmpeg-x86_64" "x86_64"
    check_binary_arch "${destination_dir}/ffprobe-x86_64" "x86_64"
    chmod +x "${destination_dir}/ffmpeg-arm64" "${destination_dir}/ffprobe-arm64" \
             "${destination_dir}/ffmpeg-x86_64" "${destination_dir}/ffprobe-x86_64"
}

echo "Building macOS universal application..."

STAGE_DIR="$(mktemp -d -t yts247-macos-stage.XXXXXX)"

if [ "${SKIP_PYINSTALLER:-0}" != "1" ]; then
    pyinstaller pyinstaller.spec --clean --target-arch "${PYI_TARGET_ARCH}"
fi

if [ ! -d "${BUILD_DIR}/${APP_BUNDLE}" ]; then
    echo "Creating .app bundle structure..."
    mkdir -p "${BUILD_DIR}/${APP_BUNDLE}/Contents/MacOS"
    mkdir -p "${BUILD_DIR}/${APP_BUNDLE}/Contents/Resources"

    if [ -f "${BUILD_DIR}/YTStream247Reencoder" ]; then
        mv "${BUILD_DIR}/YTStream247Reencoder" "${BUILD_DIR}/${APP_BUNDLE}/Contents/MacOS/"
    fi

    cat > "${BUILD_DIR}/${APP_BUNDLE}/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>YTStream247Reencoder</string>
    <key>CFBundleIdentifier</key>
    <string>com.HhhHSoft.YTStream247Reencoder</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>1.0.2</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.2</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
</dict>
</plist>
EOF

    if [ ! -f "icon.icns" ] && [ -f "assets/icons/icon.png" ]; then
        echo "Generating icon.icns from assets/icons/icon.png..."
        generate_icns_from_png "assets/icons/icon.png" "icon.icns" || true
    fi

    if [ -f "icon.icns" ]; then
        cp "icon.icns" "${BUILD_DIR}/${APP_BUNDLE}/Contents/Resources/"
    fi
fi

if [ ! -f "${BUILD_DIR}/${APP_BUNDLE}/Contents/MacOS/YTStream247Reencoder" ]; then
    echo "Error: App executable not found at ${BUILD_DIR}/${APP_BUNDLE}/Contents/MacOS/YTStream247Reencoder"
    echo "Make sure PyInstaller build succeeded before packaging."
    exit 1
fi

APP_FFMPEG_DIR="${BUILD_DIR}/${APP_BUNDLE}/Contents/MacOS/ffmpeg-apps"
stage_dual_ffmpeg_binaries "${APP_FFMPEG_DIR}"

if [ "${SKIP_CODESIGN:-0}" != "1" ]; then
    echo "Applying ad-hoc code signature (reduces Gatekeeper friction on unsigned builds)..."
    codesign --force --deep --sign - "${APP_FFMPEG_DIR}/ffmpeg-arm64"   2>/dev/null || true
    codesign --force --deep --sign - "${APP_FFMPEG_DIR}/ffprobe-arm64"  2>/dev/null || true
    codesign --force --deep --sign - "${APP_FFMPEG_DIR}/ffmpeg-x86_64"  2>/dev/null || true
    codesign --force --deep --sign - "${APP_FFMPEG_DIR}/ffprobe-x86_64" 2>/dev/null || true
    codesign --force --deep --sign - "${BUILD_DIR}/${APP_BUNDLE}"       2>/dev/null || true
fi

echo "Creating DMG..."
rm -rf "${DMG_DIR}"
rm -f "${DMG_NAME}.dmg"

mkdir -p "${DMG_DIR}"
cp -R "${BUILD_DIR}/${APP_BUNDLE}" "${DMG_DIR}/"
ln -s /Applications "${DMG_DIR}/Applications"

if [ -f "installer/macos/FIRST-RUN-MAC.txt" ]; then
    cp "installer/macos/FIRST-RUN-MAC.txt" "${DMG_DIR}/FIRST-RUN (read me).txt"
fi

hdiutil create -volname "${APP_NAME}" -srcfolder "${DMG_DIR}" -ov -format UDZO "${DMG_NAME}.dmg"

rm -rf "${DMG_DIR}"
echo "DMG created: ${DMG_NAME}.dmg"

