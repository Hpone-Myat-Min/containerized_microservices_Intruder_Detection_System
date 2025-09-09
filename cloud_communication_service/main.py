import os
import boto3
from datetime import datetime
import time
import requests
import threading
from queue import Queue
from flask import Flask,request, jsonify

app = Flask(__name__)

s3 = boto3.client('s3') 
S3_BUCKET = "intruder-detection-images"
IMAGES_DIR = "/app/Images"
image_queue = Queue()

DEPLOYMENT_MODE =os.getenv("DEPLOYMENT_MODE", "Edge")

if DEPLOYMENT_MODE == "Edge":
    DETECTION_SERVICE_ENDPOINT = "http://detection_service:5000/detect"
else:
    DETECTION_SERVICE_ENDPOINT = "http://56.228.35.90:5003/detect"

def upload_to_cloud(file_paths):
    # Uploading captured images to S3 bucket
    filenames = []

    for file_path in file_paths:
        s3_key = os.path.basename(file_path)
        try:
            s3.upload_file(file_path, S3_BUCKET,s3_key)
            filenames.append(s3_key)

        except FileNotFoundError:
            print("File not found")
        except NoCredentialsError:
            print("Credentials not found")
        
    if DEPLOYMENT_MODE == "Edge":
        image_queue.put(file_paths)
    else:
        image_queue.put(filenames) # Put the images into queue to trigger the cloud 
     

def trigger_detection_service():
    # Trigger Cloud by sending POST request to its endpoint
    while True:
        images = image_queue.get()
        if images:
            try:
                response = requests.post(DETECTION_SERVICE_ENDPOINT, json={"images":images})
                result = response.json()
                print(f"{result}")
                return jsonify({"status": "Done"})

                # if result["results"] == "INTRUDER":
                #     trigger_alert()

            except Exception as e:
                print("Failed",e)
        image_queue.task_done()

@app.route("/upload", methods=["POST"])
def cloud_service_endpoint():
    try:
        data = request.get_json()
        filepaths = data.get("image_paths", [])
    
        if not filepaths:
            return jsonify({"status": "No Image Paths found"})
        
        upload_to_cloud(filepaths)
        return jsonify({"status": "OK", "Files": len(filepaths)}), 200
    
    except Exception as e:
        return jsonify({"status": e}), 500

if __name__ == "__main__":
    threading.Thread(target=trigger_detection_service, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
    