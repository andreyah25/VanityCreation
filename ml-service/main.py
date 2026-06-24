from fastapi import FastAPI
from pydantic import BaseModel
from ultralytics import YOLO
import cv2
import requests
import numpy as np

app = FastAPI()

model = YOLO("yolov8n.pt")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

class ImageRequest(BaseModel):
    image_url: str


@app.get("/")
def home():
    return {
        "status": "running",
        "service": "Auto Tagging ML Service"
    }


@app.post("/detect")
def detect(request: ImageRequest):

    try:
        # Download image
        response = requests.get(request.image_url, timeout=10)

        if response.status_code != 200:
            return {"error": "Failed to download image"}

        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return {"error": "Invalid image format"}

        # --------------------
        # OBJECT DETECTION
        # --------------------
        results = model(image)
        result = results[0]

        detected_objects = []

        for box in result.boxes:
            if box.conf[0] > 0.5:
                class_id = int(box.cls[0])
                label = model.names[class_id]

                if label not in detected_objects:
                    detected_objects.append(label)

        # --------------------
        # FACE DETECTION
        # --------------------
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5
        )

        face_count = len(faces)

        # --------------------
        # TAGGING
        # --------------------
        tags = detected_objects.copy()

        if face_count > 0:
            tags.append("portrait")

        if face_count > 1:
            tags.append("group-photo")

        return {
            "faces_detected": face_count,
            "objects": detected_objects,
            "tags": list(set(tags))
        }

    except Exception as e:
        return {"error": str(e)}