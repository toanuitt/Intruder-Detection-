import cv2
import numpy as np
from ultralytics import YOLO

# find if a point is inside a polygon

class YoloDetect():
    def __init__(self, model_path, conf_thresh=0.5):
        """
        Parameters:
        model_path: path to YOLO-v8 model
        conf_thresh: confident threshold for model prediction
        """
        self.model = YOLO(model_path) # load model
        self.conf_threshold = conf_thresh # confidence threshold
        self.count = 0 # count number of people inside the zone 
        self.classes = 0 # class index of 'people' for YOLO
        
    # detect people using YOLO-v8
    def predict(self, img):
        return self.model.predict(img, classes=self.classes, conf=self.conf_threshold)
    
    # give warning with given condition
    def warn(self, curr):
        if curr == 0:
            if self.count != curr:
                print("Only person left!")
        else:
            if self.count > curr:
                print("New person in!")
            elif self.count < curr:
                print("One person out!")

    def isInside(contour, corr):
        return True if cv2.pointPolygonTest(contour, corr, False) == 1 else False

    # run function
    def detect(self, img, polygon):
        results = self.predict(img)
        img = cv2.polylines(img, polygon, True, (0,255,0), 3)
        
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
            
        # give warning message and update counter
        self.warn(current_count)
        self.count = current_count
            
        return img
            