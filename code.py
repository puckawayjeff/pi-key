"""pi-key: USB HID Keyboard Emulator for Waveshare RP2040-One

Features:
- Double-press: Types macro string from macro.txt file
- Long-press (1+ sec): Activates keep-alive mode (prevents screen lock)
- Keep-alive: Sends programmable keystroke sequence from keepalive.txt at random intervals
- Visual feedback via WS2812 RGB LED
- Fully configurable via config.yaml (timing, colors, USB identity)
"""
import time
import board
import digitalio
import usb_hid
import neopixel
import random
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

# --- Hardware Configuration ---
BUTTON_PIN = board.GP29  # Momentary button (internal pull-up, active-low)
NEOPIXEL_PIN = board.GP16  # WS2812 RGB LED (GRB color order)
MACRO_FILE = "macro.txt"  # Text file containing string to type
KEEPALIVE_FILE = "keepalive.txt"  # Text file containing keep-alive sequence
CONFIG_FILE = "config.yaml"  # Configuration file

# --- Default Values ---
# These are used if config file is missing or invalid
DEFAULT_DOUBLE_PRESS_GAP = 0.5  # Max time between clicks for double-press
DEFAULT_LONG_PRESS_DURATION = 1.0  # Hold duration to trigger keep-alive
DEFAULT_KEEP_ALIVE_MIN = 0.8  # Minimum interval between keep-alive keystrokes
DEFAULT_KEEP_ALIVE_MAX = 2.0  # Maximum interval between keep-alive keystrokes
DEFAULT_MACRO_COLOR = (0, 128, 128)  # Purple in GRB
DEFAULT_KEEPALIVE_COLOR = (191, 255, 0)  # Amber in GRB
DEFAULT_CANCEL_COLOR = (0, 255, 0)  # Red in GRB

