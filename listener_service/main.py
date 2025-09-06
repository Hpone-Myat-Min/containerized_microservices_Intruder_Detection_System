from flask import Flask
import serial
import time
import threading
import requests

app = Flask(__name__)

is_monitoring = False
serial_port = serial.Serial('/dev/rfcomm0', baudrate=9600, timeout=1)
MONITORING_URL = ""

def listen_bluetooth():
    while True:
        try:
            motion_status = serial_port.readline().decode('utf-8').strip() # listening for bluetooth serial signal
            if motion_status == "MOTION_DETECTED" and not is_monitoring:
                print("PIR detects motion and now camera will be open")
                is_monitoring = True

                try:
                    response = requests.post(MONITORING_URL, timeout=5)
                    print("Triggered Monitoring Service: ", response.status_code)
                except Exception as e:
                    print("Failed to trigger service: ", e)

                time.sleep(15)
                is_monitoring = False
        
        except Exception as e:
            print("Listener service error: ", e)
            time.sleep(2)

app.route("/")
def index():
    return "Listener Service is running"

if __name__ == "__main__":
    threading.Thread(target=listen_bluetooth, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)







