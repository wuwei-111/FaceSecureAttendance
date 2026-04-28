# Day1 问题排查与修复记录（2026-04-27）

本文仅记录本次联调中与 `mediapipe.solutions` 相关的问题与修复。

## 1. 截帧上传报错的核心问题

### 现象

- 前端可打开摄像头，但截帧上传常失败。
- 后端 `POST /api/attendance/checkin` 返回 `500` 或 `503`。
- 关键报错：`AttributeError: module 'mediapipe' has no attribute 'solutions'`。

### 结论

- 不是“功能没做”，也不是“未安装依赖”这么简单。
- 当前环境里的 `mediapipe` 虽已安装，但运行时不暴露 `solutions` 接口，导致原活体检测路径不可用。

## 2. 已实施修复

文件：`backend/app/services/liveness_service.py`

- 增加 `mediapipe.solutions` 可用性判断。
- 当 `solutions` 不可用时，自动降级到 OpenCV Haar 人脸检测（fallback），避免接口直接崩溃。
- fallback 处理规则：
  - 无人脸 -> `未检测到人脸`
  - 多人脸 -> `检测到多张人脸`
  - 单人脸 -> `ok_fallback`

## 3. 修复后效果

- 服务不再因为 `mediapipe.solutions` 缺失而 500。
- 前端可以获得可解释的业务结果，不再是无意义的网络错误。

## 4. 当前限制与后续计划

- OpenCV fallback 稳定性低于 MediaPipe，复杂场景下误判率会更高。
- 后续优化方向：
  1. 优先恢复可用的 MediaPipe 标准检测路径。
  2. 前端增加取景引导（人脸位置、距离、光照提示）。
  3. fallback 增加小框/边缘框过滤，减少“误判多脸”。
