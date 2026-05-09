# FaceSecureAttendance

基于浏览器的人脸识别班级考勤系统（Vue 3 + FastAPI）。覆盖考勤、合照识别、情绪统计、学生人脸库与导出等课程大纲功能；鉴权采用 JWT，角色区分教师与学生。

---

## 快速开始

### 1）后端（建议 Python 3.10）

```powershell
cd backend
$PYTHON_VERSION = "3.10"
$VENV_NAME = ".venv"
py -$PYTHON_VERSION -m venv $VENV_NAME
& ".\$VENV_NAME\Scripts\activate"
python -m pip install -r requirements.txt
python -m pip install -r requirements-cv.txt
python -m uvicorn app.main:app --reload --port 8000
```

日常只需：

```powershell
cd backend
& ".\.venv\Scripts\activate"
python -m uvicorn app.main:app --reload --port 8000
```

说明：`requirements-cv.txt` 含 DeepFace / MediaPipe 等，用于人脸与活体；若 `MediaPipe` 在个别 Windows 环境下不可用，后端会降级到 OpenCV Haar，活体精度可能略降。

可选环境变量：`JWT_SECRET`（生产务必修改）、`CORS_ORIGINS`（逗号分隔来源）、`MAX_UPLOAD_IMAGE_MB`、`MAX_UPLOAD_CSV_MB` 等。

### 2）前端

```powershell
cd frontend
npm install
npm run dev
```

默认前端 `http://127.0.0.1:5173`，后端 `http://127.0.0.1:8000`。可在 `frontend` 配置 `VITE_API_BASE_URL` 指向实际 API 根地址。

---

## 目录结构

```
FaceSecureAttendance/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口、CORS、全局异常、静态目录挂载
│   │   ├── db_schema.py            # SQLite 轻量迁移（补列）
│   │   ├── core/
│   │   │   ├── database.py         # SQLAlchemy 引擎与 Session
│   │   │   ├── security.py         # 密码哈希、JWT 签发/校验、角色依赖
│   │   │   ├── timezone.py         # 时间展示（如北京时区）
│   │   │   ├── upload_limits.py    # 上传大小与图片魔数校验
│   │   │   ├── request_context.py  # 请求 ID
│   │   │   └── student_visibility.py  # 学生端数据范围（学籍绑定等）
│   │   ├── models/                 # ORM：User / Student / AttendanceRecord / …
│   │   ├── routers/                # 各业务路由（见下文章节「HTTP 接口」）
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   └── services/               # 人脸、活体、合照匹配、情绪等
│   ├── requirements.txt
│   ├── requirements-cv.txt
│   └── attendance.db               # 默认 SQLite 库（运行后生成）
├── frontend/
│   ├── src/
│   │   ├── api/                    # axios 封装与各模块 API
│   │   ├── components/             # 摄像头、布局等
│   │   ├── layouts/                # 主布局、侧栏
│   │   ├── router/                 # 路由与登录守卫
│   │   ├── stores/                 # 模块级状态（如合照识别跨页会话）
│   │   ├── styles/                 # 主题 CSS 变量
│   │   └── views/                  # 登录、考勤、记录、合照、情绪、学生管理
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   └── verify-auth.ps1             # 接口级鉴权冒烟（可选）
├── face_attendance_outline.md      # 课程开发大纲
└── README.md
```

---

## 统一响应格式

业务接口多为：

```json
{ "code": 0, "message": "ok", "data": { ... }, "request_id": "..." }
```

`code !== 0` 表示失败；HTTP 状态码与业务码并存（如 401、403、422）。

---

## HTTP 接口说明

基础 URL：`http://127.0.0.1:8000`（下方路径均带此前缀）。  
鉴权：除登录外，需在请求头携带 `Authorization: Bearer <access_token>`。

### 根与健康

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 服务信息与文档入口提示 |
| GET | `/health` | 否 | 健康检查 |

### 认证 `/api/auth`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/auth/login` | 否 | 表单 JSON：`{ "username", "password" }`，返回 `access_token`、`username`、`role` |
| GET | `/api/auth/me` | 是 | 当前用户 `id`、`username`、`role` |

### 考勤 `/api/attendance`

