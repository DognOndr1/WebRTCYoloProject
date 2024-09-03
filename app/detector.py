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
        
        processed_frame = results[0].plot()

        return processed_frame
