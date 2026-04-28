"""合照：多人脸检测 + DeepFace embedding 与学生库比对。"""

from __future__ import annotations

from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.models.student import Student
from app.services.face_service import cosine_distance, deserialize_embedding, extract_face_embedding

MATCH_THRESHOLD = 0.35


def _detect_face_crops_bgr(img_bgr: np.ndarray):
    import cv2

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if cascade.empty():
        return []
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=4,
        minSize=(48, 48),
    )
    crops = []
    for (x, y, w, h) in faces:
        pad = int(min(w, h) * 0.08)
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(img_bgr.shape[1], x + w + pad)
        y1 = min(img_bgr.shape[0], y + h + pad)
        crops.append(img_bgr[y0:y1, x0:x1])
    return crops


def _embedding_from_crop_bgr(crop_bgr: np.ndarray) -> list[float]:
    import cv2

    ok, buf = cv2.imencode(".jpg", crop_bgr)
    if not ok:
        raise ValueError("人脸区域编码失败")
    return extract_face_embedding(buf.tobytes())


def match_group_photo_faces(db: Session, image_bytes: bytes) -> tuple[list[dict[str, Any]], int]:
    import cv2

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("图片解码失败")

    crops = _detect_face_crops_bgr(img)
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

        best: Student | None = None
        best_dist = 1.0
        for s in students:
            emb = deserialize_embedding(s.face_encoding)
            if not emb:
                continue
            dist = cosine_distance(probe, emb)
            if dist < best_dist:
                best_dist = dist
                best = s

        if best and best_dist <= MATCH_THRESHOLD:
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
