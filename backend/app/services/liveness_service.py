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
    with mp.solutions.face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=0.6,
    ) as fd, mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.6,
    ) as mesh:
        detect = fd.process(rgb)
        if not detect.detections:
            return False, "未检测到人脸"
        if len(detect.detections) > 1:
            return False, "检测到多张人脸"

        mesh_res = mesh.process(rgb)
        if not mesh_res.multi_face_landmarks:
            return False, "人脸关键点提取失败"
        lm = mesh_res.multi_face_landmarks[0].landmark

        # 用眼角和鼻尖粗判偏转，避免明显平面翻拍
        left_eye = lm[33]
        right_eye = lm[263]
        nose = lm[1]
        eye_mid_x = (left_eye.x + right_eye.x) / 2
        yaw = abs(nose.x - eye_mid_x)
        if yaw > 0.08:
            return False, "请正视摄像头"

    return True, "ok"

