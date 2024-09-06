from ultralytics import YOLO
from dataclasses import dataclass
import torch

@dataclass
class Detector:
    use_cuda: bool
    model: str = None
    filter_classes: list = None  # Filtreleme için sınıf ID'leri
    
    def __post_init__(self):
        if self.use_cuda and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        print(torch.cuda.is_available())
        
        self.model = YOLO("modules/yolov10s.pt")
        self.model.to(self.device)
        self.class_names = self.model.names

    def process_frame(self, frame):
        if frame is None:
            return None

        height, width = frame.shape[:2]

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

                # Sınıf ID'lerine göre filtreleme
                if self.filter_classes is None or class_id in self.filter_classes:
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
                    detections.append(detection)

        return detections, width, height
