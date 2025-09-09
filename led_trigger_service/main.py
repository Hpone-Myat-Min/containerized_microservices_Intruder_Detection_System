from rgbmatrix5x5 import RGBMatrix5x5
from flask import Flask, request, jsonify
import time

rgbmatrix = RGBMatrix5x5()
app = Flask(__name__)

@app.route("/trigger", methods=["POST"])
def trigger_alert():

    data = request.get_json()
    result = data.get("result")
    if not data or data.get("result") != "INTRUDER":
        return jsonify({"message": "Pass"}), 400
    
    rgbmatrix = RGBMatrix5x5()
    rgbmatrix.set_all(255, 0, 0)
    rgbmatrix.show()

    time.sleep(10)
    rgbmatrix.clear()
    rgbmatrix.show()

    return jsonify({"message": "LED Trigger"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
