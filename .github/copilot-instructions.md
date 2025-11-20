# Copilot Instructions for pi-key

## Project Overview
USB HID keyboard emulator for Waveshare RP2040-One using CircuitPython. Single-button interface with double-press macro typing and long-press keep-alive mode.

## Architecture
- **Platform**: CircuitPython 9.x on Waveshare RP2040-One
- **Main file**: `code.py` (deployed to CIRCUITPY USB drive at `/media/jeff/CIRCUITPY`)
- **Hardware**: 
  - Button: GP29 with internal pull-up (active-low)
  - RGB LED: GP16 WS2812 (GRB color order, NOT RGB!)
- **Libraries**: `adafruit_hid` (keyboard), `neopixel` (LED)

## Development Workflow

### Deploy Code
```bash
./deploy.sh  # Copies code.py to /media/jeff/CIRCUITPY
```
Device auto-reloads immediately after file copy. No compilation needed.

### Monitor Console
```bash
./monitor.sh  # Connects to /dev/ttyACM0 serial console
```
View `print()` statements and runtime errors. Press Ctrl+A then K to exit screen.

### Typical Development Cycle
1. Edit `code.py` in VS Code
2. Run `./deploy.sh` to push to device
3. Device reloads automatically (~2 seconds)
4. Use `./monitor.sh` to observe behavior

## Key Implementation Patterns

### Button State Detection
```python
# Simple edge detection (no debounce library needed)
button_reading = btn.value  # True=released, False=pressed
if button_reading != last_button_state:
    last_button_state = button_reading
    if not button_reading:  # Just pressed
        # Handle press
    else:  # Just released
        # Handle release
```

### Double-Press Detection
- Track `click_count` and `last_click_time`
- Increment count on each press
- After `DOUBLE_PRESS_GAP` timeout, check if count == 2
- Reset count after timeout or action

### Long-Press Detection
- Record `press_start_time` when button pressed
- On release, check `current_time - press_start_time >= LONG_PRESS_DURATION`

### Non-Blocking LED Animation
Use incremental updates in main loop instead of blocking loops:
```python
# Bad: blocks for 2 seconds
for i in range(100):
    update_led(i)
    time.sleep(0.02)

# Good: update once per loop iteration
breathe_brightness += breathe_direction * 2
if breathe_brightness >= 127:
    breathe_direction = -1
```

### Keyboard Output
```python
# Type strings
layout.write("text to type")

# Send key combinations
kbd.send(Keycode.CONTROL, Keycode.C)
kbd.send(Keycode.SPACE)
kbd.send(Keycode.LEFT_ARROW)
```

## Hardware Configuration

### Pin Assignments
- Button: `board.GP29` (internal pull-up enabled, active-low)
- RGB LED: `board.GP16` (WS2812 NeoPixel with GRB color order)

### CRITICAL: Color Order
WS2812 on this board uses **GRB**, not RGB:
```python
pixel = neopixel.NeoPixel(board.GP16, 1, pixel_order=neopixel.GRB)
pixel.fill((0, 255, 0))  # Red in GRB = (G=0, R=255, B=0)
pixel.fill((0, 128, 128))  # Purple in GRB = (G=0, R=128, B=128)
pixel.fill((191, 255, 0))  # Amber in GRB = (G=191, R=255, B=0)
```

### Button Wiring
Connect momentary switch between GP29 and GND. Internal pull-up makes pin HIGH when released, LOW when pressed.

## Library Management

Check installed libraries:
```bash
ls /media/jeff/CIRCUITPY/lib/
```

Required library: `adafruit_hid` (directory containing keyboard.py and keycode.py)

Install from CircuitPython Bundle:
1. Download bundle: https://circuitpython.org/libraries
2. Extract and copy `adafruit_hid/` folder to `/media/jeff/CIRCUITPY/lib/`

## Common Macros

### Single Keys
```python
kbd.send(Keycode.T)  # Letter T
kbd.send(Keycode.ENTER)
kbd.send(Keycode.SPACE)
```

### Modifier Combinations
```python
kbd.send(Keycode.CONTROL, Keycode.C)  # Ctrl+C
kbd.send(Keycode.CONTROL, Keycode.SHIFT, Keycode.T)  # Ctrl+Shift+T
kbd.send(Keycode.ALT, Keycode.TAB)  # Alt+Tab
kbd.send(Keycode.GUI, Keycode.D)  # Super/Windows+D
```

### Typing Strings
```python
layout = KeyboardLayout(kbd)
layout.write("Hello World!")
```
Note: Requires `from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS`

## Debugging

### Check CircuitPython Version
```bash
cat /media/jeff/CIRCUITPY/boot_out.txt
```

### View All Print Statements
Run `./monitor.sh` before deploying code to see boot messages and runtime output.

### Common Issues
- **Device not auto-reloading**: Check for syntax errors in `code.py`
- **Import errors**: Verify `adafruit_hid` is in `/media/jeff/CIRCUITPY/lib/`
- **Button not responding**: Confirm wiring (GP29 to button to GND)
- **File copy fails**: Ensure device is not write-protected

## Code Structure
- Keep all code in single `code.py` file for simplicity
- Configuration constants at top of file
- Hardware setup before main loop
- Main loop must never exit (infinite `while True:`)
- Use `time.sleep()` to control polling frequency
