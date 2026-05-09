"""
被动活体 + 轻量抗伪造：
- 抗照片：人脸 ROI 微纹理（拉普拉斯方差）、与全图对比，抑制平面打印翻拍。
- 抗视频/屏幕：ROI 内水平方向频谱尖峰（摩尔纹/像素栅格），抑制屏摄与部分视频翻拍。

可通过环境变量关闭或调参：LIVENESS_ENABLE_TEXTURE、LIVENESS_MIN_ROI_LAPLACIAN_VAR 等。
"""

from __future__ import annotations

import os


def _require_cv():
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "MediaPipe/OpenCV 不可用，请先安装 requirements-cv.txt"
        ) from exc
    return cv2, mp, np


def _texture_enabled() -> bool:
    return os.getenv("LIVENESS_ENABLE_TEXTURE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _roi_from_relative_bbox(gray, rel, frame_h: int, frame_w: int, pad_ratio: float = 0.12):
    import numpy as np

    rx = float(getattr(rel, "xmin", getattr(rel, "x_min", 0.0)))
    ry = float(getattr(rel, "ymin", getattr(rel, "y_min", 0.0)))
    rw = float(rel.width)
    rh = float(rel.height)
    x = int(rx * frame_w)
    y = int(ry * frame_h)
    bw = max(1, int(rw * frame_w))
    bh = max(1, int(rh * frame_h))
    pad = int(pad_ratio * max(bw, bh))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(frame_w, x + bw + pad)
    y1 = min(frame_h, y + bh + pad)
    if x1 <= x0 or y1 <= y0:
        return None
    return gray[y0:y1, x0:x1]


def _anti_photo_texture(gray_full, roi_gray) -> tuple[bool, str]:
    """平面照片：人脸块内高频细节往往偏弱或与整图比例异常。"""
    import cv2

    if roi_gray is None or roi_gray.size < 400:
        return True, "ok"
    lap_roi = float(cv2.Laplacian(roi_gray, cv2.CV_64F).var())
    lap_full = float(cv2.Laplacian(gray_full, cv2.CV_64F).var())
    min_roi = float(os.getenv("LIVENESS_MIN_ROI_LAPLACIAN_VAR", "42"))
    if lap_roi < min_roi:
        return False, "人脸区域纹理过弱，疑似照片翻拍"
    # 整图很清晰但人脸块异常平（举手机拍屏幕上的脸）
    if lap_full > 120 and lap_roi < min_roi * 1.35:
        return False, "人脸区域与场景清晰度不一致，疑似伪造画面"
    return True, "ok"


def _anti_screen_periodicity(roi_gray) -> tuple[bool, str]:
    """屏幕/视频：水平方向易出现规则能量峰（摩尔纹、子像素条纹）。"""
    import cv2
    import numpy as np

    if roi_gray is None or roi_gray.size < 900:
        return True, "ok"
    g = cv2.resize(roi_gray, (128, 96), interpolation=cv2.INTER_AREA).astype(np.float32)
    g -= float(g.mean())
    # 沿列做 rFFT，再对行平均 -> 水平空间频率分布
    mag = np.abs(np.fft.rfft(g, axis=1))
    mag = mag[:, 4 : min(64, mag.shape[1])]
    if mag.size < 20:
        return True, "ok"
    row_mean = np.mean(mag, axis=0)
    peak_ratio = float(row_mean.max() / (row_mean.mean() + 1e-6))
    thr = float(os.getenv("LIVENESS_SCREEN_PEAK_RATIO", "6.2"))
    if peak_ratio > thr:
        return False, "检测到屏幕类规则纹理，请正对真人、勿翻拍屏幕"
    return True, "ok"


def _fallback_face_detect(cv2, gray) -> tuple[bool, str]:
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    if len(faces) == 0:
        return False, "未检测到人脸"
    if len(faces) > 1:
        return False, "检测到多张人脸"
    return True, "ok_fallback"


def passive_liveness_check(image_bytes: bytes) -> tuple[bool, str]:
    cv2, mp, np = _require_cv()
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return False, "图片解码失败"

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if brightness < 35:
        return False, "光线过暗"
    if blur < 80:
        return False, "画面过于模糊"

    if not hasattr(mp, "solutions"):
        return _fallback_face_detect(cv2, gray)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = frame.shape[:2]
    with mp.solutions.face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=0.62,
    ) as fd, mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.62,
    ) as mesh:
        detect = fd.process(rgb)
        if not detect.detections:
            return False, "未检测到人脸"
        if len(detect.detections) > 1:
            return False, "检测到多张人脸"

        rel = detect.detections[0].location_data.relative_bounding_box
        roi_gray = _roi_from_relative_bbox(gray, rel, h, w)

        mesh_res = mesh.process(rgb)
        if not mesh_res.multi_face_landmarks:
            return False, "人脸关键点提取失败"
        lm = mesh_res.multi_face_landmarks[0].landmark

        left_eye = lm[33]
        right_eye = lm[263]
        nose = lm[1]
        eye_mid_x = (left_eye.x + right_eye.x) / 2
        yaw = abs(nose.x - eye_mid_x)
        if yaw > 0.08:
            return False, "请正视摄像头"

        if _texture_enabled():
            ok_p, reason_p = _anti_photo_texture(gray, roi_gray)
            if not ok_p:
                return False, reason_p
            ok_s, reason_s = _anti_screen_periodicity(roi_gray)
            if not ok_s:
                return False, reason_s

    return True, "ok"
