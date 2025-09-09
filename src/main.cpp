/*
  Enhanced Secure Password & Keep-Alive Device for RP2040

  This sketch turns an RP2040-based board (like the Waveshare RP2040-One)
  into a multi-function USB Keyboard device.

  Features:
  - Double Press: Types a pre-defined password.
  - Long Press: Toggles a "keep-alive" mode.
  - Keep-Alive Mode: Indefinitely types a space and then a left-arrow key
    at randomized intervals to prevent a computer from sleeping or locking.
  - Single Input: All actions are controlled by a single momentary button.
  - Status LED: Uses the onboard RGB NeoPixel to indicate keep-alive status (Blue).
  - Custom USB ID: Vendor ID, Product ID, and names are now configurable.

  Setup:
  - Board: Waveshare RP2040-One (or similar RP2040 board).
  - Button: Connect a momentary pushbutton switch between the configured buttonPin
    and a Ground (GND) pin.
*/

// Required for USB HID functionality on the RP2040
#include <Adafruit_TinyUSB.h>
// Required for the onboard WS2812 RGB LED
#include <Adafruit_NeoPixel.h>

// --- Configuration ---
// Set your secret password here.
const char* superSecretPassword = "this-is-my-new-rp2040-password!";

// Pin connected to the momentary pushbutton.
// Use any available GPIO pin.
const int buttonPin = 15; // Using GP15 as an example

// Pin connected to the onboard WS2812 RGB LED.
// On the Waveshare RP2040-One, this is GP23.
const int neoPixelPin = 23;

// --- Custom USB Device Information ---
#define USB_VID   0x413C // Dell Inc.
#define USB_PID   0x0250 // Dell KB216 Wired Keyboard
char usb_product_name[] = "Dell USB Entry Keyboard";
char usb_mfg_name[] = "Dell Inc.";


// --- Timing Settings (in milliseconds) ---
const unsigned long longPressDuration = 1000;
const unsigned int doublePressGap = 300;
const unsigned int debounceDelay = 50;
const int keepAliveMinDelay = 600;
const int keepAliveMaxDelay = 2000;
// --- End of Configuration ---

// --- Global State Variables (do not change) ---
int buttonState;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long pressStartTime = 0;
int clickCount = 0;
unsigned long lastClickTime = 0;

bool keepAliveActive = false;
bool keepAliveActionToggle = false;
unsigned long lastKeepAliveActionTime = 0;
long currentKeepAliveDelay = 0;

// USB HID object for keyboard functionality
Adafruit_USBD_HID usb_hid;
// NeoPixel object for the onboard RGB LED
Adafruit_NeoPixel pixels(1, neoPixelPin, NEO_GRB + NEO_KHZ800);

void setup() {
  // Set the button pin as an input with an internal pull-up resistor.
  pinMode(buttonPin, INPUT_PULLUP);

  // Initialize the NeoPixel library.
  pixels.begin();
  pixels.setBrightness(20); // Set a moderate brightness
  pixels.clear(); // Ensure LED is off at start
  pixels.show();

  // --- Set Custom USB Descriptors ---
  // This MUST be done before TinyUSB_Device_Init()
  TinyUSBDevice.setID(USB_VID, USB_PID);
  TinyUSBDevice.setProductDescriptor(usb_product_name);
  TinyUSBDevice.setManufacturerDescriptor(usb_mfg_name);
  // --- End of Custom USB Descriptors ---

  // Initialize the USB device and set it up as a keyboard.
  TinyUSB_Device_Init(0);
  usb_hid.setPollInterval(2);
  usb_hid.setReportDescriptor(tud_hid_keyboard_descriptor, sizeof(tud_hid_keyboard_descriptor));
  usb_hid.begin();

  // Wait until USB is connected.
  while (!TinyUSBDevice.mounted()) delay(1);
}

void loop() {
  handleButton();
  handleKeepAlive();
}

/**
 * @brief Detects single, double, and long presses in a non-blocking way.
 */
void handleButton() {
  int reading = digitalRead(buttonPin);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;

      if (buttonState == LOW) { // Button pressed
        pressStartTime = millis();
        clickCount++;
        lastClickTime = pressStartTime;
      } else { // Button released
        unsigned long pressDuration = millis() - pressStartTime;
        if (pressDuration >= longPressDuration) {
          toggleKeepAlive();
          clickCount = 0;
        }
      }
    }
  }

  if (clickCount > 0 && (millis() - lastClickTime) > doublePressGap) {
    if (clickCount == 2) {
      typePassword();
    }
    clickCount = 0;
  }

  lastButtonState = reading;
}

/**
 * @brief Types the configured password followed by the Enter key.
 */
void typePassword() {
  // Wait until the USB device is ready to send keystrokes.
  while (!usb_hid.ready()) {
    delay(1);
  }
  usb_hid.keyboardReport(0, 0, NULL); // Release all keys first
  delay(50);

  // Type the password string
  for (const char* p = superSecretPassword; *p; p++) {
    usb_hid.keyboardPress(0, *p);
    delay(10); // A small delay can improve reliability
    usb_hid.keyboardRelease(0);
  }

  // Press Enter
  usb_hid.keyboardPress(0, HID_KEY_ENTER);
  delay(50);
  usb_hid.keyboardRelease(0);
}

/**
 * @brief Toggles the keep-alive mode on or off and updates the RGB LED.
 */
void toggleKeepAlive() {
  keepAliveActive = !keepAliveActive;

  if (keepAliveActive) {
    // When activating, set LED to blue and reset the timer.
    pixels.setPixelColor(0, pixels.Color(0, 0, 150)); // Blue
    pixels.show();
    lastKeepAliveActionTime = millis();
    currentKeepAliveDelay = random(keepAliveMinDelay, keepAliveMaxDelay);
  } else {
    // When deactivating, turn the LED off.
    pixels.clear();
    pixels.show();
  }
}

/**
 * @brief If keep-alive is active, performs the next key press action.
 */
void handleKeepAlive() {
  if (!keepAliveActive || !usb_hid.ready()) {
    return;
  }

  if (millis() - lastKeepAliveActionTime > currentKeepAliveDelay) {
    uint8_t keycode = keepAliveActionToggle ? HID_KEY_ARROW_LEFT : HID_KEY_SPACE;

    usb_hid.keyboardPress(0, keycode);
    delay(50); // Hold key for a moment
    usb_hid.keyboardRelease(0);

    keepAliveActionToggle = !keepAliveActionToggle;
    lastKeepAliveActionTime = millis();
    currentKeepAliveDelay = random(keepAliveMinDelay, keepAliveMaxDelay);
  }
}
