# Vehicle License Plate Detection and Display System

## Overview
This project implements a vehicle license plate detection system using computer vision and MQTT communication. The system consists of two main components:

1. **Vehicle Detection Script (Python)**: Uses OpenCV and Tesseract OCR to detect yellow license plates in a video feed, extract the plate text, and publish it to an MQTT broker.
2. **ESP32 Display Script (MicroPython)**: Receives the license plate data via MQTT and displays it on a 16x2 LCD screen connected to an ESP32 microcontroller.

The system is designed for real-time license plate detection and remote display, suitable for applications like automated vehicle monitoring or parking systems.

## Features
- Detects yellow license plates in a video feed using color segmentation and contour detection.
- Extracts license plate text using Tesseract OCR with custom configuration for alphanumeric characters.
- Publishes detected plate data to an MQTT broker in JSON format.
- ESP32 subscribes to the MQTT topic and displays the received license plate on a 16x2 LCD.
- Includes debouncing to prevent duplicate MQTT messages for the same plate.
- Configurable parameters for MQTT, Tesseract, and image processing.

## Requirements

### Hardware
- **For Vehicle Detection**:
  - A computer with a webcam or an external camera.
- **For ESP32 Display**:
  - ESP32 microcontroller (e.g., ESP32-WROOM-32).
  - 16x2 LCD with PCF8574 I2C backpack.
  - Wi-Fi network access for the ESP32.

### Software
- **Vehicle Detection Script**:
  - Python 3.7+
  - OpenCV (`pip install opencv-python`)
  - NumPy (`pip install numpy`)
  - Pytesseract (`pip install pytesseract`)
  - Tesseract OCR installed (set path in `TESSERACT_PATH`)
  - Paho MQTT (`pip install paho-mqtt`)
  - Pillow (`pip install Pillow`)
- **ESP32 Display Script**:
  - MicroPython firmware on ESP32
  - `umqtt.simple` library (available in MicroPython)
  - `ujson` library (included with MicroPython)
  - I2C LCD library (provided in `esp32.py`)

## Installation

### Vehicle Detection Script
1. Install Tesseract OCR:
   - Download and install Tesseract from [here](https://github.com/UB-Mannheim/tesseract/wiki).
   - Update the `TESSERACT_PATH` variable in `vehicle detection + mqtt.py` with the path to `tesseract.exe`.
2. Install Python dependencies:
   ```bash
   pip install opencv-python numpy pytesseract paho-mqtt Pillow
3.Save the script as vehicle detection + mqtt.py.

##ESP32 Display Script
Flash MicroPython firmware to the ESP32 using a tool like esptool.py.
Install the umqtt.simple library on the ESP32:
Copy the umqtt/simple.py from the MicroPython library to the ESP32 filesystem.
Update the Wi-Fi credentials (WIFI_SSID, WIFI_PASSWORD) in esp32.py.
Upload esp32.py to the ESP32.
Connect the 16x2 LCD to the ESP32:
```bash
SDA to GPIO 21
SCL to GPIO 22
VCC to 3.3V or 5V (check LCD specifications)
GND to GND
```

##Configuration
Vehicle Detection:
MQTT_BROKER: Set to your MQTT broker address (default: test.mosquitto.org).
MQTT_PORT: Default is 1883.
MQTT_TOPIC: Topic for publishing/receiving plate data (default: KATHIRTEMP).
MQTT_CLIENT_ID: Unique client ID (default: ESP32_Kathir).
MIN_PLATE_LENGTH: Minimum characters for a valid plate (default: 4).
DEBOUNCE_TIME: Seconds to wait before resending the same plate (default: 3).

##ESP32 Display:
WIFI_SSID and WIFI_PASSWORD: Your Wi-Fi credentials.
MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_CLIENT_ID: Must match the vehicle detection script.
I2C_ADDR, SDA_PIN, SCL_PIN: Adjust if your LCD uses different I2C settings.
Usage
Run the Vehicle Detection Script:
```bash
python "vehicle detection + mqtt.py"
```

The script starts the webcam, detects yellow license plates, and publishes the plate text to the MQTT broker.
Press q to quit.
Run the ESP32 Script:
Upload esp32.py to the ESP32 and run it.
The ESP32 connects to Wi-Fi, subscribes to the MQTT topic, and displays received license plates on the LCD.


##Operation:
The vehicle detection script processes the webcam feed, detects yellow plates, extracts text, and sends it via MQTT.
The ESP32 receives the MQTT messages and updates the LCD with the license plate number.

##Notes
Ensure both scripts use the same MQTT_TOPIC for communication.
The vehicle detection script is optimized for yellow license plates. Adjust the HSV range (lower_yellow, upper_yellow) for other plate colors.
The LCD display truncates plates longer than 16 characters to fit the 16x2 display.
The system uses the public test.mosquitto.org broker for testing. For production, use a secure, private MQTT broker.

##Troubleshooting
Camera not detected: Check if the webcam is connected and accessible (cv2.VideoCapture(0)).
Tesseract errors: Verify the TESSERACT_PATH and ensure Tesseract is installed.
MQTT connection issues: Confirm the broker address, port, and internet connectivity.
ESP32 Wi-Fi failure: Double-check WIFI_SSID and WIFI_PASSWORD.
LCD not displaying: Verify I2C connections and address (I2C_ADDR).

##License
This project is licensed under the MIT License.

##Acknowledgments
OpenCV for image processing.
Tesseract OCR for text recognition.
Paho MQTT and umqtt.simple for MQTT communication.
MicroPython for ESP32 programming.
