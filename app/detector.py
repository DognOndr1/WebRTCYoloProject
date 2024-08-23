from ultralytics import YOLO
from dataclasses import dataclass
import cv2
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

        processed_frame = results[0].plot()

        if processed_frame is None:
            return None

        return processed_frame

    def generate_frames(self, frame):
        processed_frame = self.process_frame(frame)
        if processed_frame is None:
            return
        
        success, buffer = cv2.imencode(".jpg", processed_frame)
        if not success:
            return
        
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )



