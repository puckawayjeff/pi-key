#!/bin/bash
# Deploy code.py to the RP2040-One CircuitPython device

MOUNT_PATH="/media/jeff/CIRCUITPY"
FILES=("code.py" "boot.py" "macro.txt" "USAGE.txt" "README.md")

if [ ! -d "$MOUNT_PATH" ]; then
    echo "❌ Error: CIRCUITPY device not found at $MOUNT_PATH"
    echo "   Make sure device is in edit mode (hold button during boot)."
    exit 1
fi

echo "📋 Deploying files to $MOUNT_PATH..."
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "⚠️  Warning: $file not found, skipping"
        continue
    fi
    echo "   Copying $file..."
    cp "$file" "$MOUNT_PATH/"
done

sync
echo "✅ Deployment complete! Device will auto-reload."
echo "💡 Note: After reboot, device will be in stealth mode (no drive/serial)."
echo "💡 To edit again, unplug, hold button, plug in, release after 1s."
