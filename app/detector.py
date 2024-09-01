from ultralytics import YOLO
from dataclasses import dataclass
import torch  

@dataclass
class Detector:
    model: str = None
    
    def __post_init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO("yolov10n.pt")
        self.model.to("cuda")
        self.class_names = self.model.names

    def process_frame(self, frame):
        if frame is None:
            return None

        results = self.model(frame, verbose=False)  

        if not results:
            return None

        detections = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                detection = {
                    "class_id": class_id,
                    "class_name": self.class_names[class_id],
                    "confidence": confidence,
                    "bounding_box": {
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    }
                }

                print(f"{class_id}")

                detections.append(detection)

        return detections
