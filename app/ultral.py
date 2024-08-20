from ultralytics import YOLO

model = YOLO("yolov8n.yaml").load("yolov8n.pt")

results = model.track(source=0, show=True, tracker="bytetrack.yaml", verbose=False)
