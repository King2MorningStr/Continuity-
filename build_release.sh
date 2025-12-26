#!/bin/bash
# Build Release APK for Play Store
# =================================

set -e

echo "🚀 Building UDAC Portal Release APK..."

# Check for keystore
KEYSTORE="$HOME/.android/udacportal.keystore"

if [ ! -f "$KEYSTORE" ]; then
    echo "⚠️  Keystore not found at $KEYSTORE"
    echo ""
    echo "Creating new keystore..."
    mkdir -p "$HOME/.android"
    keytool -genkey -v -keystore "$KEYSTORE" \
        -alias udacportal \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass android \
        -keypass android \
        -dname "CN=UDAC Portal, OU=Development, O=UDAC, L=Unknown, ST=Unknown, C=US"
    echo "✅ Keystore created!"
fi

# Build release APK
echo "📦 Building release APK..."
buildozer android release

# Find the APK
APK_PATH=$(find bin -name "*-release*.apk" -type f | head -1)

if [ -f "$APK_PATH" ]; then
    echo ""
    echo "✅ Release build successful!"
    echo "📱 APK location: $APK_PATH"
    echo ""
    echo "Next steps for Play Store:"
    echo "1. Test the release APK on a device"
    echo "2. Create an app listing in Google Play Console"
    echo "3. Upload this APK or generate an AAB with:"
    echo "   buildozer android aab"
    echo "4. Complete store listing and submit for review"
    echo ""
    echo "Note: Update keystore passwords in buildozer.spec for automated signing"
else
    echo "❌ Build failed - APK not found"
    exit 1
fi
