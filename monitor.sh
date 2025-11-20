#!/bin/bash
# Monitor the CircuitPython serial console

SERIAL_PORT="/dev/ttyACM0"

if [ ! -e "$SERIAL_PORT" ]; then
    echo "❌ Error: Serial port $SERIAL_PORT not found"
    echo "   Make sure the Waveshare RP2040-One is connected."
    exit 1
fi

echo "📡 Connecting to CircuitPython serial console on $SERIAL_PORT"
echo "   Press Ctrl+C to exit"
echo ""

# Check if screen is installed
if command -v screen &> /dev/null; then
    screen $SERIAL_PORT 115200
elif command -v minicom &> /dev/null; then
    minicom -D $SERIAL_PORT -b 115200
else
    echo "⚠️  Neither 'screen' nor 'minicom' found."
    echo "   Install with: sudo apt install screen"
    exit 1
fi
