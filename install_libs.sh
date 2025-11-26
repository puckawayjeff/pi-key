#!/bin/bash
# install_libs.sh - Install required CircuitPython libraries for pi-key
#
# This script downloads the CircuitPython 10.x library bundle and installs
# the required libraries (adafruit_hid and neopixel) to the device.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BUNDLE_VERSION="20241125"  # Update this periodically
BUNDLE_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/${BUNDLE_VERSION}/adafruit-circuitpython-bundle-10.x-mpy-${BUNDLE_VERSION}.zip"
BUNDLE_LATEST_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/latest/download/adafruit-circuitpython-bundle-10.x-mpy-${BUNDLE_VERSION}.zip"
DEVICE_PATH="/media/jeff/CIRCUITPY"
LIB_PATH="${DEVICE_PATH}/lib"
TMP_DIR="/tmp/circuitpy_libs_$$"

echo -e "${GREEN}pi-key Library Installer${NC}"
echo "================================"
echo

# Check if device is mounted
if [ ! -d "$DEVICE_PATH" ]; then
    echo -e "${RED}Error: CIRCUITPY drive not found at $DEVICE_PATH${NC}"
    echo
    echo "To enter edit mode:"
    echo "  1. Unplug the device"
    echo "  2. Hold the button down"
    echo "  3. Plug in the device while holding"
    echo "  4. Release after 1 second"
    echo "  5. Run this script again"
    exit 1
fi

# Create lib directory if it doesn't exist
if [ ! -d "$LIB_PATH" ]; then
    echo "Creating lib directory..."
    mkdir -p "$LIB_PATH"
fi

# Create temporary directory
echo "Creating temporary directory..."
mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

# Download bundle
echo
echo "Downloading CircuitPython 10.x library bundle..."
echo "URL: $BUNDLE_URL"
if ! wget -q "$BUNDLE_URL" 2>/dev/null; then
    echo -e "${YELLOW}Specific version not found, trying latest...${NC}"
    # Try to get the latest release
    LATEST_TAG=$(curl -s https://api.github.com/repos/adafruit/Adafruit_CircuitPython_Bundle/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
    if [ -z "$LATEST_TAG" ]; then
        echo -e "${RED}Error: Could not determine latest bundle version${NC}"
        echo "Please download manually from: https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases"
        rm -rf "$TMP_DIR"
        exit 1
    fi
    BUNDLE_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/${LATEST_TAG}/adafruit-circuitpython-bundle-10.x-mpy-${LATEST_TAG}.zip"
    echo "Downloading from: $BUNDLE_URL"
    if ! wget -q "$BUNDLE_URL"; then
        echo -e "${RED}Error: Failed to download bundle${NC}"
        rm -rf "$TMP_DIR"
        exit 1
    fi
fi

# Extract bundle
echo "Extracting bundle..."
if ! unzip -q adafruit-circuitpython-bundle-*.zip; then
    echo -e "${RED}Error: Failed to extract bundle${NC}"
    rm -rf "$TMP_DIR"
    exit 1
fi

# Find the extracted directory
BUNDLE_DIR=$(find . -maxdepth 1 -type d -name "adafruit-circuitpython-bundle-*" | head -n 1)
if [ -z "$BUNDLE_DIR" ]; then
    echo -e "${RED}Error: Could not find extracted bundle directory${NC}"
    rm -rf "$TMP_DIR"
    exit 1
fi

echo
echo "Installing libraries to $LIB_PATH..."

# Install adafruit_hid (directory)
if [ -d "${BUNDLE_DIR}/lib/adafruit_hid" ]; then
    echo "  ✓ Installing adafruit_hid..."
    rm -rf "${LIB_PATH}/adafruit_hid"  # Remove old version
    cp -r "${BUNDLE_DIR}/lib/adafruit_hid" "${LIB_PATH}/"
else
    echo -e "${RED}  ✗ Error: adafruit_hid not found in bundle${NC}"
    rm -rf "$TMP_DIR"
    exit 1
fi

# Install neopixel (single file)
if [ -f "${BUNDLE_DIR}/lib/neopixel.mpy" ]; then
    echo "  ✓ Installing neopixel.mpy..."
    cp "${BUNDLE_DIR}/lib/neopixel.mpy" "${LIB_PATH}/"
else
    echo -e "${RED}  ✗ Error: neopixel.mpy not found in bundle${NC}"
    rm -rf "$TMP_DIR"
    exit 1
fi

# Verify installations
echo
echo "Verifying installations..."
if [ -d "${LIB_PATH}/adafruit_hid" ]; then
    HID_SIZE=$(du -sh "${LIB_PATH}/adafruit_hid" | cut -f1)
    echo "  ✓ adafruit_hid installed (${HID_SIZE})"
else
    echo -e "${RED}  ✗ adafruit_hid verification failed${NC}"
fi

if [ -f "${LIB_PATH}/neopixel.mpy" ]; then
    NEOPIXEL_SIZE=$(stat -c%s "${LIB_PATH}/neopixel.mpy")
    if [ "$NEOPIXEL_SIZE" -gt 0 ]; then
        echo "  ✓ neopixel.mpy installed (${NEOPIXEL_SIZE} bytes)"
    else
        echo -e "${RED}  ✗ neopixel.mpy is empty (0 bytes)${NC}"
        rm -rf "$TMP_DIR"
        exit 1
    fi
else
    echo -e "${RED}  ✗ neopixel.mpy verification failed${NC}"
fi

# Cleanup
echo
echo "Cleaning up temporary files..."
rm -rf "$TMP_DIR"

echo
echo -e "${GREEN}✓ Libraries installed successfully!${NC}"
echo
echo "Next steps:"
echo "  1. Unplug the device (or press Ctrl+D in serial console)"
echo "  2. The device will reload and run with the new libraries"
echo "  3. If in stealth mode, unplug and replug without holding button"
echo
