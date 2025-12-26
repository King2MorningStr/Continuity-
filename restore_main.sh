#!/bin/bash
# Restore original __main__.py

set -e

echo "🔄 Restoring original __main__.py..."

if [ -f "udac_portal/__main__.py.backup" ]; then
    cp udac_portal/__main__.py.backup udac_portal/__main__.py
    rm udac_portal/__main__.py.backup
    echo "✅ Original __main__.py restored!"
else
    echo "❌ No backup found"
    exit 1
fi
