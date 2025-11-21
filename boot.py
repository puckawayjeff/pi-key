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
    """Parse config.yaml and return USB settings.
    
    Returns dict with manufacturer, product, vid, pid.
    Falls back to dell_kb216 preset if config missing or invalid.
    """
    config = {
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
    
    if preset_name == "custom":
        # Use custom values
        return {
            "manufacturer": config.get("usb_manufacturer", "Generic"),
            "product": config.get("usb_product", "USB Keyboard"),
            "vid": int(config.get("usb_vid", "0x1234"), 16) if config.get("usb_vid") else 0x1234,
            "pid": int(config.get("usb_pid", "0x5678"), 16) if config.get("usb_pid") else 0x5678,
        }
    else:
        # Use preset (default to dell_kb216 if invalid)
        return USB_PRESETS.get(preset_name, USB_PRESETS["dell_kb216"])

# 1. Setup the "Safe Mode" button
# We use the same pin as your macro button (GP29).
# If held during boot, we keep the drive/serial enabled for editing.
button = digitalio.DigitalInOut(board.GP29)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# Check if button is pressed (Logic False because of Pull-up)
# If pressed, we are in "Maintenance Mode" -> Do nothing (keep Drive/Serial)
if not button.value:
    print("Maintenance Mode: USB Drive & Serial Enabled.")

else:
    # If button is NOT pressed, go "Stealth Mode"
    
    # 2. Disable the USB Drive (Mass Storage)
    storage.disable_usb_drive()
    
    # 3. Disable the Serial Console (CDC)
    usb_cdc.disable()
    
    # 4. Load USB device configuration
    usb_config = parse_config()
    
    # 5. Set USB identification from config
    supervisor.set_usb_identification(
        manufacturer=usb_config["manufacturer"],
        product=usb_config["product"],
        vid=usb_config["vid"],
        pid=usb_config["pid"]
    )

    # 6. Enable only keyboard interface
    usb_hid.enable(
        (usb_hid.Device.KEYBOARD,)
    )