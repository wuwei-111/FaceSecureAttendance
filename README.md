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
- 完成前端结构升级：拆分 `MainLayout/NavSidebar/TopHeader`，路由增加 `meta.roles` 权限控制，新增 `RecordsPage` 占位页并接入导航。
- 修复主框架三栏错位：右侧容器强制纵向布局；并新增多角色测试账号（`teacher1/teacher2/student1/student2`，密码均为 `123456`）便于权限联调。

## 今日总结（2026-04-26）

- 优化记录查询筛选栏：拉开日期与状态间距，查询/重置按钮与关键字输入框底部对齐。
- 调整学生管理交互：移除常驻操作列，改为“选中记录后上方操作区”模式。
- 升级选中行为：支持单击选中/再点取消、长按多选、批量删除与一键取消选中。
- 优化选中反馈：选中行采用更深浅蓝高亮，便于快速识别当前操作目标。
- 完成真人脸匹配与活体检测主链路：学生人脸上传改为 DeepFace embedding 入库；考勤接口增加 MediaPipe 被动活体检测与 embedding 余弦距离匹配（替换 SHA256 占位方案）。
- 调整记录查询筛选区布局：日期与关键字区块左右对齐，筛选栏间距与底部对齐进一步统一。
- 完成考勤联调页增强：新增活体/匹配状态标签、请求中防重复提交、CV 依赖缺失与无人脸场景的可读错误提示。
- 完成考勤记录联调第一版：新增后端 `/api/attendance/records`（分页+状态/关键字筛选），前端 `RecordsPage` 接口接入与分页展示。
- 修复 DeepFace 运行依赖：`requirements-cv.txt` 增加 `tf-keras`，解决上传人脸时 `503`（RetinaFace 对 keras3 兼容依赖缺失）问题。
- 学生管理细节优化：新增“取消已上传人脸”接口与按钮（删除图片+清空编码）；预览图改为完整显示（`contain`），避免视觉裁切误判。
- 补齐考勤会话接口：新增 `/api/attendance/sessions`，并为 `/api/attendance/records` 增加登录角色过滤（学生仅看本人、教师可看全班）。
- 修复人脸预览回显稳定性：后端挂载 `/face_uploads` 静态目录；前端详情预览支持按 `face_path` 直接回显，重新进入详情不再丢失图片。

