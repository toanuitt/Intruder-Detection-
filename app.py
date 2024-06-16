from flask import Flask, render_template, request, jsonify
import base64
import os
import numpy as np
import cv2
from services.detectors.detect import YoloDetect
import datetime
import json

# global var
polygon_coords = []
with open("config.json", "r") as f:
    config = json.load(f)
detector = YoloDetect(model_path=config['model_path'], conf_thresh=config['conf_thresh'])

# Create flask app
app = Flask(__name__)

# Add app routes
@app.route('/')
def application():
    return render_template('index.html')

@app.route('/_send_polygon', methods=['POST'])
def receive_polygon():
    global polygon_coords
    try:
        data = request.get_json()
        polygon_coords = data['points']
        response = {'message': 'Polygon coordinates received successfully'}
    except Exception as e:
        response = {'error': str(e)}
    
    return jsonify(response)

@app.route('/_photo_cap', methods=['POST'])
def photo_cap():
    response = "Unknown error"
    data = ""
    try:
        photo_base64 = request.form.get('photo_cap')
        header, encoded = photo_base64.split(",", 1)
        binary_data = base64.b64decode(encoded)
        
        # Convert binary data to numpy array for processing with OpenCV
        nparr = np.frombuffer(binary_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        global polygon_coords

        if rgb_image and polygon_coords:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = f"photo_{timestamp}.jpeg"
            image_path = os.path.join("static", image_name)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            result = detector.detect(rgb_image, polygon_coords)

    except Exception as e:
        response = str(e)

    return jsonify({'message': data})

if __name__ == "__main__":
    app.run()