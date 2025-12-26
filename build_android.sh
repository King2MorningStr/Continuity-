#!/bin/bash
# Build Android APK with Buildozer (Kivy)
# ========================================

set -e

echo "🚀 Building UDAC Portal APK with Buildozer..."

# Check dependencies
if ! command -v buildozer &> /dev/null; then
    echo "❌ Buildozer not found!"
    echo "Install with: pip install buildozer"
    echo "Also install system dependencies:"
    echo "  Ubuntu/Debian: sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev"
    exit 1
fi

# Clean previous builds if requested
if [ "$1" == "clean" ]; then
    echo "🧹 Cleaning previous builds..."
    buildozer android clean
fi

# Build debug APK
echo "📦 Building debug APK..."
buildozer android debug

# Find the APK
APK_PATH=$(find bin -name "*.apk" -type f | head -1)

if [ -f "$APK_PATH" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📱 APK location: $APK_PATH"
    echo ""
    echo "To install on device:"
    echo "  adb install -r \"$APK_PATH\""
    echo ""
    echo "To view logs:"
    echo "  adb logcat | grep python"
else
    echo "❌ Build failed - APK not found"
    exit 1
fi
