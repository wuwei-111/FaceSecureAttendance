# FaceSecureAttendance

## 快速开始

### 1) 启动后端（Python 3.10）

```bash
cd backend
py -3.10 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# 到“人脸/活体/情绪”阶段再安装（避免初始化阶段安装过慢）
pip install -r requirements-cv.txt
uvicorn app.main:app --reload --port 8000
```

如果你之前用其他版本 Python 创建过 `backend/.venv`，先删除再重建：

```bash
cd backend
rmdir /s /q .venv
py -3.10 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
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
- 2026-04-25：打通前后端数据链路：前端摄像头截帧/合照上传/情绪统计三页面可请求后端；后端三个接口写入 SQLite 占位记录并返回可展示结果。
- 2026-04-25：前端升级为浅色“玻璃拟态”布局（侧边栏 + 顶栏 + 页面切换动效），新增“学生管理”页面（搜索/分页/抽屉新增/上传预览/优雅降级）。
- 2026-04-25：完善学生管理交互：新增表单校验（必填/学号唯一）、上传进度条与上传中禁用、统一错误提示。
- 2026-04-25：完成学生管理后端：新增 `/api/students` 列表/新增/删除与 `/api/students/{id}/face` 上传接口，上传文件落盘到 `backend/face_uploads/` 并写回 `students.face_path/face_encoding`。
- 2026-04-25：实现考勤与学生库联动（占位比对版）：学生上传人脸时写入图片 SHA256 指纹，`/api/attendance/checkin` 截帧上传后按指纹匹配学生并写入 `attendance_records`。
- 2026-04-25：统一接口返回结构为 `{code,message,data}`，学生列表改为后端分页（`items/total/page/page_size`），前端 API 层新增统一解包逻辑并同步对齐学生页分页查询。
- 2026-04-25：完成 JWT 预埋对齐：后端中间件生成并回传 `X-Request-ID`，响应体增加 `request_id`；401/403 固定语义（`unauthorized/forbidden`）；前端 axios 拦截器支持 token 注入与 401/403 自动跳转 `/login`。
- 2026-04-25：完成可用登录页：新增后端 `/api/auth/login`（默认测试账号 `admin/123456`），前端登录页改为账号密码表单；登录成功写入 `access_token`，并通过路由守卫拦截未登录访问。
