# 人脸识别班级考勤系统 — 开发大纲

> **技术栈**：Vue 3 + Vite + Element Plus｜FastAPI + SQLite/PostgreSQL｜DeepFace + MediaPipe｜ECharts  
> **团队规模**：2-3 人｜**验收节点**：第 11 周周五

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构设计](#2-系统架构设计)
3. [数据库设计](#3-数据库设计)
4. [第一阶段：项目初始化与环境搭建](#4-第一阶段项目初始化与环境搭建)
5. [第二阶段：人脸库管理](#5-第二阶段人脸库管理)
6. [第三阶段：基础考勤功能](#6-第三阶段基础考勤功能)
7. [第四阶段：合照识别功能](#7-第四阶段合照识别功能)
8. [第五阶段：情绪分析功能](#8-第五阶段情绪分析功能)
9. [第六阶段：系统安全与权限管理](#9-第六阶段系统安全与权限管理)
10. [前端页面规划](#10-前端页面规划)
11. [API 接口汇总](#11-api-接口汇总)
12. [测试计划](#12-测试计划)
13. [课程报告结构建议](#13-课程报告结构建议)
14. [分工建议](#14-分工建议)
15. [开发日程表](#15-开发日程表)

---

## 1. 项目概述

### 1.1 项目背景

以内容安全领域的人脸识别、活体检测技术为核心，结合 BS（Browser/Server）架构，实现一套功能完整、安全可靠的班级考勤系统。

### 1.2 核心功能模块

| 模块 | 描述 | 对应评分 |
|------|------|---------|
| 基础考勤 | 摄像头采集 → 活体检测 → 人脸比对 → 记录考勤 | 25 分 |
| 合照识别 | 上传合照 → 批量人脸识别 → 生成名单与报表 | 9 分 |
| 情绪分析 | 考勤/合照过程中同步分析面部情绪 | 8 分 |
| 系统安全 | 活体检测抗攻击 + 权限管理 + 异常处理 | 18 分 |
| 架构设计 | BS 架构规范、前后端分离、数据库设计 | 10 分 |
| 实验报告 | 课程设计报告 + 源码提交 | 30 分 |

### 1.3 技术选型理由

| 技术 | 版本 | 选型理由 |
|------|------|---------|
| Vue 3 + Vite | ^3.4 | 组合式 API，热更新快，适合快速迭代 |
| Element Plus | ^2.7 | 开箱即用的企业级 UI 组件 |
| FastAPI | ^0.110 | 异步、自动生成 Swagger 文档、与 Python CV 库无缝集成 |
| DeepFace | ^0.0.93 | 一个库同时覆盖人脸检测、比对、情绪分析 |
| MediaPipe | ^0.10 | Google 出品，眨眼/头动活体检测易实现 |
| SQLite → PostgreSQL | — | 开发用 SQLite，生产可无缝迁移 PostgreSQL |
| ECharts | ^5.5 | 柱状图、饼图、折线图均支持，中文文档齐全 |

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────┐
│                  Browser (Vue 3)             │
│  考勤页 │ 合照页 │ 情绪统计页 │ 管理页        │
└───────────────────┬─────────────────────────┘
                    │ HTTP / WebSocket
                    ▼
┌─────────────────────────────────────────────┐
│              FastAPI Backend                │
│  /auth  /attendance  /photo  /emotion       │
│  /students  /stats  /export                 │
└────────┬─────────────────┬──────────────────┘
         │                 │
         ▼                 ▼
┌──────────────┐   ┌───────────────────────┐
│  SQLite /    │   │  Face Engine          │
│  PostgreSQL  │   │  DeepFace + MediaPipe │
│  (存储数据)  │   │  (人脸编码 .pkl 文件)  │
└──────────────┘   └───────────────────────┘
```

### 2.2 目录结构

```
face-attendance/
├── frontend/                    # Vue 3 项目
│   ├── src/
│   │   ├── views/
│   │   │   ├── AttendancePage.vue    # 考勤主页面
│   │   │   ├── GroupPhotoPage.vue    # 合照识别页面
│   │   │   ├── EmotionPage.vue       # 情绪统计页面
│   │   │   ├── StudentManage.vue     # 学生管理页面
│   │   │   └── LoginPage.vue         # 登录页
│   │   ├── components/
│   │   │   ├── CameraCapture.vue     # 摄像头组件
│   │   │   ├── AttendanceTable.vue   # 考勤记录表格
│   │   │   └── EmotionChart.vue      # 情绪图表组件
│   │   ├── api/                      # axios 接口封装
│   │   ├── stores/                   # Pinia 状态管理
│   │   └── router/                   # Vue Router
│   └── vite.config.js
│
├── backend/                     # FastAPI 项目
│   ├── main.py                       # 入口文件
│   ├── routers/
│   │   ├── auth.py                   # 登录/权限
│   │   ├── students.py               # 学生人脸库管理
│   │   ├── attendance.py             # 考勤接口
│   │   ├── photo.py                  # 合照识别接口
│   │   ├── emotion.py                # 情绪查询接口
│   │   └── export.py                 # Excel 导出接口
│   ├── models/
│   │   ├── database.py               # SQLAlchemy 配置
│   │   └── schemas.py                # Pydantic 模型
│   ├── services/
│   │   ├── face_service.py           # 人脸识别核心逻辑
│   │   ├── liveness_service.py       # 活体检测逻辑
│   │   └── emotion_service.py        # 情绪分析逻辑
│   ├── face_db/                      # 人脸编码存储（.pkl）
│   └── requirements.txt
│
└── README.md
```

### 2.3 数据流说明

**考勤流程**：
```
前端摄像头截帧 → base64 编码 → POST /attendance/check
→ [活体检测] MediaPipe 眨眼/头动校验
→ [人脸比对] DeepFace 与人脸库对比
→ [情绪分析] DeepFace 同步提取情绪标签
→ 写入数据库 → 返回结果 JSON → 前端渲染
```

**合照识别流程**：
```
上传图片文件 → POST /photo/recognize
→ DeepFace 检测所有人脸位置
→ 逐人脸与人脸库批量比对
→ 写入 group_photo / activity_log 表
→ 返回匹配名单 + 统计数据 → 前端展示报表
```

---

## 3. 数据库设计

### 3.1 表结构

#### `students` — 学生信息表

```sql
CREATE TABLE students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  TEXT NOT NULL UNIQUE,   -- 学号
    name        TEXT NOT NULL,           -- 姓名
    class_name  TEXT,                    -- 班级
    face_path   TEXT,                    -- 原始照片路径
    face_encoding BLOB,                 -- 人脸编码（pickle 序列化）
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `attendance_records` — 考勤记录表

```sql
CREATE TABLE attendance_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,          -- 关联学号
    name         TEXT,
    check_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
    status       TEXT DEFAULT 'present', -- present / failed
    confidence   REAL,                   -- 比对置信度
    emotion      TEXT,                   -- 当次情绪标签
    session_id   TEXT                    -- 考勤场次 ID
);
```

#### `group_photos` — 合照记录表

```sql
CREATE TABLE group_photos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_path   TEXT NOT NULL,
    activity_name TEXT,                  -- 活动名称
    upload_time  DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_faces  INTEGER,                -- 检测到的人脸总数
    matched      INTEGER                 -- 成功匹配数
);
```

#### `activity_logs` — 活动参与记录表

```sql
CREATE TABLE activity_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,
    group_photo_id INTEGER,
    activity_name TEXT,
    emotion      TEXT,
    record_time  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `emotion_logs` — 情绪详细记录表

```sql
CREATE TABLE emotion_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,
    name         TEXT,
    source       TEXT,                   -- 'attendance' 或 'group_photo'
    emotion      TEXT,                   -- happy / neutral / sad / angry / surprise / fear / disgust
    confidence   REAL,
    record_time  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `users` — 系统用户表（教师/学生账号）

```sql
CREATE TABLE users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role         TEXT DEFAULT 'student',  -- 'teacher' 或 'student'
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. 第一阶段：项目初始化与环境搭建

**目标**：前后端项目可跑通，数据库建立完毕  
**预计时间**：2 天

### 4.1 前端初始化

```bash
# 创建 Vue 3 项目
npm create vite@latest frontend -- --template vue
cd frontend
npm install

# 安装依赖
npm install element-plus axios pinia vue-router echarts
npm install @element-plus/icons-vue
```

`main.js` 配置：
```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus, { locale: zhCn })
app.use(createPinia())
app.use(router)
app.mount('#app')
```

### 4.2 后端初始化

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安装依赖
pip install fastapi uvicorn sqlalchemy deepface mediapipe
pip install python-multipart python-jose[cryptography] passlib
pip install openpyxl pillow numpy opencv-python
```

`requirements.txt`：
```
fastapi==0.110.0
uvicorn==0.29.0
sqlalchemy==2.0.30
deepface==0.0.93
mediapipe==0.10.14
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib==1.7.4
openpyxl==3.1.2
pillow==10.3.0
numpy==1.26.4
opencv-python==4.9.0.80
```

`main.py` 入口：
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, students, attendance, photo, emotion, export

app = FastAPI(title="人脸考勤系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(students.router, prefix="/students", tags=["学生管理"])
app.include_router(attendance.router, prefix="/attendance", tags=["考勤"])
app.include_router(photo.router, prefix="/photo", tags=["合照识别"])
app.include_router(emotion.router, prefix="/emotion", tags=["情绪分析"])
app.include_router(export.router, prefix="/export", tags=["导出"])
```

### 4.3 数据库初始化

```python
# models/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4.4 验收标准

- [ ] `uvicorn main:app --reload` 启动成功，访问 `http://localhost:8000/docs` 可见 Swagger 文档
- [ ] `npm run dev` 启动成功，前端页面可在 `http://localhost:5173` 访问
- [ ] 数据库文件 `attendance.db` 自动创建，所有表结构正确

---

## 5. 第二阶段：人脸库管理

**目标**：完成学生人脸的录入、存储、管理 CRUD  
**预计时间**：3 天

### 5.1 后端：人脸编码服务

```python
# services/face_service.py
import pickle
import numpy as np
from deepface import DeepFace

def extract_face_encoding(image_path: str) -> bytes:
    """提取人脸编码，返回序列化字节"""
    embedding = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet512",   # 精度更高
        enforce_detection=True
    )
    encoding = np.array(embedding[0]["embedding"])
    return pickle.dumps(encoding)

def compare_faces(encoding1: bytes, encoding2: bytes, threshold: float = 0.4) -> dict:
    """比较两个人脸编码，返回是否匹配和距离"""
    enc1 = pickle.loads(encoding1)
    enc2 = pickle.loads(encoding2)
    distance = np.linalg.norm(enc1 - enc2)
    return {
        "match": distance < threshold,
        "distance": float(distance),
        "confidence": max(0, 1 - distance)
    }
```

### 5.2 后端：学生管理 API

```python
# routers/students.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil, os, uuid
from models.database import get_db
from services.face_service import extract_face_encoding

router = APIRouter()

@router.post("/add")
async def add_student(
    student_id: str,
    name: str,
    class_name: str,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """添加学生并录入人脸"""
    # 1. 保存上传照片
    photo_dir = "face_db/photos"
    os.makedirs(photo_dir, exist_ok=True)
    photo_path = f"{photo_dir}/{uuid.uuid4()}.jpg"
    with open(photo_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    # 2. 提取人脸编码
    try:
        encoding = extract_face_encoding(photo_path)
    except Exception as e:
        os.remove(photo_path)
        raise HTTPException(status_code=400, detail=f"人脸检测失败：{str(e)}")
    
    # 3. 写入数据库
    # ... (SQLAlchemy insert)
    return {"success": True, "student_id": student_id, "name": name}

@router.get("/list")
async def list_students(db: Session = Depends(get_db)):
    """获取所有学生列表"""
    # ... (SQLAlchemy query)
    pass

@router.delete("/{student_id}")
async def delete_student(student_id: str, db: Session = Depends(get_db)):
    """删除学生"""
    pass

@router.post("/batch-import")
async def batch_import(csv_file: UploadFile = File(...)):
    """批量 CSV 导入学生信息（不含照片，后续补录）"""
    pass
```

### 5.3 前端：学生管理页面

**核心组件：`StudentManage.vue`**

- Element Plus `el-table` 展示学生列表（学号、姓名、班级、人脸状态）
- `el-upload` 组件支持照片上传预览
- 搜索栏支持按学号、姓名过滤
- 操作列：编辑 / 删除 / 重新录入照片
- 批量导入：上传 CSV 文件（格式：学号, 姓名, 班级）

### 5.4 验收标准

- [ ] 可添加单个学生 + 上传照片，后端成功提取并存储编码
- [ ] 前端学生列表正常显示，支持搜索
- [ ] 可删除学生（含人脸编码和照片文件）
- [ ] 批量 CSV 导入基本可用

---

## 6. 第三阶段：基础考勤功能

**目标**：实现完整的摄像头采集 → 活体检测 → 人脸比对 → 记录全流程  
**预计时间**：4 天  
**对应评分**：25 分

### 6.1 前端：摄像头组件

```vue
<!-- components/CameraCapture.vue -->
<template>
  <div class="camera-container">
    <video ref="videoRef" autoplay playsinline width="480" height="360" />
    <canvas ref="canvasRef" style="display:none" width="480" height="360" />
    
    <div class="controls">
      <el-button @click="startCamera" type="primary">开启摄像头</el-button>
      <el-button @click="captureAndCheck" type="success" :loading="checking">
        {{ mode === 'manual' ? '手动打卡' : '自动检测中...' }}
      </el-button>
      <el-switch v-model="autoMode" active-text="自动模式" @change="toggleAutoMode" />
    </div>
    
    <!-- 状态指示器 -->
    <div class="status-indicator" :class="statusClass">{{ statusText }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { attendanceApi } from '@/api/attendance'

const videoRef = ref(null)
const canvasRef = ref(null)
const autoMode = ref(false)
let autoTimer = null

async function startCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({ 
    video: { width: 480, height: 360, facingMode: 'user' } 
  })
  videoRef.value.srcObject = stream
}

function captureFrame() {
  const ctx = canvasRef.value.getContext('2d')
  ctx.drawImage(videoRef.value, 0, 0, 480, 360)
  return canvasRef.value.toDataURL('image/jpeg', 0.8)  // base64
}

async function captureAndCheck() {
  const imageData = captureFrame()
  const result = await attendanceApi.check({ image: imageData })
  // 处理返回结果...
}

function toggleAutoMode(val) {
  if (val) {
    autoTimer = setInterval(captureAndCheck, 3000)  // 每3秒自动检测
  } else {
    clearInterval(autoTimer)
  }
}

onUnmounted(() => clearInterval(autoTimer))
</script>
```

### 6.2 后端：活体检测服务

```python
# services/liveness_service.py
import cv2
import mediapipe as mp
import numpy as np
import base64

mp_face_mesh = mp.solutions.face_mesh

# 眼部关键点索引（MediaPipe 468点模型）
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

def eye_aspect_ratio(landmarks, eye_indices, image_w, image_h):
    """计算眼睛纵横比（EAR），EAR 低于阈值 = 眨眼"""
    points = [(landmarks[i].x * image_w, landmarks[i].y * image_h) for i in eye_indices]
    # 垂直距离
    A = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    B = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
    # 水平距离
    C = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
    return (A + B) / (2.0 * C)

def liveness_check_single_frame(image_bytes: bytes) -> dict:
    """
    单帧活体检测（基础版）
    对于更强的活体检测，需要前端连续发送多帧并检测眨眼动作
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    
    with mp_face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1, refine_landmarks=True
    ) as face_mesh:
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            return {"is_live": False, "reason": "未检测到人脸"}
        
        landmarks = results.multi_face_landmarks[0].landmark
        left_ear  = eye_aspect_ratio(landmarks, LEFT_EYE, w, h)
        right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
        avg_ear   = (left_ear + right_ear) / 2.0
        
        # 基本检测：EAR 在正常范围内（睁眼 0.25-0.45）
        if avg_ear < 0.15:
            return {"is_live": False, "reason": "眼部异常，疑似照片"}
        
        return {"is_live": True, "ear": float(avg_ear)}
```

### 6.3 后端：考勤主接口

```python
# routers/attendance.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import base64, io
from PIL import Image

router = APIRouter()

class AttendanceRequest(BaseModel):
    image: str        # base64 编码的图片
    session_id: str = "default"

@router.post("/check")
async def check_attendance(req: AttendanceRequest, db: Session = Depends(get_db)):
    # 1. 解码图片
    img_data = base64.b64decode(req.image.split(',')[1])
    
    # 2. 活体检测
    liveness = liveness_service.liveness_check_single_frame(img_data)
    if not liveness["is_live"]:
        return {"success": False, "reason": liveness["reason"], "step": "liveness"}
    
    # 3. 提取当前帧人脸编码
    try:
        current_encoding = face_service.extract_face_encoding_from_bytes(img_data)
    except:
        return {"success": False, "reason": "未检测到清晰人脸", "step": "detection"}
    
    # 4. 与人脸库所有学生比对
    students = db.query(Student).all()
    best_match = None
    best_distance = float('inf')
    
    for student in students:
        result = face_service.compare_faces(student.face_encoding, current_encoding)
        if result["match"] and result["distance"] < best_distance:
            best_distance = result["distance"]
            best_match = student
    
    if not best_match:
        return {"success": False, "reason": "未找到匹配学生", "step": "recognition"}
    
    # 5. 同步情绪分析
    emotion_result = emotion_service.analyze_emotion(img_data)
    
    # 6. 写入考勤记录
    record = AttendanceRecord(
        student_id=best_match.student_id,
        name=best_match.name,
        confidence=1 - best_distance,
        emotion=emotion_result.get("dominant_emotion"),
        session_id=req.session_id
    )
    db.add(record)
    db.commit()
    
    return {
        "success": True,
        "student_id": best_match.student_id,
        "name": best_match.name,
        "confidence": round(1 - best_distance, 3),
        "emotion": emotion_result.get("dominant_emotion"),
        "check_time": record.check_time.isoformat()
    }

@router.get("/records")
async def get_records(session_id: str = None, db: Session = Depends(get_db)):
    """查询考勤记录，支持按场次筛选"""
    pass
```

### 6.4 Excel 导出

```python
# routers/export.py
from fastapi.responses import StreamingResponse
import openpyxl, io
from datetime import datetime

@router.get("/attendance/excel")
async def export_attendance_excel(session_id: str = None, db: Session = Depends(get_db)):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "考勤记录"
    ws.append(["学号", "姓名", "考勤时间", "状态", "置信度", "情绪"])
    
    records = db.query(AttendanceRecord).all()
    for r in records:
        ws.append([r.student_id, r.name, r.check_time.strftime("%Y-%m-%d %H:%M:%S"),
                   r.status, r.confidence, r.emotion])
    
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    filename = f"考勤记录_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### 6.5 验收标准

- [ ] 摄像头可正常调用，手动/自动模式均可截帧发送
- [ ] 活体检测能拦截直接对屏幕拍照的情况
- [ ] 人脸比对准确率测试 ≥ 85%（用多名同学测试）
- [ ] 考勤结果（成功/失败、学生信息、时间）实时显示
- [ ] Excel 导出文件格式正确，数据完整

---

## 7. 第四阶段：合照识别功能

**目标**：批量识别合照中的所有学生人脸，生成名单和统计报表  
**预计时间**：3 天  
**对应评分**：9 分

### 7.1 后端：合照识别服务

```python
# routers/photo.py
from fastapi import APIRouter, UploadFile, File, Form
from deepface import DeepFace
import cv2, numpy as np

router = APIRouter()

@router.post("/recognize")
async def recognize_group_photo(
    photo: UploadFile = File(...),
    activity_name: str = Form("未命名活动"),
    db: Session = Depends(get_db)
):
    # 1. 保存上传照片
    img_data = await photo.read()
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 2. 检测所有人脸（DeepFace 批量检测）
    try:
        detected_faces = DeepFace.extract_faces(
            img_path=img,
            detector_backend="retinaface",  # 多人脸检测效果好
            enforce_detection=False
        )
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    # 3. 逐个人脸与人脸库比对
    students = db.query(Student).all()
    matched_students = []
    
    for face_obj in detected_faces:
        if face_obj["confidence"] < 0.9:
            continue  # 过滤低置信度检测结果
        
        face_img = face_obj["face"]
        
        # 提取当前人脸编码
        try:
            curr_encoding = face_service.extract_face_encoding_from_array(face_img)
        except:
            continue
        
        # 与所有学生比对
        for student in students:
            result = face_service.compare_faces(student.face_encoding, curr_encoding)
            if result["match"]:
                matched_students.append({
                    "student_id": student.student_id,
                    "name": student.name,
                    "confidence": 1 - result["distance"]
                })
                # 记录活动日志
                log = ActivityLog(
                    student_id=student.student_id,
                    activity_name=activity_name
                )
                db.add(log)
                break
    
    db.commit()
    
    return {
        "success": True,
        "activity_name": activity_name,
        "total_faces": len(detected_faces),
        "matched_count": len(matched_students),
        "students": matched_students
    }

@router.get("/activity-stats")
async def get_activity_stats(db: Session = Depends(get_db)):
    """统计每个学生参与活动的次数"""
    # 返回用于 ECharts 柱状图的数据
    pass
```

### 7.2 前端：合照上传与结果展示

**`GroupPhotoPage.vue` 核心功能：**

- `el-upload` 拖拽上传，支持预览大图
- 上传后显示识别进度（可用 `el-progress`）
- 识别结果：
  - 匹配名单卡片（学号 + 姓名 + 置信度）
  - 统计数字：检测到 N 张人脸，成功匹配 M 人
- ECharts 柱状图：各学生活动参与次数对比
- 导出功能：将名单导出为 Excel

### 7.3 验收标准

- [ ] 上传合照后能检测出多人人脸
- [ ] 单张合照中 10 人以上可正常处理，超时控制在 30 秒内
- [ ] 合照识别准确率 ≥ 85%
- [ ] 活动统计报表（柱状图/表格）正常展示
- [ ] 可导出参与名单 Excel

---

## 8. 第五阶段：情绪分析功能

**目标**：在考勤和合照识别过程中同步分析情绪，前端可视化统计  
**预计时间**：2 天  
**对应评分**：8 分

### 8.1 后端：情绪分析服务

```python
# services/emotion_service.py
from deepface import DeepFace
import numpy as np

EMOTION_MAP = {
    "happy": "开心", "neutral": "平静", "sad": "悲伤",
    "angry": "愤怒", "surprise": "惊讶", "fear": "恐惧", "disgust": "厌恶"
}

def analyze_emotion(img_bytes: bytes) -> dict:
    """分析图片中人脸的情绪"""
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    try:
        result = DeepFace.analyze(
            img_path=img,
            actions=["emotion"],
            enforce_detection=False,
            silent=True
        )
        if isinstance(result, list):
            result = result[0]
        
        dominant = result.get("dominant_emotion", "neutral")
        emotions = result.get("emotion", {})
        
        return {
            "dominant_emotion": dominant,
            "dominant_emotion_cn": EMOTION_MAP.get(dominant, dominant),
            "scores": {k: round(v / 100, 3) for k, v in emotions.items()}
        }
    except Exception as e:
        return {"dominant_emotion": "unknown", "error": str(e)}
```

### 8.2 后端：情绪统计查询接口

```python
# routers/emotion.py
@router.get("/stats")
async def get_emotion_stats(
    student_id: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """
    返回情绪统计数据（用于 ECharts）
    返回格式：
    {
      "pie_data": [{"name": "开心", "value": 45}, ...],
      "line_data": {"dates": [...], "happy": [...], "neutral": [...]}
    }
    """
    pass

@router.get("/records")
async def get_emotion_records(student_id: str = None, db: Session = Depends(get_db)):
    """查询情绪详细记录（学号、时间、情绪类型）"""
    pass
```

### 8.3 前端：情绪统计页面

**`EmotionPage.vue` 核心功能：**

```javascript
// ECharts 情绪分布饼图配置
const pieOption = {
  title: { text: '班级情绪分布', left: 'center' },
  tooltip: { trigger: 'item' },
  legend: { bottom: '5%' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],   // 环形图
    data: emotionData.value   // [{ name: '开心', value: 45 }, ...]
  }]
}

// 情绪趋势折线图（按日期）
const lineOption = {
  title: { text: '情绪趋势（近7天）' },
  xAxis: { type: 'category', data: dates },
  yAxis: { type: 'value' },
  series: ['happy', 'neutral', 'sad'].map(e => ({
    name: EMOTION_MAP[e],
    type: 'line',
    smooth: true,
    data: emotionTrend[e]
  }))
}
```

- 筛选器：按学生、按日期范围筛选
- 支持查看单个学生的情绪历史明细表

### 8.4 验收标准

- [ ] 每次考勤时情绪同步记录到数据库（不阻塞主流程）
- [ ] 情绪统计饼图/折线图正常渲染
- [ ] 可按学号查询个人情绪历史
- [ ] 情绪标签中文显示

---

## 9. 第六阶段：系统安全与权限管理

**目标**：提升活体检测抗攻击能力，实现账号权限管理，完善异常处理  
**预计时间**：3 天  
**对应评分**：18 分

### 9.1 活体检测增强

**多帧眨眼检测（更强的防照片攻击）：**

```python
# 前端连续发送5帧，后端统计 EAR 变化
@router.post("/liveness/multi-frame")
async def multi_frame_liveness(frames: List[str]):  # List of base64
    ear_values = []
    for frame_b64 in frames:
        img_data = base64.b64decode(frame_b64.split(',')[1])
        result = liveness_service.liveness_check_single_frame(img_data)
        ear_values.append(result.get("ear", 0))
    
    # 检测 EAR 波动（眨眼会导致 EAR 骤降再回升）
    ear_variance = np.var(ear_values)
    blink_detected = any(e < 0.2 for e in ear_values) and max(ear_values) > 0.25
    
    return {
        "is_live": blink_detected or ear_variance > 0.005,
        "blink_detected": blink_detected,
        "ear_values": ear_values
    }
```

**防视频攻击（纹理分析）：**
- 使用 LBP（局部二值模式）检测图像纹理
- 屏幕播放视频的截图纹理与真实人脸纹理存在差异

### 9.2 JWT 权限认证

```python
# routers/auth.py
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480   # 8小时

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not pwd_context.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = jwt.encode(
        {"sub": user.username, "role": user.role, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """依赖注入：获取当前登录用户"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return {"username": username, "role": role}

def require_teacher(current_user=Depends(get_current_user)):
    """只有教师角色可访问"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="权限不足，需要教师账号")
    return current_user
```

**权限划分：**

| 功能 | 学生 | 教师 |
|------|------|------|
| 查看自己的考勤记录 | ✅ | ✅ |
| 考勤打卡 | ✅ | ✅ |
| 查看全班考勤记录 | ❌ | ✅ |
| 管理学生人脸库 | ❌ | ✅ |
| 上传合照/查看统计 | ❌ | ✅ |
| 导出 Excel | ❌ | ✅ |

### 9.3 异常处理规范

```python
# 统一异常处理
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "type": type(exc).__name__}
    )
```

**前端统一错误处理（axios 拦截器）：**

```javascript
// api/request.js
import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'

const request = axios.create({ baseURL: 'http://localhost:8000', timeout: 30000 })

request.interceptors.response.use(
  res => res.data,
  err => {
    const status = err.response?.status
    const errorMap = {
      400: '请求参数错误',
      401: '登录已过期，请重新登录',
      403: '权限不足',
      500: '服务器内部错误',
    }
    ElMessage.error(errorMap[status] || '网络异常，请稍后重试')
    if (status === 401) router.push('/login')
    return Promise.reject(err)
  }
)

export default request
```

**需处理的异常场景：**

| 场景 | 前端处理 | 后端处理 |
|------|---------|---------|
| 摄像头调用失败 | 提示"请允许摄像头权限"，显示说明图 | — |
| 照片上传失败（超大文件） | 前端限制 ≤ 10MB，上传前校验 | 返回 413 错误 |
| 人脸识别超时 | 30s 超时提示，可重试 | 设置 `timeout` 参数 |
| 活体检测不通过 | 提示"请正视摄像头并眨眼" | 返回具体原因 |
| 未检测到人脸 | 提示"未检测到人脸，请调整光线" | 返回 step: detection |
| 网络断开 | axios timeout 捕获，提示重试 | — |

### 9.4 验收标准

- [ ] 直接对照片拍照打卡被活体检测拦截
- [ ] 教师/学生账号登录后功能菜单按权限显示
- [ ] Token 过期后自动跳转登录页
- [ ] 摄像头调用失败有友好提示（不崩溃）
- [ ] 上传超大文件（>10MB）有错误提示

---

## 10. 前端页面规划

### 10.1 页面列表

| 页面 | 路由 | 权限 |
|------|------|------|
| 登录页 | `/login` | 公开 |
| 考勤打卡 | `/attendance` | 全部 |
| 合照识别 | `/group-photo` | 教师 |
| 情绪统计 | `/emotion` | 教师 |
| 学生管理 | `/students` | 教师 |
| 考勤记录查询 | `/records` | 全部（学生只能看自己） |

### 10.2 布局结构

```
App.vue
├── LoginPage.vue         （未登录时显示）
└── MainLayout.vue        （登录后的主框架）
    ├── NavSidebar.vue    （左侧导航栏，根据角色显示菜单）
    ├── TopHeader.vue     （顶部：用户名、角色标签、退出按钮）
    └── <router-view>     （右侧内容区域）
        ├── AttendancePage.vue
        ├── GroupPhotoPage.vue
        ├── EmotionPage.vue
        ├── StudentManage.vue
        └── RecordsPage.vue
```

---

## 11. API 接口汇总

### 认证模块

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/auth/login` | 用户登录，返回 JWT |
| GET | `/auth/me` | 获取当前用户信息 |

### 学生管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/students/list` | 获取所有学生 |
| POST | `/students/add` | 添加学生（含照片） |
| PUT | `/students/{id}` | 修改学生信息 |
| DELETE | `/students/{id}` | 删除学生 |
| POST | `/students/batch-import` | CSV 批量导入 |

### 考勤模块

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/attendance/check` | 提交考勤（单帧） |
| POST | `/attendance/liveness` | 多帧活体检测 |
| GET | `/attendance/records` | 查询考勤记录 |
| GET | `/attendance/sessions` | 获取考勤场次列表 |

### 合照识别

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/photo/recognize` | 上传合照并识别 |
| GET | `/photo/list` | 历史合照列表 |
| GET | `/photo/activity-stats` | 活动参与统计 |

### 情绪分析

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/emotion/stats` | 情绪统计（饼图/折线图数据） |
| GET | `/emotion/records` | 情绪详细记录 |

### 导出

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/export/attendance/excel` | 导出考勤 Excel |
| GET | `/export/activity/excel` | 导出活动名单 Excel |

---

## 12. 测试计划

### 12.1 功能测试

| 测试项 | 测试方法 | 通过标准 |
|--------|---------|---------|
| 人脸录入 | 上传 5 名同学照片（正面、侧面各一张） | 全部提取编码成功 |
| 正常考勤 | 5 名同学逐一打卡 | 识别准确率 ≥ 90% |
| 活体检测 | 对屏幕上的照片截图尝试打卡 | 全部拦截 |
| 合照识别 | 上传 10 人以上合照 | 识别准确率 ≥ 85% |
| 情绪分析 | 做出开心、平静、惊讶表情各打卡一次 | 情绪标签与实际基本吻合 |
| Excel 导出 | 导出考勤记录 | 文件可正常打开，数据完整 |
| 权限隔离 | 用学生账号访问教师功能 | 返回 403，前端跳转或隐藏菜单 |

### 12.2 性能测试

- 单次考勤响应时间 ≤ 3 秒
- 10 人合照识别完成时间 ≤ 30 秒
- 并发 3 人同时打卡不崩溃

---

## 13. 课程报告结构建议

对应评分 **30 分**（报告 20 分 + 源码 10 分）

```
一、需求分析（约 3 页）
  1.1 项目背景与意义
  1.2 功能性需求分析
  1.3 非功能性需求（性能、安全、可用性）
  1.4 用例图

二、系统设计（约 5 页）
  2.1 总体架构设计（BS 架构图）
  2.2 模块划分与说明
  2.3 数据库设计（E-R 图 + 表结构）
  2.4 API 接口设计
  2.5 关键算法说明（活体检测 EAR 原理、人脸比对原理）

三、代码实现（约 6 页）
  3.1 开发环境与配置
  3.2 核心功能实现（附关键代码片段）
    - 人脸编码提取与比对
    - 活体检测实现
    - 合照批量识别
    - 情绪分析集成
  3.3 前端关键组件实现
  3.4 权限认证实现

四、结果分析（约 3 页）
  4.1 系统运行截图
  4.2 功能测试结果（表格形式）
  4.3 性能测试结果
  4.4 识别准确率分析
  4.5 问题与改进方向

五、总结（约 1 页）
```

---

## 14. 分工建议

### 3 人团队推荐分工

| 成员 | 职责 |
|------|------|
| 成员 A（后端负责人） | FastAPI 项目搭建、人脸识别服务、活体检测、数据库设计、JWT 认证 |
| 成员 B（前端负责人） | Vue 3 项目搭建、考勤页、学生管理页、合照上传页、ECharts 图表 |
| 成员 C（全栈 + 报告） | 情绪分析接口、Excel 导出、异常处理、系统测试、课程报告撰写 |

### 2 人团队推荐分工

| 成员 | 职责 |
|------|------|
| 成员 A（后端为主） | 全部后端接口、数据库、人脸识别算法、活体检测、安全模块 |
| 成员 B（前端为主） | 全部前端页面、ECharts、API 集成、测试、课程报告 |

---

## 15. 开发日程表

| 周次 | 任务 | 产出 |
|------|------|------|
| 第 1 周 | 项目初始化、环境搭建、数据库建表 | 前后端跑通，Swagger 文档可访问 |
| 第 2 周 | 人脸库管理（后端 + 前端学生管理页） | 可添加/删除/查询学生人脸 |
| 第 3-4 周 | 基础考勤功能（摄像头 + 活体 + 比对） | 完整考勤流程可用，可导出 Excel |
| 第 5-6 周 | 合照识别功能（批量比对 + 统计报表） | 合照上传识别可用，柱状图展示 |
| 第 7 周 | 情绪分析功能 | 情绪饼图/折线图展示 |
| 第 8-9 周 | 安全加固（JWT 权限 + 异常处理 + 活体增强） | 权限管理完善，抗攻击能力提升 |
| 第 10 周 | 系统联调、Bug 修复、测试 | 系统稳定可演示 |
| 第 11 周 | 课程报告完善、验收准备 | 报告完稿，系统可演示 |

---

*最后更新：按实际进度动态调整，建议每周 Code Review 一次*
