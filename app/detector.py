from ultralytics import YOLO
from dataclasses import dataclass
import cv2, json
import numpy as np

@dataclass
class Detector:
    model: str = None

    def __post_init__(self):
        self.model = YOLO("yolov8n.pt")

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
                confidence = float(box.conf[0])

                detection = {
                    "class_id": class_id,
                    "confidence": confidence,
                    "bounding_box": {
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    }
                }

                detections.append(detection)
        
                # print(f"Sınıf: {class_id}, Güven: {confidence:.2f}, Bounding Box: x1={x1:.0f}, y1={y1:.0f}, x2={x2:.0f}, y2={y2:.0f}")

        processed_frame = results[0].plot()

        if processed_frame is None:
            return None

        return processed_frame, detections

    # def generate_frames(self, frame):
    #     processed_frame, detections = self.process_frame(frame)
    #     if processed_frame is None:
    #         return
        
    #     success, buffer = cv2.imencode(".jpg", processed_frame)
    #     if not success:
    #         return
    #     frame_bytes = buffer.tobytes()
        

    #     json_data = json.dumps(detections)
    #     yield (
    #         b"--frame\r\n"
    #         b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
    #     )
