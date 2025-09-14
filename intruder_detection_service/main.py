from datetime import datetime
import time
import tflite_runtime.interpreter as tflite
import numpy as np
import threading
import boto3
from botocore.exceptions import NoCredentialsError
from PIL import Image
from queue import Queue
from flask import Flask,request, jsonify
import requests
import os

CLASS_NAMES = ["intruder", "jason"]
CONF_THRESHOLD = 0.25
IOU_THRESHOLD =0.45
IMG_SIZE = 640

interpreter = tflite.Interpreter(model_path="custom_model_saved_model/custom_model_float16.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

mobilenet_interpreter = tflite.Interpreter(model_path="ssd_mobilenet.tflite")
mobilenet_interpreter.allocate_tensors()

mobilenet_input = mobilenet_interpreter.get_input_details()
mobilenet_output = mobilenet_interpreter.get_output_details()

DEPLOYMENT_MODE =os.getenv("DEPLOYMENT_MODE", "Edge")
TRIGGER_ENDPOINT = "http://trigger_service:5000/trigger"
s3 = boto3.client('s3')
S3_BUCKET = "intruder-detection-images"
app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect():
    data = request.get_json()
    image_files =  data.get("images")
    valid_images = []

    detect_start_time = time.time()#T6
    print(f"Detection starting at: {detect_start_time}")


    for image in image_files:
        if DEPLOYMENT_MODE == "Edge":
            # TRIGGER_ENDPOINT = "http://trigger_service:5000/trigger"
            image_path = image
        else:
            # TRIGGER_ENDPOINT = "http://148.252.146.22:5004/trigger"
            image_path = os.path.join("static/images", os.path.basename(image))
            try:
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                s3.download_file(S3_BUCKET, image, image_path)
            except Exception as e:
                print(f"Download error:", e)
                continue
        if detect_person(image_path):
            valid_images.append(image_path)
    
    if valid_images:
        results = [analyse_image(img) for img in valid_images]
        final = max(set(results),key=results.count)
        print("Final Decision: ", final, flush=True)
        detect_end_time = time.time() #T7
        print(f"Detection ending at: {detect_end_time}")

        # if final == "INTRUDER":
        #     try:
        #         response = requests.post(TRIGGER_ENDPOINT,json={"result": final})
        #     except Exception as e:
        #         print("Failed: ", e)
        return jsonify({"results": final})
    else:
        detect_end_time = time.time() #T7
        return jsonify({"results":"No person"})
        

def detect_person(image_path):
    image = Image.open(image_path).resize((300, 300))
    input_data = np.expand_dims(image, axis=0).astype(np.uint8)

    mobilenet_interpreter.set_tensor(mobilenet_input[0]['index'], input_data)
    mobilenet_interpreter.invoke()

    raw_output_data = mobilenet_interpreter.get_tensor(mobilenet_output[0]['index'])

    boxes = mobilenet_interpreter.get_tensor(mobilenet_output[0]['index'])[0]

    scores = mobilenet_interpreter.get_tensor(mobilenet_output[2]['index'])[0]
    classes = mobilenet_interpreter.get_tensor(mobilenet_output[1]['index'])[0]
    number_detections = int(interpreter.get_tensor(mobilenet_output[3]['index'])[0])

    for i in range(len(scores)):
        if scores[i] > CONF_THRESHOLD and int(classes[i]) == 0:
            print("Person detected with scores: ", scores[i])
            return True
    return False

def analyse_image(image_path):

    image = Image.open(image_path).resize((640, 640))
    input_data = np.expand_dims(image, axis=0).astype(np.float32) /255.0

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    raw_output_data = interpreter.get_tensor(output_details[0]['index'])

    out = np.squeeze(raw_output_data)
    nc = out.shape[0] - 4

    boxes_xywh = out[:4, :].T
    class_scores = out[4:, :].T

    img_w, img_h = 640, 640
    scale = np.array([img_w / IMG_SIZE, img_h/IMG_SIZE, img_w / IMG_SIZE, img_h/IMG_SIZE,])
    boxes_xyxy= np.apply_along_axis(_xywh_to_xyxy, 1, boxes_xywh) * scale

    best_scores = class_scores.max(axis=1)
    mask = best_scores >= CONF_THRESHOLD
    boxes_xyxy = boxes_xyxy[mask]
    class_scores = class_scores[mask]

    final_scores_by_class = [0.0] * nc
    for c in range(nc):
        scores_c = class_scores[:, c]
        keep_c = scores_c >= CONF_THRESHOLD
        if not np.any(keep_c):
            continue
        b = boxes_xyxy[keep_c]
        s = scores_c[keep_c]
        keep_idx = _nms(b, s, IOU_THRESHOLD)
        if len(keep_idx):
            final_scores_by_class[c] = float(np.max(s[keep_idx]))

    results = [(CLASS_NAMES[i] if i < len(CLASS_NAMES) else f"class_{i}", final_scores_by_class[i]) for i in range(nc)]

    results = [(n, s) for (n, s) in results if s > 0]
    results.sort(key=lambda x: x[1], reverse=True)

    decision="none"

    if results:
        names = [n for n,_ in results]
        jason_score = dict(results).get("jason", 0.0)
        intruder_score = dict(results).get("intruder", 0.0)

        if intruder_score >= 0.4 and jason_score < 0.70:
            decision = "INTRUDER"
        elif jason_score >= 0.70 and intruder_score < 0.40:
            decision = "JASON"
        elif intruder_score >=0.40 and jason_score >= 0.70:
            decision = "INTRUDER"
        else:
            decision = "INTRUDER"
    
    else:
        decision = "INTRUDER"

    return decision

def _xywh_to_xyxy(xywh):
    x, y, w, h = xywh
    return np.array([x - w/2, y - h/2, x + w/2, y + h/2], dtype=np.float32)

def _box_iou(box, boxes):
    x1 = np.maximum(box[0], boxes[:,0]); y1 = np.maximum(box[1], boxes[:,1]);
    x2 = np.minimum(box[2], boxes[:,2]); y2 = np.minimum(box[3], boxes[:,3]);
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    a = (box[2] - box[0]) * (box[3] - box[1]); b = (boxes[:,2] - boxes[:,0]) * (boxes[:,3] - boxes[:,1])
    return inter / (a + b - inter + 1e-6)

def _nms(boxes, scores, iou_thres):
    keep =[]
    idxs = np.argsort(scores)[::-1]
    while idxs.size:
        i = idxs[0]; keep.append(i)
        if idxs.size == 1: break
        iou = _box_iou(boxes[i], boxes[idxs[1:]])
        idxs = idxs[1:][iou < iou_thres]
    return keep

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

