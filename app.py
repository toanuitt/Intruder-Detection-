from flask import Flask, render_template, request, jsonify, Response
import os, io
import numpy as np
import cv2
from services.detectors.detect import YoloDetect
import datetime
import json

# global var
video_stream = None
intruder_count = 0
polygon_coords = np.array([[210,350], [1010,490], [900,1080], [0,1080], [0,520]], np.int32).reshape(-1, 1, 2)
first_frame = None
default_first_frame = cv2.imread("./static/images/default_first_frame.png")


with open("./assets/configs/config.json", "r") as f:
    config = json.load(f)
detector = YoloDetect(model_path=config['model_path'], conf_thresh=config['conf_thresh'])

# Create flask app
app = Flask(__name__)

# Add app routes
@app.route('/')
def application():
    return render_template('index.html')

def parseInput(input): 
    if len(input) == 1:
        return int(input)
    return input

@app.route('/_send_camera_ip', methods=['POST'])
def send_value():
    global video_stream
    try:
        if video_stream is not None:
            video_stream.release()

        data = request.get_json()
        ip_value = data.get('value')
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
    
def img_tobyte(img, type= ".jpg"):
    _, buffer = cv2.imencode(type, img)
    img_bytes = buffer.tobytes()
    return img_bytes

def generate():
    global video_stream, intruder_count, first_frame
    while video_stream:
        success, frame = video_stream.read()  # read the camera frame
        if not success:
            print("Stream has been ended!")
            break
        else:
            if first_frame is None:
                first_frame = img_tobyte(frame)

            result_frame, intruder_count = detector.detect(frame, polygon_coords, "YOLO")
            frame = img_tobyte(result_frame)
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
def first_take():
    global first_frame, default_first_frame
    while True:
        if first_frame is not None:
            result = (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + first_frame + b'\r\n')
        else:
            default_first_frame_byte = img_tobyte(default_first_frame)
            result = (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + default_first_frame_byte + b'\r\n')
        yield result
    
@app.route("/first_image")
def first_image():
    return Response(first_take(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host= "0.0.0.0")