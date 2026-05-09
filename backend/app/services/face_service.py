import json
import os
from typing import Iterable

import numpy as np


def _require_deepface():
    try:
        from deepface import DeepFace
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "DeepFace 未安装或不可用，请先安装 requirements-cv.txt"
        ) from exc
    return DeepFace


def deepface_module():
    return _require_deepface()


def _detector_backends() -> tuple[str, ...]:
    raw = os.getenv("DEEPFACE_DETECTOR_BACKEND", "").strip()
    if raw:
        return tuple(b.strip() for b in raw.split(",") if b.strip())
    return ("mtcnn", "retinaface", "opencv")


def _decode_bgr(image_bytes: bytes) -> np.ndarray:
    try:
        import cv2
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "OpenCV / NumPy 不可用，请先安装 requirements-cv.txt"
        ) from exc
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("图片解码失败")
    return img


def _embed_max_side_px() -> int:
    """送入检测器前的最长边上限；高分辨率原图会导致 MTCNN/RetinaFace 内存与 CPU 激增。"""
    raw = os.getenv("FACE_EMBED_MAX_SIDE", "1024").strip()
    try:
        n = int(raw)
    except ValueError:
        return 1024
    return n if n > 0 else 1024


def downscale_bgr_max_side(img: np.ndarray, max_side: int) -> np.ndarray:
    """保持宽高比缩小（INTER_AREA）；供 DeepFace / MediaPipe 等共用，避免千万级像素拖垮进程。"""
    if max_side <= 0:
        return img
    import cv2

    h, w = img.shape[:2]
    side = max(h, w)
    if side <= max_side:
        return img
    scale = max_side / float(side)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)


def decode_upload_bgr_for_deepface(image_bytes: bytes) -> np.ndarray:
    """解码上传图并按 FACE_EMBED_MAX_SIDE 缩小，再送入 DeepFace（特征 / 情绪）。"""
    img = _decode_bgr(image_bytes)
    return downscale_bgr_max_side(img, _embed_max_side_px())


def extract_face_embedding(
    image_bytes: bytes,
    *,
    detector_backends: tuple[str, ...] | None = None,
) -> list[float]:
    """整图人脸特征；默认可多检测器回退以提高准确率。"""
    img = decode_upload_bgr_for_deepface(image_bytes)
    deepface = _require_deepface()
    backends = detector_backends if detector_backends is not None else _detector_backends()
    last_err: Exception | None = None
    for backend in backends:
        try:
            reps = deepface.represent(
                img_path=img,
                model_name="Facenet512",
                detector_backend=backend,
                enforce_detection=True,
            )
            if not reps:
                continue
            emb = reps[0].get("embedding")
            if not emb:
                continue
            return [float(x) for x in emb]
        except Exception as exc:
            last_err = exc
            continue
    if last_err:
        raise ValueError("未检测到人脸或特征提取失败") from last_err
    raise ValueError("未检测到人脸或特征提取失败")


def represent_aligned_face_bgr(face_bgr: np.ndarray) -> list[float]:
    """已对齐人脸小图：优先 skip 检测，失败则仅用 opencv 整图提取。"""
    deepface = _require_deepface()
    try:
        reps = deepface.represent(
            img_path=face_bgr,
            model_name="Facenet512",
            detector_backend="skip",
            enforce_detection=False,
        )
        if reps:
            emb = reps[0].get("embedding")
            if emb:
                return [float(x) for x in emb]
    except Exception:
        pass
    try:
        import cv2

        ok, buf = cv2.imencode(".jpg", face_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            raise ValueError("人脸区域编码失败")
        return extract_face_embedding(buf.tobytes(), detector_backends=("opencv",))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("人脸特征提取失败") from exc


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
