"""合照：缩小分辨率 + Haar 检脸 + 阈值/间隔比对；避免整图 MTCNN 卡死。"""

from __future__ import annotations

import os
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.models.student import Student
from app.services.face_service import (
    cosine_distance,
    deepface_module,
    deserialize_embedding,
    extract_face_embedding,
    represent_aligned_face_bgr,
)
from app.services.match_quality import (
    group_face_match_min_margin,
    group_face_match_threshold,
    pick_match_by_margin,
)


def match_threshold_used() -> float:
    return group_face_match_threshold()


def _max_long_side() -> int:
    return max(640, min(4096, int(os.getenv("GROUP_PHOTO_MAX_SIDE", "1600"))))


def _max_face_crops() -> int:
    return max(1, min(200, int(os.getenv("GROUP_MAX_FACE_CROPS", "48"))))


def _downscale_image_bgr(img_bgr: np.ndarray, max_side: int) -> np.ndarray:
    import cv2

    h, w = img_bgr.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return img_bgr
    scale = max_side / m
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA)


def _detector_backends_slow() -> tuple[str, ...]:
    raw = os.getenv("DEEPFACE_GROUP_DETECTOR_BACKEND", "").strip()
    if raw:
        return tuple(b.strip() for b in raw.split(",") if b.strip())
    return ("opencv",)


def _face_rgb_to_bgr_uint8(face: np.ndarray) -> np.ndarray:
    if face.dtype != np.uint8:
        face = (
            np.clip(face * 255.0, 0, 255).astype(np.uint8)
            if face.size and float(face.max()) <= 1.0 + 1e-6
            else face.astype(np.uint8)
        )
    if face.ndim == 2:
        face = np.stack([face] * 3, axis=-1)
    if face.shape[-1] == 4:
        face = face[:, :, :3]
    return face[:, :, ::-1].copy()


def _detect_face_crops_bgr_haar(img_bgr: np.ndarray) -> list[np.ndarray]:
    import cv2

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if cascade.empty():
        return []
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=4,
        minSize=(40, 40),
    )
    crops = []
    for (x, y, w, h) in faces:
        pad = int(min(w, h) * 0.1)
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(img_bgr.shape[1], x + w + pad)
        y1 = min(img_bgr.shape[0], y + h + pad)
        crops.append(img_bgr[y0:y1, x0:x1])
    return crops


def _face_crops_deepface_fallback(img_bgr: np.ndarray) -> list[np.ndarray]:
    DeepFace = deepface_module()
    min_conf = float(os.getenv("GROUP_FACE_MIN_CONFIDENCE", "0.75"))
    crops: list[np.ndarray] = []
    for backend in _detector_backends_slow():
        try:
            faces = DeepFace.extract_faces(
                img_path=img_bgr,
                detector_backend=backend,
                enforce_detection=False,
                align=True,
            )
        except Exception:
            continue
        for item in faces:
            if not isinstance(item, dict):
                continue
            if float(item.get("confidence") or 1.0) < min_conf:
                continue
            face = item.get("face")
            if face is None or not isinstance(face, np.ndarray):
                continue
            crops.append(_face_rgb_to_bgr_uint8(face))
        if crops:
            break
    return crops


def _face_crops_from_image(img_bgr: np.ndarray) -> list[np.ndarray]:
    crops = _detect_face_crops_bgr_haar(img_bgr)
    if crops:
        return crops[: _max_face_crops()]
    return _face_crops_deepface_fallback(img_bgr)[: _max_face_crops()]


def _embedding_from_crop_bgr(crop_bgr: np.ndarray) -> list[float]:
    try:
        return represent_aligned_face_bgr(crop_bgr)
    except Exception:
        import cv2

        ok, buf = cv2.imencode(".jpg", crop_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            raise ValueError("人脸区域编码失败") from None
        return extract_face_embedding(buf.tobytes(), detector_backends=("opencv",))


def match_group_photo_faces(db: Session, image_bytes: bytes) -> tuple[list[dict[str, Any]], int]:
    import cv2

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("图片解码失败")

    img = _downscale_image_bgr(img, _max_long_side())
    crops = _face_crops_from_image(img)
    if not crops:
        return [], 0

    students = db.query(Student).filter(Student.face_encoding.isnot(None)).all()
    matches: list[dict[str, Any]] = []
    seen_sid: set[str] = set()

    for crop in crops:
        try:
            probe = _embedding_from_crop_bgr(crop)
        except Exception:
            continue

        scored: list[tuple[Student, float]] = []
        for s in students:
            emb = deserialize_embedding(s.face_encoding)
            if not emb:
                continue
            scored.append((s, cosine_distance(probe, emb)))

        best, best_dist, reason = pick_match_by_margin(
            scored,
            threshold=group_face_match_threshold(),
            min_margin=group_face_match_min_margin(),
        )
        if reason != "ok" or best is None:
            continue

        sid = best.student_id
        if sid in seen_sid:
            continue
        seen_sid.add(sid)
        matches.append(
            {
                "student_no": best.student_id,
                "student_name": best.name,
                "confidence": round(max(0.0, 1.0 - best_dist), 4),
            }
        )

    return matches, len(crops)
