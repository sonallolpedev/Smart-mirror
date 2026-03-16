import serial
import time

class ArduinoLightController:
    def __init__(self, port='COM3', baudrate=9600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2) # Wait for connection
            print(f"Connected to Arduino on {port}")
        except Exception as e:
            print(f"Error: Could not connect to Arduino. {e}")
            self.ser = None

    def turn_on(self):
        if self.ser:
            self.ser.write(b'1')
            print("Hardware Command: LED ON")

    def turn_off(self):
        if self.ser:
            self.ser.write(b'0')
            print("Hardware Command: LED OFF")

    def check_wake_command(self):
        if self.ser and self.ser.in_available() > 0:
            line = self.ser.readline().decode('utf-8').strip()
            if line == "WAKE":
                return True
        return False

# Example of how to use in Main Script:
# light = ArduinoLightController(port='COM3')
# if gesture == "PALM": light.turn_on()