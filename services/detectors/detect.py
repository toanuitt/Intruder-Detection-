import cv2
import numpy as np
from ultralytics import YOLO
from services.trackers.deep_sort import DeepSortWrapper

class IntruderDetector():
    def __init__(self, model_paths, conf_thresh=0.5, iou_tracking=0.5):
        """
        Parameters:
        model_path: path to YOLO-v8 model
        conf_thresh: confident threshold for model prediction
        """
        self.models = dict()
        for model_name in model_paths.keys():
            self.models[model_name] = YOLO(model_paths[model_name])
        self.conf_threshold = conf_thresh
        self.iou_tracking = iou_tracking
        self.classes = 0
        self.tracker = DeepSortWrapper(max_age= 30, n_init= 3)

    def load_model(self, model_path):
        self.model = YOLO(model_path)

    def transform_yolo_prediction(self, predicts):
        detections = []
        for predict in predicts:
            bboxes = predict.boxes.xyxy.numpy()
            labels = predict.boxes.cls.numpy()
            for bbox, label in zip(bboxes, labels):
                x1, y1, x2, y2 = map(int, bbox)
                bbox = (x1, y1, x2 - x1, y2 - y1)
                detections.append((bbox, label))
        return detections
        
    # detect people using YOLO-v8
    def predict(self, img, tracker, verbose= False):
        if tracker == "YOLO":
            person_predicts = self.models["yolov8n"].track(img, classes=self.classes, conf=self.conf_threshold, 
                                    iou=self.iou_tracking, verbose= verbose, persist= True)
            results = self.transform_yolo_prediction(person_predicts)
        elif tracker == "DEEPSORT":
            person_predicts = self.models["yolov5mu"].predict(img, classes=self.classes, conf=self.conf_threshold, verbose= verbose)
            person_bboxes = self.transform_yolo_prediction(person_predicts)
            tracks = self.tracker.update_tracker(person_bboxes, img)
            print(len(person_bboxes), len(tracks))
            results = []
            for track in tracks:
                if not track.is_confirmed() or track.time_since_update > 1:
                    continue
                results.append([list(map(int, track.to_ltrb())), 0])
            
        return results
                
    def isInside(self, contour, corr):
        return cv2.pointPolygonTest(contour, corr, False) == 1

    def detect(self, img, polygon, tracker):
        polygon = np.array(polygon).reshape(-1, 1, 2)
        bboxes = self.predict(img, tracker)
        img = cv2.polylines(img, [polygon], True, (0,255,0), 3)
        
        current_count = 0
        for bbox, label in bboxes:
            xA, yA, w, h = bbox

            corr = (int(w/2), yA+h)
            
            if self.isInside(polygon, corr):
                color = (0,0,255)
                current_count += 1
            else:
                color = (255,0,0) 
            
            cv2.rectangle(img, (xA,yA), (xA + w, yA + h), color, 3)
            
        return img, current_count
            