#!/bin/bash
# UDAC Portal Crash Log Collector
# Run this script while the app crashes to capture the error

echo "🔍 UDAC Portal Crash Log Collector"
echo "==================================="
echo ""
echo "Instructions:"
echo "1. Keep this terminal open"
echo "2. In another terminal: adb logcat -c (clear old logs)"
echo "3. Launch the app on your device"
echo "4. Wait for crash"
echo "5. Check udac_crash.log in this directory"
echo ""
echo "Starting log capture..."
echo ""

# Clear logcat
adb logcat -c

# Capture logs with filters for Python, UDAC, and crashes
adb logcat -v time \
    python:V \
    pythonhost:V \
    Python:V \
    AndroidRuntime:E \
    ActivityManager:W \
    *:E \
    | grep -i -E "(udac|python|exception|error|crash|fatal)" \
    | tee udac_crash.log

echo ""
echo "✅ Log saved to: udac_crash.log"
echo "Please send this file for analysis"
