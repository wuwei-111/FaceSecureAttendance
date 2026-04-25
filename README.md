# FaceSecureAttendance

## 快速开始

### 1) 启动后端（Python 3.10）

```powershell
cd backend
deactivate
if (Test-Path ".venv") { Remove-Item ".venv" -Recurse -Force }
py -3.10 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
# 到“人脸/活体/情绪”阶段再安装（避免初始化阶段安装过慢）
# python -m pip install -r requirements-cv.txt
python -m uvicorn app.main:app --reload --port 8000
```

日常启动

```powershell
cd backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

常见报错与处理：

- `uvicorn is not recognized`：没激活 `backend/.venv`，或不在 `backend` 目录（优先使用 `python -m uvicorn ...`）
- `Could not open requirements*.txt`：命令在错误目录执行，先 `cd backend`
- `Permission denied ... .venv\\Scripts\\python.exe`：正在占用 `.venv`，先 `deactivate`，再 `Remove-Item ".venv" -Recurse -Force`

### 2) 启动前端

```powershell
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

## 今日总结（2026-04-25）

- 完成前后端基础骨架：Vue3 + FastAPI + SQLite，项目可运行。
- 完成数据库与核心表：`students/attendance_records/group_photos/activity_logs/emotion_logs/users`。
- 完成学生管理全链路：前端页面交互（搜索、分页、校验、上传进度）+ 后端 `students` CRUD 与人脸上传。
- 完成考勤联动占位比对：截帧上传后可与学生已上传图片指纹匹配并写入考勤记录。
- 完成接口契约统一：后端统一 `{code,message,data,request_id}`，学生列表支持后端分页。
- 完成登录与鉴权预埋：`/api/auth/login`、前端登录页、路由守卫、axios token 注入、401/403 统一跳转登录。
- 完成工程与文档稳态：README 启动命令防错化（PowerShell 场景）并补充常见报错处理。

