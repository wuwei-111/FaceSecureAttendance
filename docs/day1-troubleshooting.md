# Day1 问题排查与修复记录（2026-04-27）

本文记录 Day1 联调过程中遇到的核心问题、定位过程、修复方案与后续优化建议，便于组内同步与答辩说明。

## 1. PowerShell 无法激活虚拟环境

### 现象

- 执行 `.\.venv\Scripts\activate` 报错：系统禁止运行脚本（Execution Policy）。
- 导致依赖误装到全局 Python，而不是项目 `.venv`。

### 原因

- 当前终端策略不允许执行 `Activate.ps1`。

### 处理

- 在当前终端临时放开策略（仅本窗口生效）：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

- 然后再激活虚拟环境并启动后端。

## 2. 截帧上传报 `Network Error`

### 现象

- 浏览器可打开摄像头，但点击截帧上传失败。
- 后端日志显示 `POST /api/attendance/checkin` 返回 `500` 或 `503`。

### 定位结果

- 根因不是前端没做，而是后端活体检测阶段异常。
- 报错为：`AttributeError: module 'mediapipe' has no attribute 'solutions'`。
- 即使 `requirements-cv.txt` 安装完成，当前环境的 `mediapipe` 包仍不暴露 `solutions`。

## 3. 已落地修复

### 3.1 后端稳定性修复（已完成）

文件：`backend/app/services/liveness_service.py`

- 新增对 `mediapipe.solutions` 可用性的判断。
- 当 `solutions` 不可用时，不再直接抛异常导致 500。
- 增加 OpenCV fallback（Haar 人脸检测）：
  - 无人脸 -> 返回 `未检测到人脸`
  - 多人脸 -> 返回 `检测到多张人脸`
  - 单人脸 -> 返回 `ok_fallback`

### 3.2 效果

- 服务不再因 `mediapipe.solutions` 缺失而崩溃。
- 前端不会再误提示“未安装依赖”，而是得到可解释的业务结果。

## 4. 当前已知限制

- fallback 使用 OpenCV Haar，精度和稳定性低于 MediaPipe：
  - 在复杂背景、弱光、噪声较大时易误判“多张人脸”或“无人脸”。
- 这属于阶段性兼容方案，不是最终效果上限。

## 5. 后续优化建议

1. 优先恢复可用的 MediaPipe 标准路径（保证 `solutions` 可用）。
2. 前端增加取景引导（人脸居中、距离提示、光照提示）。
3. fallback 增加框过滤策略（小框/边缘框抑制）以减少误判。
4. 统一错误码与提示文案，区分“依赖异常”和“识别失败”。
