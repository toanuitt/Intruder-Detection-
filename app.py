from flask import Flask, render_template, request, jsonify, Response
import os, io
import numpy as np
import cv2
from services.detectors.detect import IntruderDetector
from datetime import datetime, timedelta
import json

# global var
video_stream = None
intruder_count = 0
intruder_list = []
polygon_coords = None
choice = "YOLO"


with open("./assets/configs/config.json", "r") as f:
    config = json.load(f)
detector = IntruderDetector(config['model_paths'], conf_thresh=config['conf_thresh'])

# Create flask app
app = Flask(__name__)

# Add app routes
@app.route('/')
def application():
    return render_template('index.html')

@app.get("/_get_intruder_count")
def get_intruder_count():
    return jsonify({"intruder_count": intruder_count})

@app.get("/_get_intruder_list")
def get_intruder_list():
    last_ten_intruder_list = intruder_list[-10:]
    results = []
    for i in range(-len(last_ten_intruder_list) + 1, 0, 1):
        info = last_ten_intruder_list[i]
        results.append(f"Time: {info[0]}, No. Intruder: {info[1]}")
    return jsonify({"intruder_list": results})

def parseInput(input): 
    if len(input) == 1:
        return int(input)
    return input

@app.route('/_send_camera_ip', methods=['POST'])
def send_value():
    global video_stream, intruder_list
    try:
        if video_stream is not None:
            video_stream.release()
            intruder_list = []

        data = request.get_json()
        ip_value = data.get('camera_ip')
        input = parseInput(ip_value)
        video_stream = cv2.VideoCapture(input)
        ret, _ = video_stream.read()
        if ret:
            response = {'action': 'access_camera_success'}
        else:
            response = {'action': 'not_found'}
    except Exception as e:
        response = {'error': str(e)}
    
    return jsonify(response)

@app.route('/_submit_model_choice', methods=['POST'])
def submit_choice():
    global choice
    try:
        data = request.json
        print(choice)
        choice = data.get('choice')
        print(choice)
        res = {'status': 'success', 'choice': choice}
    except Exception as e:
        res = {"status": "failed", "error": str(e)}
    return jsonify(res)

def parse_json_poly(jsonPoly):
    polygon = [[point["x"], point["y"]] for point in jsonPoly]
    return polygon

@app.route('/_send_polygon', methods=['POST'])
def receive_polygon():
    global polygon_coords
    try:
        data = request.get_json()
        polygon_coords = parse_json_poly(data.get("polygon"))
        
        response = {'message': 'Polygon coordinates received successfully'}
    except Exception as e:
        response = {'error': str(e)}
    
    return jsonify(response)

@app.route("/_reset_polygon", methods=['POST'])
def reset_polygon():
    global polygon_coords, intruder_count
    try:
        data = request.get_json()
        if data.get("reset"):
            polygon_coords = []
            intruder_count = 0
        
        res = {"message": "Reset successfully"}
    except Exception as e:
        res = {"error": str(e)}
    
    return jsonify(res)
    
def img_tobyte(img, type= ".jpg"):
    _, buffer = cv2.imencode(type, img)
    img_bytes = buffer.tobytes()
    return img_bytes

def update_list(time_list, time, count):
    if len(time_list) == 0:
        time_list.append([time, count])
        return
    
    time_range = time - time_list[-1][0]
    if time_range.total_seconds() > 2:
        time_list.append([time, count])
            

def generate():
    global video_stream, intruder_count, intruder_list
    while video_stream:
        success, frame = video_stream.read()  # read the camera frame
        if not success:
            print("Stream has been ended!")
            video_stream.release()
            break
        else:
            result_frame = img_tobyte(frame)
            
            if polygon_coords is not None and len(polygon_coords)>2:
                result_frame, intruder_count = detector.detect(frame, polygon_coords, choice)
                if intruder_count > 0:
                    update_list(intruder_list, datetime.now(), intruder_count)
                result_frame = img_tobyte(result_frame)

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + result_frame + b'\r\n')

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host= "0.0.0.0")