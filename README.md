# FaceSecureAttendance

## 快速开始

### 1) 启动后端（Python 3.10）

```bash
cd backend
python3.10 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# 到“人脸/活体/情绪”阶段再安装（避免初始化阶段安装过慢）
pip install -r requirements-cv.txt
uvicorn app.main:app --reload --port 8000
```

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 项目介绍

课程实验：以内容安全场景为核心的人脸识别考勤系统（BS 架构）。

## 目录结构

- `frontend/` 前端（Vue3 + Vite + Element Plus）
- `backend/` 后端（FastAPI + SQLAlchemy + SQLite）

## 当前接口骨架

- `GET /health` 健康检查
- `POST /api/attendance/checkin` 考勤占位接口
- `POST /api/photo/recognize` 合照识别占位接口
- `GET /api/emotion/stats` 情绪统计占位接口

## 变更记录

- 2026-04-25：初始化前后端骨架；后端数据库模型按大纲扩展为 `students/attendance_records/group_photos/activity_logs/emotion_logs/users`；拆分依赖为基础 `requirements.txt` 与可选 `requirements-cv.txt`。
