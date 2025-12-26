#!/bin/bash
# Test Minimal App - Swap to minimal version, build, install

set -e

echo "🧪 Testing Minimal UDAC App"
echo "============================"
echo ""

# Backup original
echo "📦 Backing up original __main__.py..."
cp udac_portal/__main__.py udac_portal/__main__.py.backup

# Swap to minimal
echo "🔄 Switching to minimal test version..."
cp udac_portal/__main___test.py udac_portal/__main__.py

echo "🏗️  Building minimal APK..."
echo ""

# Clean and build
rm -rf build/
briefcase build android
briefcase package android

echo ""
echo "📱 Installing minimal test app..."
adb install -r build/udac_portal/android/gradle/app/build/outputs/apk/release/app-release.apk

echo ""
echo "✅ Minimal test app installed!"
echo ""
echo "Now tap the app icon and tell me what happens:"
echo "  - Does it show a window with 'UDAC Portal - Minimal Test'?"
echo "  - Does it crash the same way?"
echo "  - Does it show an error?"
echo ""
echo "After testing, run ./restore_main.sh to restore the full app"
