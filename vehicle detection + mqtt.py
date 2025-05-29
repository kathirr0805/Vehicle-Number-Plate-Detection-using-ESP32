import cv2
import numpy as np
import pytesseract
import paho.mqtt.client as mqtt
import time
from PIL import Image
import json

# Configuration
TESSERACT_PATH = r'S:\Python_Add\Tesseract\tesseract.exe'
MQTT_BROKER = "test.mosquitto.org"  # Mosquitto test broker
MQTT_PORT = 1883                   # Default MQTT port
MQTT_TOPIC = "KATHIRTEMP"          # Custom topic
MQTT_CLIENT_ID = "ESP32_Kathir"    # Unique client ID
MIN_PLATE_LENGTH = 4               # Minimum characters to consider as valid plate
DEBOUNCE_TIME = 3                  # Seconds to wait before sending the same plate again

# Set the path to Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}")
    else:
        print(f"Failed to connect to MQTT broker with code: {rc}")

def initialize_mqtt():
    try:
        client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv5)
        client.on_connect = on_connect
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()  # Start the network loop in a separate thread
        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        return client
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return None

def detect_yellow_plate(img):
    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define range for yellow color in HSV
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    
    # Threshold the HSV image to get only yellow colors
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Bitwise-AND mask and original image
    yellow_region = cv2.bitwise_and(img, img, mask=mask)
    
    # Convert to grayscale for further processing
    gray = cv2.cvtColor(yellow_region, cv2.COLOR_BGR2GRAY)
    
    return gray

def preprocess_plate(plate_img):
    # Enhance contrast
    plate_img = cv2.convertScaleAbs(plate_img, alpha=1.5, beta=0)
    
    # Apply adaptive thresholding
    plate_img = cv2.adaptiveThreshold(plate_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    
    # Apply morphological operations to clean up the image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    plate_img = cv2.morphologyEx(plate_img, cv2.MORPH_CLOSE, kernel)
    
    return plate_img

def find_license_plate_contours(img):
    # Find contours in the image
    contours, _ = cv2.findContours(img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by area in descending order
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    plate_contour = None
    
    # Find the rectangular contour that is likely to be a license plate
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        
        # License plate typically has 4 corners and is a rectangle
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            
            # Check for reasonable aspect ratio of license plate
            if 2.0 < aspect_ratio < 5.0:
                plate_contour = approx
                break
    
    return plate_contour

def recognize_plate_text(plate_img):
    # Apply additional processing for better OCR results
    plate_img = cv2.medianBlur(plate_img, 3)
    plate_img = cv2.threshold(plate_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Use Tesseract to recognize text with custom configuration
    config = '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    text = pytesseract.image_to_string(plate_img, config=config)
    
    # Clean up the recognized text (remove spaces and special characters)
    text = ''.join(e for e in text if e.isalnum())
    
    # Only return text that looks like a license plate
    if len(text) >= MIN_PLATE_LENGTH:
        return text.upper()  # Convert to uppercase for consistency
    return ""

def publish_mqtt_data(client, plate_text):
    if client and client.is_connected():
        try:
            # Create a JSON payload
            payload = {
                "plate": plate_text,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            # Publish the JSON payload to the MQTT topic
            result = client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published to {MQTT_TOPIC}: {plate_text}")
            else:
                print(f"Failed to publish to {MQTT_TOPIC}")
        except Exception as e:
            print(f"MQTT publish error: {e}")

def main():
    # Initialize MQTT client
    mqtt_client = initialize_mqtt()
    
    # Initialize the integrated camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        return
    
    print("Yellow License Plate Detection started. Press 'q' to quit.")
    last_valid_plate = ""
    last_sent_time = 0
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Detect yellow regions first
        yellow_region = detect_yellow_plate(frame)
        
        # Find license plate contours
        plate_contour = find_license_plate_contours(yellow_region)
        
        if plate_contour is not None:
            # Get the bounding rectangle of the contour
            x, y, w, h = cv2.boundingRect(plate_contour)
            
            # Draw the contour on the original image
            cv2.drawContours(frame, [plate_contour], -1, (0, 255, 0), 3)
            
            # Extract and preprocess the license plate region
            plate_region = frame[y:y+h, x:x+w]
            plate_gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            plate_processed = preprocess_plate(plate_gray)
            
            # Recognize the license plate text
            plate_text = recognize_plate_text(plate_processed)
            
            if plate_text:
                current_time = time.time()
                
                # Check if plate is different or enough time has passed since last publish
                if (plate_text != last_valid_plate or 
                    (current_time - last_sent_time) > DEBOUNCE_TIME):
                    
                    print(f"Detected License Plate: {plate_text}")
                    publish_mqtt_data(mqtt_client, plate_text)
                    
                    last_valid_plate = plate_text
                    last_sent_time = current_time
                
                # Display the recognized text on the frame
                cv2.putText(frame, plate_text, (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Display the resulting frame
        cv2.imshow('Yellow License Plate Detection', frame)
        
        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    if mqtt_client and mqtt_client.is_connected():
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Disconnected from MQTT broker")

if __name__ == "__main__":
    main()