# pi-key

USB HID keyboard emulator for Waveshare RP2040-One using CircuitPython. Types keyboard sequences and provides keep-alive functionality via a single button.

## Features

- **Double-Press**: Types customizable macro string (from `macro.txt`)
- **Long-Press** (1+ second): Activates keep-alive mode  
- **Keep-Alive Mode**: Alternates Space/Left-Arrow every 600ms to prevent screen lock
- **Visual Feedback**: RGB LED indicates actions (purple=typing, amber=keep-alive, red=exit)

## Hardware

- **Board**: Waveshare RP2040-One
- **Button**: Momentary pushbutton between GP29 and GND (internal pull-up)
- **LED**: Onboard WS2812 RGB LED on GP16 (GRB color order)

## Quick Start

### 1. Install CircuitPython

Download CircuitPython 9.x for Waveshare RP2040-One from https://circuitpython.org/downloads

### 2. Install Required Libraries

Device needs `adafruit_hid` and `neopixel` in `/lib/` folder:

```bash
# Libraries already configured if using provided bundle
ls /media/jeff/CIRCUITPY/lib/
# Should show: adafruit_hid/ and neopixel.mpy
```

### 3. Deploy Code

```bash
./deploy.sh  # Copies code.py and macro.txt to device
```

### 4. Customize Macro

Edit `macro.txt` to change the string that gets typed on double-press, then redeploy.

### 5. Monitor (Optional)

```bash
./monitor.sh  # View serial console output
# Press Ctrl+C to exit
```

## Usage

- **Double-tap button**: Purple flash → Types macro string
- **Hold button 1+ seconds**: Amber breathing → Keep-alive mode active
- **Press during keep-alive**: Two red flashes → Exits keep-alive mode

## Development

1. Edit `code.py` or `macro.txt` 
2. Run `./deploy.sh`
3. Device auto-reloads (~2 seconds)
4. Use `./monitor.sh` to see debug output

## Project Structure

```
code.py          # Main firmware (CircuitPython)
macro.txt        # String to type on double-press
deploy.sh        # Deployment helper
monitor.sh       # Serial console monitor
archive/         # Historical Arduino experiments
```

## Dependencies

**CircuitPython**: 9.x or 10.x  
**Libraries**:
- `adafruit_hid` - USB HID keyboard emulation
- `neopixel` - WS2812 RGB LED control

## Hardware Notes

- **GP16**: WS2812 LED (GRB color order, not RGB!)
- **GP29**: Button input with internal pull-up (active-low)
- Button wiring: GP29 → momentary switch → GND
