from flask import Flask, jsonify
from picamera2 import Picamera2
from datetime import datetime
import os
import time
import threading
import requests

app = Flask(__name__)

CLOUD_SERVICE_URL = "http://upload:5000/upload"
IMAGES_DIR = "/app/Images"

is_monitoring = False

def start_monitoring():
    # Capture 10 photos with 1 second interval 
    global is_monitoring
    is_monitoring = True
    print("Monitoring Service is starting")

    picam = Picamera2()
    # picam.start_preview(Preview.QT)
    picam.start()

    image_paths = []

    capture_start_time = time.time()                                     # overall start time of image capturing

    for i in range(10):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = "image_" + timestamp + "_" + str(i) + ".jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        picam.capture_file(filepath)

        image_paths.append(filepath)
        print(f"Image {i} is captured")
        time.sleep(1)

    capture_end_time = time.time()                                      # overall end time of image capturing
    # picam.stop_preview()
    picam.close()
    print("Monitoring service completed")

    try:
        response = requests.post(CLOUD_SERVICE_URL, json={"image_paths": image_paths})
        print("Triggered Cloud Communication Service: ", response.status_code)

    except Exception as e:
        print("Failed to connect Cloud Communication Service: ", e)

    try: 
        response = requests.post("http://listener:5000/capture_complete")
        return jsonify({"status": "ok"}), 200
        print("Notified availability to Listener Service: ", response.status_code)
    except Exception as e:
        print("Failed to notify listener service: ", e)

    is_monitoring = False

@app.route("/start", methods=["POST"])
def start_capturing():
    global is_monitoring
    if is_monitoring:
        return jsonify({"status": "busy"}), 409
    
    threading.Thread(target=start_monitoring).start()
    return jsonify({"status": "started"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

    