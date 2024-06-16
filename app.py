from flask import Flask, render_template, request, jsonify
import base64
import os
import numpy as np
import cv2
from services.detectors.detect import YoloDetect
import datetime
import json

# Create flask app
app = Flask(__name__)

# Add app routes
with open("config.json", "r") as f:
    config = json.load(f)
cap = cv2.VideoCapture(config['cam_idx'])
yo = YoloDetect(model_path=config['model_path'], poly=config['poly'], video_cap=cap, conf_thresh=config['conf_thresh'])

@app.route('/')
def application():
    return render_template('index.html')
polygon_coords = []


def isInside(polygon, point):
    # This function checks if a point is inside a polygon using the ray-casting algorithm
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

@app.route('/_set_polygon', methods=['POST'])
def set_polygon():
    global polygon_coords
    data = request.get_json()
    polygon_coords = data['polygon']
    return jsonify(response="Polygon set successfully")

@app.route('/_photo_cap', methods=['POST'])
def photo_cap():
    response = "Unknown error"
    data = ""
    count =0
    def warn(curr):
        if curr == 0:
            if count != curr:
                data = "Only person left!"
        else:
            if count > curr:
                data = "New person in!"
            elif count < curr:
                data = "One person out!"
    try:
        photo_base64 = request.form.get('photo_cap')
        header, encoded = photo_base64.split(",", 1)
        binary_data = base64.b64decode(encoded)
        
        # Convert binary data to numpy array for processing with OpenCV
        nparr = np.frombuffer(binary_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert BGR (OpenCV format) to RGB 
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        global polygon_coords
        if polygon_coords:
            cv2.polylines(rgb_image, [np.array(polygon_coords, np.int32)], True, (0, 255, 0), 3)
        img = yo.predict(rgb_image)

        if (img):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = f"photo_{timestamp}.jpeg"
            image_path = os.path.join("static", image_name)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            # Process results and draw polygons
            current_count = 0
            for result in img:
                for box in result.boxes:
                    xA, yA, xB, yB = map(int, box.xyxy[0])
                    corr = (int((xA + xB) / 2), yB)
                    if isInside(polygon_coords, corr):
                        color = (0, 0, 255)
                        current_count += 1
                    else:
                        color = (255, 0, 0)
                    cv2.rectangle(image, (xA, yA), (xB, yB), color, 3)
            warn(current_count)
            cv2.polylines(image, [np.array(polygon_coords, np.int32)], True, (0, 255, 0), 3)
            cv2.imwrite(image_path, image)

    except Exception as e:
        response = str(e)

    return jsonify({'message': data})

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

if __name__ == "__main__":
    app.run()