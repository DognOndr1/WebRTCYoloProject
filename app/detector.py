from ultralytics import YOLO
from dataclasses import dataclass
from typing import Any

@dataclass
class Detector:
    use_cuda: bool
    model: Any = None
    
    def __post_init__(self):
        self.model = YOLO("yolov8n.pt")
        if self.use_cuda:
            print("CUDA'ya erişim var")
            self.model.to('cuda')
        else:
            print("CUDA'ya erişim yok")
            self.model.to('cpu')

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
                x1, y1, x2, y2 = box.xyxy[0]
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

        processed_frame = results[0].plot()

        if processed_frame is None:
            return None

        return processed_frame




