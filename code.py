"""pi-key: USB HID Keyboard Emulator for Waveshare RP2040-One

Features:
- Double-press: Types macro string from macro.txt file
- Long-press (1+ sec): Activates keep-alive mode (prevents screen lock)
- Keep-alive: Alternates Space and Left-Arrow keypresses every 600ms
- Visual feedback via WS2812 RGB LED
"""
import time
import board
import digitalio
import usb_hid
import neopixel
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

# --- Hardware Configuration ---
BUTTON_PIN = board.GP29  # Momentary button (internal pull-up, active-low)
NEOPIXEL_PIN = board.GP16  # WS2812 RGB LED (GRB color order)
MACRO_FILE = "macro.txt"  # Text file containing string to type

# --- Timing Constants (in seconds) ---
DOUBLE_PRESS_GAP = 0.3  # Max time between clicks for double-press
LONG_PRESS_DURATION = 1.0  # Hold duration to trigger keep-alive
KEEP_ALIVE_MIN = 0.6  # Interval between keep-alive keystrokes

# --- Load Macro String from File ---
try:
    with open(MACRO_FILE, "r") as f:
        MACRO_STRING = f.read().strip()
    print(f"Loaded macro: {MACRO_STRING}")
except Exception as e:
    print(f"Error loading {MACRO_FILE}: {e}")
    MACRO_STRING = "fallback-text"

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
keep_alive_toggle = False  # Alternate between space and arrow

# --- LED Breathing Animation State ---
breathe_brightness = 0  # Current brightness (0-127)
breathe_direction = 1  # 1=brightening, -1=dimming


def purple_flash():
    """Visual feedback for typing macro: purple ramp up to 80%, then down.
    
    Total duration: ~1 second (0.5s up, 0.5s down)
    Color: Purple (Red + Blue) in GRB order = (0, R, B)
    """
    steps = 20
    max_bright = 204  # 80% of 255
    
    # Ramp up
    for i in range(steps):
        brightness = int((i / steps) * max_bright)
        pixel.fill((0, brightness, brightness))  # GRB: purple = (0, R, B)
        pixel.show()
        time.sleep(0.025)
    
    # Ramp down
    for i in range(steps, -1, -1):
        brightness = int((i / steps) * max_bright)
        pixel.fill((0, brightness, brightness))
        pixel.show()
        time.sleep(0.025)
    
    pixel.fill((0, 0, 0))
    pixel.show()


def red_pulse():
    """Visual feedback for exiting keep-alive: two quick red flashes.
    
    Color: Red in GRB order = (0, 255, 0)
    """
    for _ in range(2):
        pixel.fill((0, 255, 0))  # GRB: red = (0, R, 0)
        pixel.show()
        time.sleep(0.15)
        pixel.fill((0, 0, 0))
        pixel.show()
        time.sleep(0.15)


def update_breathe():
    """Update amber breathing LED for keep-alive mode (non-blocking).
    
    Called every loop iteration when keep-alive is active.
    Smoothly breathes from 0 to 50% brightness and back.
    Color: Amber in GRB order = (191, 255, 0)
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
    
    # Apply color (amber in GRB order)
    brightness_factor = breathe_brightness / 255
    pixel.fill((int(191 * brightness_factor),
                int(255 * brightness_factor), 0))
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
        update_breathe()
    
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
                red_pulse()
                pixel.fill((0, 0, 0))
                pixel.show()
            else:
                # Count clicks for double-press detection
                click_count += 1
                last_click_time = current_time
        
        # Button just released (active-low: False→True)
        else:
            press_duration = current_time - press_start_time
            print(f"Button released ({press_duration:.2f}s)")
            
            # Long press: activate keep-alive mode
            if (press_duration >= LONG_PRESS_DURATION and
                    not keep_alive_active):
                print("Long press - activating keep-alive")
                keep_alive_active = True
                last_keep_alive_time = current_time
                click_count = 0  # Clear pending clicks
    
    # Double-press detection: check if timeout expired
    if (click_count > 0 and
            (current_time - last_click_time) > DOUBLE_PRESS_GAP):
        if click_count == 2 and not keep_alive_active:
            print("Double press - typing macro")
            purple_flash()
            layout.write(MACRO_STRING)
        click_count = 0  # Reset for next detection
    
    # Keep-alive: send alternating keystrokes
    if (keep_alive_active and
            (current_time - last_keep_alive_time) > KEEP_ALIVE_MIN):
        if keep_alive_toggle:
            kbd.send(Keycode.LEFT_ARROW)
        else:
            kbd.send(Keycode.SPACE)
        keep_alive_toggle = not keep_alive_toggle
        last_keep_alive_time = current_time
    
    time.sleep(0.01)  # Poll at 100Hz
