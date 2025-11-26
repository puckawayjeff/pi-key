import storage
import usb_cdc
import usb_hid
import supervisor
import board
import digitalio

# === USB Device Presets ===
USB_PRESETS = {
    "dell_kb216": {
        "manufacturer": "Dell Computer Corp.",
        "product": "KB216 Wired Keyboard",
        "vid": 0x413C,
        "pid": 0x2113,
    },
    "logitech_k120": {
        "manufacturer": "Logitech",
        "product": "USB Keyboard",
        "vid": 0x046D,
        "pid": 0xC31C,
    },
    "hp_km100": {
        "manufacturer": "Chicony Electronics Co., Ltd.",
        "product": "HP USB Keyboard",
        "vid": 0x03F0,
        "pid": 0x0024,
    },
    "microsoft_600": {
        "manufacturer": "Microsoft",
        "product": "Wired Keyboard 600",
        "vid": 0x045E,
        "pid": 0x0750,
    },
    "apple_keyboard": {
        "manufacturer": "Apple Inc.",
        "product": "Apple Keyboard",
        "vid": 0x05AC,
        "pid": 0x0250,
    },
}

def parse_config():
    """Parse config.yaml and return USB settings and button type.
    
    Returns dict with manufacturer, product, vid, pid, button_type.
    Falls back to dell_kb216 preset if config missing or invalid.
    """
    config = {
        "button_type": "mechanical",
        "usb_preset": "dell_kb216",
        "usb_manufacturer": None,
        "usb_product": None,
        "usb_vid": None,
        "usb_pid": None,
    }
    
    try:
        with open("config.yaml", "r") as f:
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
                    
                    # Store config values
                    if key in config:
                        config[key] = value
    except Exception as e:
        print(f"Config error (using defaults): {e}")
    
    # Determine USB settings
    preset_name = config.get("usb_preset", "dell_kb216")
    
    result = {}
    if preset_name == "custom":
        # Use custom values
        result = {
            "manufacturer": config.get("usb_manufacturer", "Generic"),
            "product": config.get("usb_product", "USB Keyboard"),
            "vid": int(config.get("usb_vid", "0x1234"), 16),
            "pid": int(config.get("usb_pid", "0x5678"), 16),
        }
    else:
        # Use preset (default to dell_kb216 if invalid)
        result = USB_PRESETS.get(preset_name, USB_PRESETS["dell_kb216"])
    
    # Add button type to result
    result["button_type"] = config.get("button_type", "mechanical")
    return result


def read_button(button, button_type):
    """Read button state with logic inversion for capacitive sensors.
    
    Args:
        button: DigitalInOut button object
        button_type: "mechanical" or "capacitive"
    
    Returns:
        bool: True if button is released, False if pressed
              (normalized to active-low logic regardless of sensor type)
    """
    raw_value = button.value
    if button_type == "capacitive":
        # Capacitive sensors in AB=00 mode output HIGH when touched
        # Invert so pressed=False (active-low, like mechanical)
        return not raw_value
    else:
        # Mechanical switches are active-low by default
        # Released=HIGH (True), Pressed=LOW (False)
        return raw_value


# 1. Load configuration
config = parse_config()
button_type = config.get("button_type", "mechanical")

# 2. Setup the "Safe Mode" button
# We use the same pin as your macro button (GP29).
# If held during boot, we keep the drive/serial enabled for editing.
button = digitalio.DigitalInOut(board.GP29)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# Check if button is pressed (normalized for button type)
# If pressed, we are in "Maintenance Mode" -> Do nothing (keep Drive/Serial)
button_reading = read_button(button, button_type)
if not button_reading:
    print("Maintenance Mode: USB Drive & Serial Enabled.")

else:
    # If button is NOT pressed, go "Stealth Mode"
    
    # 3. Disable the USB Drive (Mass Storage)
    storage.disable_usb_drive()
    
    # 4. Disable the Serial Console (CDC)
    usb_cdc.disable()
    
    # 5. Set USB identification from config
    supervisor.set_usb_identification(
        manufacturer=config["manufacturer"],
        product=config["product"],
        vid=config["vid"],
        pid=config["pid"]
    )

    # 6. Enable only keyboard interface
    usb_hid.enable(
        (usb_hid.Device.KEYBOARD,)
    )
