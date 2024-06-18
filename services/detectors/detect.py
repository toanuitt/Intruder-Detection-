import cv2
import numpy as np
from ultralytics import YOLO
# from services.trackers import DeepSortWrapper

class YoloDetect():
    def __init__(self, model_path, conf_thresh=0.5, iou_tracking=0.5):
        """
        Parameters:
        model_path: path to YOLO-v8 model
        conf_thresh: confident threshold for model prediction
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_thresh
        self.iou_tracking = iou_tracking
        self.classes = 0
        # self.tracker = DeepSortWrapper(max_age= 30, n_init= 3)

    def load_model(self, model_path):
        self.model = YOLO(model_path)
        
    # detect people using YOLO-v8
    def predict(self, img, tracker, verbose= False):
        if tracker == "YOLO":
            return self.model.track(img, classes=self.classes, conf=self.conf_threshold, 
                                    iou=self.iou_tracking, verbose= verbose, persist= True)
        elif tracker == "DEEPSORT":
            self.model.predict(img, classes=self.classes, conf=self.conf_threshold, verbose= verbose)
            tracks = self.tracker.update_tracks(img, )    
        else:
            return self.model.predict(img, classes=self.classes, conf=self.conf_threshold, verbose= verbose)
    
    def isInside(self, contour, corr):
        return cv2.pointPolygonTest(contour, corr, False) == 1

    def detect(self, img, polygon, isTrack):
        results = self.predict(img, isTrack)
        img = cv2.polylines(img, [polygon], True, (0,255,0), 3)
        
        current_count = 0
        for result in results:
            for box in result.boxes:
                xA, yA, xB, yB = map(int, box.xyxy[0]) 

                corr = (int((xA+xB)/2), yB)
                
                if self.isInside(polygon, corr): 
                    color = (0,0,255)
                    current_count += 1
                else: 
                    color = (255,0,0) 
                
                cv2.rectangle(img, (xA,yA), (xB,yB), color, 3)
            
        return img, current_count
            