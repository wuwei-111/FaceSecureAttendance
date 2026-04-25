# FaceSecureAttendance

课程实验骨架：Vue3 + FastAPI + SQLite（后端固定 Python 3.10）。

## 目录

- `frontend/` 前端（Vue3 + Vite + Element Plus）
- `backend/` 后端（FastAPI + SQLAlchemy）

## 快速启动

### 1) 启动后端

```bash
cd backend
python3.10 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

## 当前接口骨架

- `GET /health` 健康检查
- `POST /api/attendance/checkin` 考勤占位接口
- `POST /api/photo/recognize` 合照识别占位接口
- `GET /api/emotion/stats` 情绪统计占位接口