# --- Named Colors (in GRB format for WS2812) ---
NAMED_COLORS = {
    "red": (0, 255, 0),
    "green": (255, 0, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (255, 0, 255),
    "magenta": (0, 255, 255),
    "white": (255, 255, 255),
    "purple": (0, 128, 128),
    "amber": (191, 255, 0),
    "orange": (128, 255, 0),
}

def parse_hex_color(hex_str):
    """Convert hex color code to GRB tuple for WS2812.
    
    Args:
        hex_str: Hex color string (e.g., "#FF00FF" or "FF00FF")
    
    Returns:
        Tuple (G, R, B) for WS2812 LED
    """
    # Remove # prefix if present
    hex_str = hex_str.strip().lstrip("#")
    
    # Parse RGB values
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (g, r, b)  # Convert RGB to GRB
    else:
        raise ValueError("Invalid hex color format")

def parse_color(color_str):
    """Parse color string (hex or named color) to GRB tuple.
    
    Args:
        color_str: Color string (e.g., "#FF00FF", "purple", "red")
    
    Returns:
        Tuple (G, R, B) for WS2812 LED
    """
    color_str = color_str.strip().lower()
    
    # Check if it's a named color
    if color_str in NAMED_COLORS:
        return NAMED_COLORS[color_str]
    
    # Try to parse as hex
    try:
        return parse_hex_color(color_str)
    except:
        # Return default purple if parsing fails
        return DEFAULT_MACRO_COLOR

def parse_config():
    """Parse config.yaml and return configuration settings.
    
    Returns dict with timing constants and color settings.
    Falls back to defaults if config missing or invalid.
    """
    config = {
        "double_press_gap": DEFAULT_DOUBLE_PRESS_GAP,
        "long_press_duration": DEFAULT_LONG_PRESS_DURATION,
        "keep_alive_min": DEFAULT_KEEP_ALIVE_MIN,
        "keep_alive_max": DEFAULT_KEEP_ALIVE_MAX,
        "macro_color": DEFAULT_MACRO_COLOR,
        "keepalive_color": DEFAULT_KEEPALIVE_COLOR,
        "cancel_color": DEFAULT_CANCEL_COLOR,
    }
    
    try:
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                # Strip whitespace and skip comments/empty lines
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Parse key: value pairs
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove trailing comments
                    if "#" in value:
                        value = value.split("#")[0].strip()
                    
                    # Parse timing values
                    if key == "double_press_gap":
                        config["double_press_gap"] = float(value)
                    elif key == "long_press_duration":
                        config["long_press_duration"] = float(value)
                    elif key == "keep_alive_min":
                        config["keep_alive_min"] = float(value)
                    elif key == "keep_alive_max":
                        config["keep_alive_max"] = float(value)
                    # Parse color values
                    elif key == "macro_color":
                        config["macro_color"] = parse_color(value)
                    elif key == "keepalive_color":
                        config["keepalive_color"] = parse_color(value)
                    elif key == "cancel_color":
                        config["cancel_color"] = parse_color(value)
    except Exception as e:
        print(f"Config error (using defaults): {e}")
    
    return config

# --- Load Configuration ---
config = parse_config()
DOUBLE_PRESS_GAP = config["double_press_gap"]
LONG_PRESS_DURATION = config["long_press_duration"]
KEEP_ALIVE_MIN = config["keep_alive_min"]
KEEP_ALIVE_MAX = config["keep_alive_max"]
MACRO_COLOR = config["macro_color"]
KEEPALIVE_COLOR = config["keepalive_color"]
CANCEL_COLOR = config["cancel_color"]

print(f"Config loaded: gap={DOUBLE_PRESS_GAP}s, long={LONG_PRESS_DURATION}s, "
      f"keepalive={KEEP_ALIVE_MIN}-{KEEP_ALIVE_MAX}s")

# --- Load Macro String from File ---
try:
    with open(MACRO_FILE, "r") as f:
        MACRO_STRING = f.read().strip()
    print(f"Loaded macro: {MACRO_STRING}")
except Exception as e:
    print(f"Error loading {MACRO_FILE}: {e}")
    MACRO_STRING = "fallback-text"

# --- Load Keep-Alive Sequence from File ---
try:
    with open(KEEPALIVE_FILE, "r") as f:
        KEEPALIVE_STRING = f.read().strip()
    print(f"Loaded keepalive: {KEEPALIVE_STRING}")
except Exception as e:
    print(f"Error loading {KEEPALIVE_FILE} (using default): {e}")
    KEEPALIVE_STRING = "{SPACE}{LEFT_ARROW}"

# --- Special Key Mapping ---
# Maps {KEY} patterns to Keycode constants
SPECIAL_KEYS = {
    "ENTER": Keycode.ENTER,
    "TAB": Keycode.TAB,
    "SPACE": Keycode.SPACE,
    "BACKSPACE": Keycode.BACKSPACE,
    "DELETE": Keycode.DELETE,
    "ESC": Keycode.ESCAPE,
    "UP": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
    "HOME": Keycode.HOME,
    "END": Keycode.END,
    "PAGEUP": Keycode.PAGE_UP,
    "PAGEDOWN": Keycode.PAGE_DOWN,
}

# Maps modifier names to Keycode constants
MODIFIERS = {
    "CTRL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT,
    "ALT": Keycode.ALT,
    "GUI": Keycode.GUI,  # Windows/Super/Command key
    "WIN": Keycode.GUI,
    "CMD": Keycode.GUI,
}

# --- Hardware Initialization ---
# USB HID keyboard
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

# Button with internal pull-up (True=released, False=pressed)
btn = digitalio.DigitalInOut(BUTTON_PIN)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.UP

# WS2812 RGB LED (GRB color order on Waveshare RP2040-One)
pixel = neopixel.NeoPixel(
    NEOPIXEL_PIN, 1, brightness=1.0,
    auto_write=False, pixel_order=neopixel.GRB
)
pixel.fill((0, 0, 0))
pixel.show()

# --- Button State Tracking ---
last_button_state = True  # Button starts released
press_start_time = 0  # Time when button was pressed
click_count = 0  # Number of clicks for double-press detection
last_click_time = 0  # Time of last click

# --- Keep-Alive Mode State ---
keep_alive_active = False  # Is keep-alive mode active?
last_keep_alive_time = 0  # Last time we sent a keystroke
next_keep_alive_delay = 0  # Randomized delay for next keystroke

# --- LED Breathing Animation State ---
breathe_brightness = 0  # Current brightness (0-127)
breathe_direction = 1  # 1=brightening, -1=dimming


def parse_and_type_macro(macro_string):
    """Parse macro string and type it, handling special key sequences.
    
    Supports:
    - Plain text: "hello world"
    - Special keys: "text{ENTER}" or "{TAB}more text"
    - Modifiers: "{CTRL+C}" or "{SHIFT+TAB}"
    - Multiple modifiers: "{CTRL+SHIFT+T}"
    - Literal braces: "{{" for { and "}}" for }
    
    Special keys are wrapped in curly braces: {KEYNAME}
    Modifiers use + to combine: {MOD+KEY}
    """
    i = 0
    while i < len(macro_string):
        # Check for escaped literal braces
        if i < len(macro_string) - 1:
            if macro_string[i:i+2] == '{{':
                layout.write('{')
                i += 2
                continue
            elif macro_string[i:i+2] == '}}':
                layout.write('}')
                i += 2
                continue
        
        # Check for special key sequence
        if macro_string[i] == '{':
            # Find closing brace
            close_idx = macro_string.find('}', i)
            if close_idx == -1:
                # No closing brace, treat as literal
                layout.write(macro_string[i])
                i += 1
                continue
            
            # Extract key sequence
            key_seq = macro_string[i+1:close_idx].upper()
            
            # Check for modifier+key combination
            if '+' in key_seq:
                parts = key_seq.split('+')
                modifiers = []
                key = None
                
                # Parse modifiers and key
                for part in parts:
                    part = part.strip()
                    if part in MODIFIERS:
                        modifiers.append(MODIFIERS[part])
                    elif part in SPECIAL_KEYS:
                        key = SPECIAL_KEYS[part]
                    else:
                        # Try as single character
                        if len(part) == 1:
                            key = getattr(Keycode, part, None)
                
                # Send modifier combination
                if key and modifiers:
                    kbd.send(*modifiers, key)
                elif key:
                    kbd.send(key)
                else:
                    # Invalid sequence, type it literally
                    layout.write(macro_string[i:close_idx+1])
            
            # Single special key
            elif key_seq in SPECIAL_KEYS:
                kbd.send(SPECIAL_KEYS[key_seq])
            else:
                # Unknown key, type literally
                layout.write(macro_string[i:close_idx+1])
            
            i = close_idx + 1
        else:
            # Regular character, type it
            layout.write(macro_string[i])
            i += 1


def color_flash(color):
    """Visual feedback for typing macro: color ramp up to 80%, then down.
    
    Total duration: ~1 second (0.5s up, 0.5s down)
    
    Args:
        color: Tuple (G, R, B) in GRB order for WS2812
    """
    steps = 20
    max_bright = 0.8  # 80% brightness
    
    # Ramp up
    for i in range(steps):
        brightness = (i / steps) * max_bright
        pixel.fill((int(color[0] * brightness),
                    int(color[1] * brightness),
                    int(color[2] * brightness)))
        pixel.show()
        time.sleep(0.025)
    
    # Ramp down
    for i in range(steps, -1, -1):
        brightness = (i / steps) * max_bright
        pixel.fill((int(color[0] * brightness),
                    int(color[1] * brightness),
                    int(color[2] * brightness)))
        pixel.show()
        time.sleep(0.025)
    
    pixel.fill((0, 0, 0))
    pixel.show()


def color_pulse(color):
    """Visual feedback for exiting keep-alive: two quick flashes.
    
    Args:
        color: Tuple (G, R, B) in GRB order for WS2812
    """
    for _ in range(2):
        pixel.fill(color)
        pixel.show()
        time.sleep(0.15)
        pixel.fill((0, 0, 0))
        pixel.show()
        time.sleep(0.15)


def update_breathe(color):
    """Update breathing LED for keep-alive mode (non-blocking).
    
    Called every loop iteration when keep-alive is active.
    Smoothly breathes from 0 to 50% brightness and back.
    
    Args:
        color: Tuple (G, R, B) in GRB order for WS2812
    """
    global breathe_brightness, breathe_direction
    
    # Update brightness
    breathe_brightness += breathe_direction * 2
    
    # Reverse direction at limits (0-127 = 0-50% brightness)
    if breathe_brightness >= 127:
        breathe_brightness = 127
        breathe_direction = -1
    elif breathe_brightness <= 0:
        breathe_brightness = 0
        breathe_direction = 1
    
    # Apply color with brightness
    brightness_factor = breathe_brightness / 255
    pixel.fill((int(color[0] * brightness_factor),
                int(color[1] * brightness_factor),
                int(color[2] * brightness_factor)))
    pixel.show()


# --- Main Program ---
print("Macro Keyboard Ready!")
print("- Double-press: Type macro")
print("- Long-press: Activate keep-alive mode")

while True:
    current_time = time.monotonic()
    button_reading = btn.value  # True=released, False=pressed
    
    # Update breathing LED animation if in keep-alive mode
    if keep_alive_active:
        update_breathe(KEEPALIVE_COLOR)
    
    # Detect button state changes
    if button_reading != last_button_state:
        last_button_state = button_reading
        
        # Button just pressed (active-low: True→False)
        if not button_reading:
            print("Button pressed")
            press_start_time = current_time
            
            # Any press during keep-alive exits the mode
            if keep_alive_active:
                print("Exiting keep-alive mode")
                keep_alive_active = False
                color_pulse(CANCEL_COLOR)
                pixel.fill((0, 0, 0))
                pixel.show()
            else:
                # Count clicks for double-press detection
                click_count += 1
                last_click_time = current_time
        
        # Button just released (active-low: False→True)
        else:
            print(f"Button released ({current_time - press_start_time:.2f}s)")
    
    # Long press detection: check while button is held
    if (not button_reading and not keep_alive_active and
            press_start_time > 0 and
            (current_time - press_start_time) >= LONG_PRESS_DURATION):
        print("Long press - activating keep-alive")
        keep_alive_active = True
        last_keep_alive_time = current_time
        # Set initial random delay
        next_keep_alive_delay = random.uniform(KEEP_ALIVE_MIN,
                                               KEEP_ALIVE_MAX)
        click_count = 0  # Clear pending clicks
        press_start_time = 0  # Prevent re-triggering
    
    # Double-press detection: check if timeout expired
    if (click_count > 0 and
            (current_time - last_click_time) > DOUBLE_PRESS_GAP):
        if click_count == 2 and not keep_alive_active:
            print("Double press - typing macro")
            parse_and_type_macro(MACRO_STRING)  # Parse and type
            color_flash(MACRO_COLOR)  # Then show animation
        click_count = 0  # Reset for next detection
    
    # Keep-alive: send keystrokes at random intervals
    if (keep_alive_active and
            (current_time - last_keep_alive_time) > next_keep_alive_delay):
        # Type the keep-alive sequence
        parse_and_type_macro(KEEPALIVE_STRING)
        last_keep_alive_time = current_time
        # Generate next random delay
        next_keep_alive_delay = random.uniform(KEEP_ALIVE_MIN,
                                               KEEP_ALIVE_MAX)
    
    time.sleep(0.01)  # Poll at 100Hz
