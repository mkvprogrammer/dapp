"""
HTTP-ручки загрузки файлов (изображения для аукционов и проектов).
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["Uploads"])

MAX_SIZE = 2 * 1024 * 1024
ALLOWED = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


class ImageUploadResponse(BaseModel):
    """Ответ после успешной загрузки изображения."""

    url: str = Field(..., description="Публичный URL файла (/uploads/...)")
    filename: str = Field(..., description="Имя файла на диске")
    size_bytes: int = Field(..., description="Размер в байтах")


@router.post("/images", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> ImageUploadResponse:
    """Загрузка изображения (PNG/JPG/WEBP, до 2 МБ) в каталог uploads."""
    if file.content_type not in ALLOWED:
        raise HTTPException(400, "Допустимы только PNG, JPG, WEBP")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "Файл больше 2 МБ")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "img.png").suffix or ".png"
    name = f"{uuid.uuid4().hex}{ext}"
    path = upload_dir / name
    path.write_bytes(data)
    return ImageUploadResponse(
        url=f"/uploads/{name}",
        filename=name,
        size_bytes=len(data),
    )
