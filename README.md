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

## Stealth Mode

The device operates in **stealth mode** by default:
- No USB drive appears
- No serial console port
- Appears as "Dell KB216 Wired Keyboard" to the host
- Code runs automatically on power-up

### Entering Edit Mode

To access the CIRCUITPY drive for editing:

1. **Unplug** the device
2. **Hold** the button (GP29) down
3. **Plug in** the device while holding the button
4. **Release** the button after 1 second
5. The CIRCUITPY drive will appear normally

This is controlled by `boot.py` which checks the button state at boot time.

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

**First time or when in edit mode:**
```bash
./deploy.sh  # Copies code.py, boot.py, and macro.txt to device
```

**Note**: After first deployment with `boot.py`, you must use edit mode (hold button during boot) to access the drive for updates.

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
boot.py          # Boot-time config (enables stealth mode)
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

## Stealth Mode Details

The `boot.py` file configures USB behavior at boot time:

- **Normal operation** (button not pressed): USB drive and serial console disabled, device appears as generic keyboard
- **Edit mode** (button pressed during boot): Full CIRCUITPY drive access enabled

This allows the device to operate covertly while still being field-updatable without requiring BOOTSEL mode.
