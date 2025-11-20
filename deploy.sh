#!/bin/bash
# Deploy code.py to the RP2040-One CircuitPython device

MOUNT_PATH="/media/jeff/CIRCUITPY"
SOURCE_FILE="code.py"

if [ ! -d "$MOUNT_PATH" ]; then
    echo "❌ Error: CIRCUITPY device not found at $MOUNT_PATH"
    echo "   Make sure the Waveshare RP2040-One is connected."
    exit 1
fi

if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ Error: $SOURCE_FILE not found in current directory"
    exit 1
fi

echo "📋 Copying $SOURCE_FILE to $MOUNT_PATH..."
cp "$SOURCE_FILE" "$MOUNT_PATH/"

if [ $? -eq 0 ]; then
    sync
    echo "✅ Deployment complete! Device will auto-reload."
    echo "💡 Run './monitor.sh' to see serial output."
else
    echo "❌ Failed to copy file"
    exit 1
fi
