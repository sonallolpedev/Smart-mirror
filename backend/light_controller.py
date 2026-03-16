import serial
import serial.tools.list_ports
import time

class ArduinoLightController:
    def __init__(self, port=None, baud_rate=9600):
        """Initialize Arduino connection for LED control"""
        self.serial_conn = None
        self.connected = False
        self.last_state = None
        
        if port:
            self._connect(port, baud_rate)
        else:
            self._auto_connect(baud_rate)
    
    def _auto_connect(self, baud_rate):
        """Auto-detect Arduino port"""
        ports = serial.tools.list_ports.comports()
        print(f"Available ports: {[p.device for p in ports]}")
        for port in ports:
            # Look for Arduino (usually has 'Arduino' or 'CH340' or 'USB' in description)
            if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'usb', 'serial']):
                try:
                    self._connect(port.device, baud_rate)
                    if self.connected:
                        print(f"Arduino connected on {port.device}")
                        return
                except:
                    continue
        print("Arduino not found. LED control disabled.")
    
    def _connect(self, port, baud_rate):
        """Connect to Arduino on specified port"""
        try:
            self.serial_conn = serial.Serial(port, baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            self.connected = True
        except Exception as e:
            print(f"Arduino connection failed: {e}")
            self.connected = False
    
    def set_led(self, state):
        """Control LED - state: 'ON' or 'OFF'"""
        if not self.connected or not self.serial_conn:
            return False
        
        # Only send if state changed (avoid flooding serial)
        if state == self.last_state:
            return True
        
        try:
            if state == "ON":
                self.serial_conn.write(b'1\n')  # Send '1' with newline
                self.serial_conn.flush()
                print("LED -> ON")
            else:
                self.serial_conn.write(b'0\n')  # Send '0' with newline
                self.serial_conn.flush()
                print("LED -> OFF")
            self.last_state = state
            return True
        except Exception as e:
            print(f"LED control error: {e}")
            return False
    
    def close(self):
        """Close serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.set_led("OFF")  # Turn off LED before closing
            self.serial_conn.close()
            self.connected = False
