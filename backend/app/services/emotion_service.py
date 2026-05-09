from deepface import DeepFace

from app.services.face_service import decode_upload_bgr_for_deepface


def analyze_emotion(image_bytes: bytes) -> dict:
    frame = decode_upload_bgr_for_deepface(image_bytes)

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
