from ultralytics import YOLO
from dataclasses import dataclass
import cv2, json
import numpy as np

@dataclass
class Detector:
    model: str = None

    def __post_init__(self):
        self.model = YOLO("yolov8n.pt")
        self.class_names = self.model.names
    def process_frame(self, frame):
        if frame is None:
            return None

        results = self.model(frame, verbose=False)
        
        if results is None or len(results) == 0:
            return None
        
        detections = []

        for result in results:
            boxes = result.boxes
            for box in boxes:

                x1,y1,x2,y2 = box.xyxy[0]
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                confidence = float(box.conf[0])

                detection = {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "bounding_box": {
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    }
                }

                detections.append(detection)

        processed_frame = results[0].plot()

        if processed_frame is None:
            return None

        return processed_frame, detections
