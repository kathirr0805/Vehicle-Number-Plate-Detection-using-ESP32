import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, I2C
import ujson

# Wi-Fi Configuration
WIFI_SSID = "Kathir WIFI"
WIFI_PASSWORD = "kathir2005"

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "KATHIRTEMP"
MQTT_CLIENT_ID = "ESP32_Kathir_LCD"

# I2C LCD Configuration
I2C_ADDR = 0x27  # Default I2C address for PCF8574-based LCD
SDA_PIN = 21
SCL_PIN = 22

# LCD I2C Driver (simplified for 16x2 LCD)
class I2CLCD:
    def __init__(self, i2c, addr=I2C_ADDR, cols=16, rows=2):
        self.i2c = i2c
        self.addr = addr
        self.cols = cols
        self.rows = rows
        self.buf = bytearray(1)
        self.BACKLIGHT = 0x08
        self.init_lcd()

    def init_lcd(self):
        time.sleep_ms(50)
        self.write_cmd(0x33)  # Initialize
        time.sleep_ms(5)
        self.write_cmd(0x32)  # Set to 4-bit mode
        time.sleep_ms(5)
        self.write_cmd(0x28)  # 2 lines, 5x8 font
        self.write_cmd(0x0C)  # Display on, cursor off
        self.write_cmd(0x06)  # Entry mode: increment, no shift
        self.write_cmd(0x01)  # Clear display
        time.sleep_ms(2)

    def write_cmd(self, cmd):
        self.buf[0] = cmd
        self.i2c.writeto(self.addr, bytearray([cmd & 0xF0 | self.BACKLIGHT]))
        self.i2c.writeto(self.addr, bytearray([cmd & 0xF0 | self.BACKLIGHT | 0x04]))
        self.i2c.writeto(self.addr, bytearray([cmd & 0xF0 | self.BACKLIGHT]))
        self.i2c.writeto(self.addr, bytearray([cmd << 4 | self.BACKLIGHT]))
        self.i2c.writeto(self.addr, bytearray([cmd << 4 | self.BACKLIGHT | 0x04]))
        self.i2c.writeto(self.addr, bytearray([cmd << 4 | self.BACKLIGHT]))
        time.sleep_us(50)

    def write_data(self, data):
        self.buf[0] = data
        self.i2c.writeto(self.addr, bytearray([data & 0xF0 | self.BACKLIGHT | 0x01]))
        self.i2c.writeto(self.addr, bytearray([data & 0xF0 | self.BACKLIGHT | 0x05]))
        self.i2c.writeto(self.addr, bytearray([data & 0xF0 | self.BACKLIGHT | 0x01]))
        self.i2c.writeto(self.addr, bytearray([data << 4 | self.BACKLIGHT | 0x01]))
        self.i2c.writeto(self.addr, bytearray([data << 4 | self.BACKLIGHT | 0x05]))
        self.i2c.writeto(self.addr, bytearray([data << 4 | self.BACKLIGHT | 0x01]))
        time.sleep_us(50)

    def clear(self):
        self.write_cmd(0x01)
        time.sleep_ms(2)

    def set_cursor(self, col, row):
        offsets = [0x00, 0x40]
        self.write_cmd(0x80 | (col + offsets[row]))

    def write_string(self, text):
        for char in text:
            self.write_data(ord(char))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(30):  # Wait up to 30 seconds
            if wlan.isconnected():
                print("Wi-Fi connected:", wlan.ifconfig())
                return True
            time.sleep(1)
        print("Failed to connect to Wi-Fi")
        return False
    return True

def mqtt_callback(topic, msg):
    try:
        # Decode JSON payload
        payload = ujson.loads(msg.decode('utf-8'))
        plate = payload.get('plate', '')
        if plate:
            print(f"Received license plate: {plate}")
            # Clear LCD and display plate number
            lcd.clear()
            lcd.set_cursor(0, 0)
            lcd.write_string("License Plate:")
            lcd.set_cursor(0, 1)
            # Truncate to fit 16 characters
            lcd.write_string(plate[:16])
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def main():
    # Initialize I2C and LCD
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
    global lcd
    lcd = I2CLCD(i2c, I2C_ADDR)
    
    # Display initial message
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.write_string("Initializing...")
    
    # Connect to Wi-Fi
    if not connect_wifi():
        lcd.clear()
        lcd.set_cursor(0, 0)
        lcd.write_string("Wi-Fi Error")
        return
    
    # Initialize MQTT client
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.set_callback(mqtt_callback)
        client.connect()
        client.subscribe(MQTT_TOPIC)
        print(f"Connected to MQTT broker, subscribed to {MQTT_TOPIC}")
        
        # Update LCD to show ready state
        lcd.clear()
        lcd.set_cursor(0, 0)
        lcd.write_string("Waiting for")
        lcd.set_cursor(0, 1)
        lcd.write_string("License Plate")
        
        # Main loop: check for MQTT messages
        while True:
            client.check_msg()
            time.sleep(0.1)
            
    except Exception as e:
        print(f"MQTT error: {e}")
        lcd.clear()
        lcd.set_cursor(0, 0)
        lcd.write_string("MQTT Error")
        
    finally:
        try:
            client.disconnect()
        except:
            pass

if __name__ == "__main__":
    main()