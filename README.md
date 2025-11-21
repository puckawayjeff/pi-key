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

## Macro Syntax

The `macro.txt` file supports both plain text and special keyboard commands using `{KEY}` syntax:

**Plain Text:**
```
Hello World
```

**Special Keys:**
```
Username{TAB}Password{ENTER}
```

**Key Combinations:**
```
{CTRL+C}          Copy
{CTRL+V}          Paste
{CTRL+SHIFT+T}    Reopen browser tab
{GUI+D}           Show desktop
```

**Available Special Keys:**
- Navigation: `{UP}`, `{DOWN}`, `{LEFT}`, `{RIGHT}`, `{HOME}`, `{END}`, `{PAGEUP}`, `{PAGEDOWN}`
- Editing: `{ENTER}`, `{TAB}`, `{SPACE}`, `{BACKSPACE}`, `{DELETE}`, `{ESC}`

**Available Modifiers:**
- `{CTRL+...}` - Control key
- `{SHIFT+...}` - Shift key
- `{ALT+...}` - Alt key
- `{GUI+...}` or `{WIN+...}` or `{CMD+...}` - Windows/Super/Command key

You can combine multiple modifiers: `{CTRL+SHIFT+KEY}`

**Literal Braces:**
To type literal `{` or `}` characters, use double braces:
```
{{     Types a single {
}}     Types a single }
```
Example: `Python {{dict}}` types `Python {dict}`

## Quick Start (Users)

If the device is already programmed, you can customize the macro without any programming:

### Edit the Macro

1. **Unplug** the device
2. **Hold** the button down
3. **Plug in** the device while holding
4. **Release** after 1 second
5. The `CIRCUITPY` drive will appear
6. **Edit** `macro.txt` with any text editor
7. **Save** the file
8. **Unplug** the device (or press Ctrl+D in serial console to reload)

The device is now ready with your custom macro!

### Usage

- **Double-tap button**: Purple flash → Types your macro
- **Hold button 1+ seconds**: Amber breathing → Keep-alive mode active
- **Press during keep-alive**: Two red flashes → Exits keep-alive mode

## Developer Setup

For initial setup or code development:

### 1. Install CircuitPython

Download CircuitPython 9.x for Waveshare RP2040-One from https://circuitpython.org/downloads

### 2. Install Required Libraries

Device needs `adafruit_hid` and `neopixel` in `/lib/` folder:

```bash
# Download CircuitPython 9.x bundle
# Extract and copy these to /media/jeff/CIRCUITPY/lib/:
# - adafruit_hid/ (directory)
# - neopixel.mpy (file)
```

### 3. Deploy Code

**First time or when in edit mode:**
```bash
./deploy.sh  # Copies code.py, boot.py, and macro.txt to device
```

**Note**: After first deployment with `boot.py`, you must use edit mode (hold button during boot) to access the drive for updates.

### 4. Monitor Serial Console (Optional)

```bash
./monitor.sh  # View serial console output (only in edit mode)
# Press Ctrl+C to exit
```

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
