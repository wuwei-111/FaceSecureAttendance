"""上传文件校验：大小、图像魔数（降低异常文件与非图风险）。"""

import os

from fastapi import HTTPException, UploadFile

# 单次上传图片默认上限（可通过环境变量 MAX_UPLOAD_IMAGE_MB 覆盖）

MAX_IMAGE_BYTES = int(os.getenv("MAX_UPLOAD_IMAGE_MB", "15")) * 1024 * 1024
MAX_CSV_BYTES = int(os.getenv("MAX_UPLOAD_CSV_MB", "5")) * 1024 * 1024


def validate_image_magic(content: bytes) -> None:
    if len(content) < 12:
        raise HTTPException(status_code=400, detail="文件过小或为空")
    head = content[:12]
    # JPEG / PNG / GIF / WEBP(RIFF....WEBP)
    if head[0:3] == b"\xff\xd8\xff":
        return
    if head[0:8] == b"\x89PNG\r\n\x1a\n":
        return
    if head[0:6] in (b"GIF87a", b"GIF89a"):
        return
    if head[0:4] == b"RIFF" and content[8:12] == b"WEBP":
        return
    raise HTTPException(status_code=415, detail="仅支持 JPG / PNG / GIF / WEBP 图片")


def validate_image_bytes(content: bytes, max_bytes: int = MAX_IMAGE_BYTES) -> None:
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"文件过大（上限 {max_bytes // (1024 * 1024)}MB）")
    validate_image_magic(content)


async def read_uploaded_image(upload: UploadFile, max_bytes: int = MAX_IMAGE_BYTES) -> bytes:
    raw = await upload.read()
    validate_image_bytes(raw, max_bytes=max_bytes)
    return raw


def validate_text_upload_bytes(content: bytes, max_bytes: int = MAX_CSV_BYTES) -> None:
    """CSV / 文本类批量导入：限制体积，防止超大文件拖垮解析。"""
    if len(content) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"文件过大（上限 {mb}MB）")
