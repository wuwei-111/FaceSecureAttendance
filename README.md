# FaceSecureAttendance

## 快速开始

### 1) 启动后端（固定 Python 3.10，可指定虚拟环境目录）

```powershell
cd backend
$PYTHON_VERSION = "3.10"
$VENV_NAME = ".venv"
deactivate
if (Test-Path $VENV_NAME) { Remove-Item $VENV_NAME -Recurse -Force }
py -$PYTHON_VERSION -m venv $VENV_NAME
& ".\$VENV_NAME\Scripts\activate"
python -m pip install -r requirements.txt
# 到“人脸/活体/情绪”阶段必须再安装（避免初始化阶段安装过慢）
python -m pip install -r requirements-cv.txt
python -m uvicorn app.main:app --reload --port 8000
```

推荐值：

- `$PYTHON_VERSION = "3.10"`：当前项目已按这个版本验证
- `$VENV_NAME = ".venv"`：默认虚拟环境目录；如需多个环境，也可改成 `.venv310`、`.venv-dev`

日常启动

```powershell
cd backend
& ".\.venv\Scripts\activate"
python -m uvicorn app.main:app --reload --port 8000
```

常见报错与处理：

- `uvicorn is not recognized`：没激活 `backend/.venv`，或不在 `backend` 目录（优先使用 `python -m uvicorn ...`）
- `Could not open requirements*.txt`：命令在错误目录执行，先 `cd backend`
- `Permission denied ... .venv\\Scripts\\python.exe`：正在占用 `.venv`，先 `deactivate`，再 `Remove-Item ".venv" -Recurse -Force`
- `WinError 32` / `另一个程序正在使用此文件`：Windows / OneDrive / 杀毒软件可能正在扫描 `.venv`，导致 `pip install -r requirements-cv.txt` 中途失败。通常直接重试一次即可；如仍失败，关闭占用 `.venv` 的 Python 进程后重试。
- `No suitable Python runtime found` / `py -3.10` 失败：说明本机还没安装 Python 3.10，需要先安装对应版本，再重新执行创建虚拟环境命令。
- 前端用 `http://127.0.0.1:5173` 而后端仅允许 `localhost` 时，上传请求可能被浏览器拦截（表现为 `Network Error`）。后端已默认同时放行 `localhost` 与 `127.0.0.1`；也可设置环境变量 `CORS_ORIGINS`（逗号分隔）自定义。

CV 依赖兼容说明：

- 当前项目固定使用 `Python 3.10` 创建 `backend/.venv`。
- `backend/requirements.txt` 与 `backend/requirements-cv.txt` 已固定到当前验证通过的版本，优先按锁定版本安装，降低不同机器上的环境漂移。
- 当前 `requirements-cv.txt` 安装的 `mediapipe` 在部分 Windows 环境下运行时不暴露 `mediapipe.solutions`，项目代码已做兼容：优先使用 `MediaPipe solutions`，若不可用则自动降级到 OpenCV Haar 人脸检测，避免考勤接口直接 `500`。
- 因此只要按上面的步骤完成 `requirements.txt` 和 `requirements-cv.txt` 安装，项目即可正常启动；若使用 fallback，活体检测精度会低于标准 `MediaPipe` 路径。

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

## 当前主要接口（摘要）

- `GET /health` 健康检查
- `POST /api/auth/login`、`GET /api/auth/me` 登录与当前用户（Bearer）
- `POST /api/attendance/checkin`、`GET /api/attendance/records`、`GET /api/attendance/sessions` 考勤（记录支持 `date_from`/`date_to`）
- `POST /api/photo/recognize`、`GET /api/photo/list`、`GET /api/photo/activity-stats` 合照识别与统计（教师）
- `GET /api/emotion/stats`、`GET /api/emotion/records` 情绪统计与明细（教师）
- `GET /api/export/attendance/excel`、`GET /api/export/activity/excel` 考勤 / 活动 Excel 导出（与列表相近筛选；学生仅本人）
- 上传治理：考勤/人脸/合照图片校验大小与类型（默认单图上限 15MB，`MAX_UPLOAD_IMAGE_MB`）；学生 CSV 批量导入上限默认 5MB（`MAX_UPLOAD_CSV_MB`）

## 今日总结（2026-04-25）

- 完成前后端基础骨架：Vue3 + FastAPI + SQLite，项目可运行。
- 完成数据库核心表：`students/attendance_records/group_photos/activity_logs/emotion_logs/users`。
- 完成统一响应契约：后端 `{code,message,data,request_id}`。
- 完成登录与鉴权链路：登录页 + token 注入 + 路由守卫（未登录跳转登录）。

## 今日总结（2026-04-26）

- 完成考勤主链路联调：截帧上传 + MediaPipe 活体检测 + DeepFace embedding 匹配。
- 完成考勤记录/会话接口联调：`/api/attendance/records`、`/api/attendance/sessions` 前后端打通。
- 完成学生人脸数据管理闭环：上传/取消上传（图片+编码）与预览回显稳定。

## 今日总结（2026-04-27）

- 鉴权升级为标准 JWT：`backend/app/core/security.py`（`HS256`，依赖 `PyJWT`），登录签发 token，`Authorization: Bearer` 验签；可选环境变量 `JWT_SECRET`（生产务必设置）。
- 新增 `GET /api/auth/me`，前端 `frontend/src/api/auth.js` 增加 `getCurrentUser`，路由守卫在无本地 `user_info` 时拉取用户信息并写入本地，鉴权失败则清理 token 并回登录页。
- 角色级后端保护：`/api/students`、`/api/photo`、`/api/emotion` 仅 `teacher`；`/api/attendance/checkin` 需登录（`teacher`/`student`）；`/api/attendance/records` 与 `sessions` 沿用 JWT + 学生仅看本人记录。
- 一键权限验证脚本：`scripts/verify-auth.ps1`（默认 `http://127.0.0.1:8000`，可用 `-BaseUrl` 覆盖）；启动后端后在项目根目录执行  
  `powershell -ExecutionPolicy Bypass -File scripts/verify-auth.ps1`  
  预期 **13 项全部 PASS**（健康检查、登录、`/me`、教师专属接口 403、考勤记录 401/200）。

## 今日总结（2026-04-28）

- 完成合照页前端：拖拽上传、预览、进度、名单与统计展示（教师权限控制）。
- 完成情绪页前端：ECharts 饼图/柱状图 + 明细表；并补齐学号/日期筛选交互壳（等待后端维度扩展）。
- 完成学生管理前端：CSV 导入（文件/粘贴双模式）、模板下载、进度与导入统计反馈。
- 完成导出入口前端：记录页/合照页导出 Excel 按钮、加载态与失败降级提示。
