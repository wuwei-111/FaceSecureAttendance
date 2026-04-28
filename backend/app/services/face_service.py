import json
from typing import Iterable


def _require_deepface():
    try:
        from deepface import DeepFace
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "DeepFace 未安装或不可用，请先安装 requirements-cv.txt"
        ) from exc
    return DeepFace


def extract_face_embedding(image_bytes: bytes) -> list[float]:
    # DeepFace 仅接受 str（路径/URL）或 numpy 数组，不能直接传 bytes。
    try:
        import cv2
        import numpy as np
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "OpenCV / NumPy 不可用，请先安装 requirements-cv.txt"
        ) from exc

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("图片解码失败")

    deepface = _require_deepface()
    reps = deepface.represent(
        img_path=img,
        model_name="Facenet512",
        detector_backend="opencv",
        enforce_detection=True,
    )
    if not reps:
        raise ValueError("未检测到人脸")
    emb = reps[0].get("embedding")
    if not emb:
        raise ValueError("人脸特征提取失败")
    return [float(x) for x in emb]


def serialize_embedding(embedding: Iterable[float]) -> bytes:
    return json.dumps(list(embedding), separators=(",", ":")).encode("utf-8")


def deserialize_embedding(blob: bytes | None) -> list[float] | None:
    if not blob:
        return None
    try:
        arr = json.loads(blob.decode("utf-8"))
        return [float(x) for x in arr]
    except Exception:
        return None


def cosine_distance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 1.0
    cos = dot / (na * nb)
    cos = max(-1.0, min(1.0, cos))
    return 1.0 - cos

