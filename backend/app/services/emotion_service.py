import cv2
import numpy as np
from deepface import DeepFace


def analyze_emotion(image_bytes: bytes) -> dict:
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("图片解码失败")

    result = DeepFace.analyze(
        img_path=frame,
        actions=["emotion"],
        enforce_detection=False,
        silent=True,
    )
    if isinstance(result, list):
        result = result[0] if result else {}

    scores = result.get("emotion") or {}
    emotion = result.get("dominant_emotion")
    confidence = None
    if emotion and emotion in scores:
        confidence = round(float(scores[emotion]) / 100.0, 4)

    return {
        "emotion": emotion,
        "confidence": confidence,
        "scores": scores,
    }
