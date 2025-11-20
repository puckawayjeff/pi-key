import storage
import usb_cdc
import usb_hid
import supervisor
import board
import digitalio

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
    
    # 4. Clone a Common Keyboard HWID
    # This mimics a standard "Dell KB216 Wired Keyboard"
    # VID: 0x413C (Dell)
    # PID: 0x2113 (KB216)
    supervisor.set_usb_identification(
        manufacturer="Dell Computer Corp.",
        product="KB216 Wired Keyboard",
        vid=0x413C,
        pid=0x2113
    )

    # Optional: Ensure only Keyboard/Mouse interfaces are active
    # (Removes Consumer Control if you don't need it to look simpler)
    usb_hid.enable(
        (usb_hid.Device.KEYBOARD,)
    )