| 方法 | 路径 | 鉴权 / 角色 | 说明 |
|------|------|----------------|------|
| POST | `/api/attendance/checkin` | 登录（教师/学生） | `multipart/form-data`，字段 `image`（照片）；活体 + 人脸比对 + 写库 |
| GET | `/api/attendance/records` | 登录 | 分页考勤列表。Query：`q`（学号/姓名）、`status`（`all`/`present`/…）、`page`、`page_size`、`date_from`、`date_to`；**学生仅本人** |
| GET | `/api/attendance/sessions` | 登录 | 按日聚合会话统计；**学生仅本人** |
| DELETE | `/api/attendance/{record_id}` | **教师** | 删除指定考勤记录 |

### 合照 `/api/photo`（均为教师）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/photo/recognize` | `multipart/form-data`：`image`；可选表单 `activity_name`；返回匹配名单等 |
| GET | `/api/photo/list` | Query：`q`（活动名）、`page`、`page_size`；合照记录列表 |
| GET | `/api/photo/activity-stats` | 活动维度统计 |

### 情绪 `/api/emotion`（均为教师）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/emotion/stats` | Query：`date_from`、`date_to`；情绪分布汇总 |
| GET | `/api/emotion/records` | Query：`q`、`emotion`、`date_from`、`date_to`、`page`、`page_size`；明细 |

### 学生管理 `/api/students`（均为教师）

路径中的 `{id}` 为学生表 **主键 id**（整数），非学号字符串。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/students` | Query：`q`（学号/姓名/班级模糊）、`page`、`page_size` |
| POST | `/api/students` | JSON 新建（含 `student_id`、`name`、`class_name` 等） |
| PUT | `/api/students/{id}` | JSON 部分更新 |
| DELETE | `/api/students/{id}` | 删除 |
| POST | `/api/students/{id}/face` | `multipart`：`image`；上传人脸并提取特征 |
| DELETE | `/api/students/{id}/face` | 清除人脸数据 |
| POST | `/api/students/batch-import` | `multipart`：`file`（CSV）；批量导入 |

### 导出 `/api/export`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/export/attendance/excel` | 登录 | Query：与考勤列表筛选一致（`q`、`status`、`date_from`、`date_to`）；**学生仅导出本人**；返回 xlsx 流 |
| GET | `/api/export/activity/excel` | 登录 | Query：`q`、`activity`、`date_from`、`date_to`；活动记录导出；**学生仅本人** |

更多字段与枚举以运行后端后的 **Swagger** 为准：`http://127.0.0.1:8000/docs`。

---

## 今日总结（2026-04-25）

- 完成前后端基础骨架：Vue3 + FastAPI + SQLite，项目可运行。
- 完成数据库核心表：`students` / `attendance_records` / `group_photos` / `activity_logs` / `emotion_logs` / `users`。
- 完成统一响应契约：后端 `{ code, message, data, request_id }`。
- 完成登录与鉴权链路：登录页、token 注入、路由守卫。

## 今日总结（2026-04-26）

- 完成考勤主链路：截帧上传、活体检测、DeepFace 特征比对。
- 完成考勤记录与会话接口联调：`/api/attendance/records`、`/api/attendance/sessions`。
- 完成学生人脸管理闭环：上传/删除与预览。

## 今日总结（2026-04-27）

- 鉴权升级为 JWT（`PyJWT`，可选 `JWT_SECRET`）；新增 `GET /api/auth/me` 与路由守卫拉取用户信息。
- 后端按角色保护：`/api/students`、`/api/photo`、`/api/emotion` 仅教师；考勤打卡需登录。
- 提供 `scripts/verify-auth.ps1` 做接口级鉴权冒烟（默认 13 项）。

## 今日总结（2026-04-28）

- 合照页：拖拽上传、预览、进度、名单与统计；情绪页：ECharts 与学生情绪明细及筛选壳层；学生管理：CSV 导入与模板。
- 导出：记录页与合照侧 Excel 入口及加载态。
- 导航与权限体验优化（侧栏、403/401 行为等）。

## 今日总结（2026-05-08）

- 对照课程大纲完成系统安全与识别侧收尾：活体抗伪造能力强化、人脸比对与合照匹配策略、服务端统一异常与前端超时/摄像头等提示；教师/学生权限与业务链路保持一致。
- 完成学生端考勤记录按学籍可见（登录账号与学号解耦时的绑定策略）、合照识别后台请求与结果跨页面保留等体验优化。
- 文档与本 README 整理：目录结构、接口说明与日常启动方式更新。
