"""Uploads MVP: local disk storage; S3 presigned-URL path when USE_S3=true."""
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.deps import get_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
PREVIEWS = os.path.join(BASE, "previews")
FILES = os.path.join(BASE, "files")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(FILES, exist_ok=True)


def mount_static(app):
    # Only previews are public. Project zips stay locked: served solely via
    # the token-gated /orders/{id}/download endpoint (FileResponse).
    app.mount("/uploads/previews", StaticFiles(directory=PREVIEWS), name="previews")


MAX_PREVIEW_BYTES = 5 * 1024 * 1024
MAX_ZIP_BYTES = 50 * 1024 * 1024


def _image_kind(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return ""


@router.post("/preview")
async def upload_preview(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    data = await file.read()
    if len(data) > MAX_PREVIEW_BYTES:
        raise HTTPException(400, "Preview too large (max 5MB)")
    kind = _image_kind(data)
    if not kind:
        raise HTTPException(400, "Only real image files allowed for previews")
    ext = { "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp" }[kind]
    name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(PREVIEWS, name)
    with open(dest, "wb") as f:
        f.write(data)
    if settings.USE_S3 and settings.S3_BUCKET:
        import boto3
        s3 = boto3.client("s3", region_name=settings.AWS_REGION,
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        s3.upload_file(dest, settings.S3_BUCKET, f"previews/{name}", ExtraArgs={"ContentType": file.content_type})
        url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/previews/{name}"
        return {"url": url}
    return {"url": f"/uploads/previews/{name}"}


@router.post("/project-file")
async def upload_project_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    import hashlib
    from app.db import database as db
    if user.get("role") not in ("seller", "both", "admin"):
        raise HTTPException(403, "Only sellers can upload project files")
    if not (file.filename or "").endswith(".zip"):
        raise HTTPException(400, "Project file must be a .zip")
    data = await file.read()
    if len(data) > MAX_ZIP_BYTES:
        raise HTTPException(400, "Project file too large (max 50MB)")
    if not data.startswith(b"PK"):
        raise HTTPException(400, "Project file must be a real .zip archive")
    digest = hashlib.sha256(data).hexdigest()
    name = f"{uuid.uuid4().hex}.zip"
    dest = os.path.join(FILES, name)
    with open(dest, "wb") as f:
        f.write(data)
    dup = await db.listings().find_one({"file_hash": digest})
    # Locked: served only via signed /orders/{id}/download, never listed publicly.
    return {"key": f"locked:files/{name}",
            "file_hash": digest,
            "duplicate_warning": bool(dup),
            "note": "Locked until purchase completes"}


@router.post("/similarity-check")
async def similarity_check(body: dict, user: dict = Depends(get_current_user)):
    """Code similarity stub (wire MOSS / plagiarism API in prod)."""
    return {"score": 0.0, "flagged": False,
            "note": "Stub — integrate MOSS or similar API for real code similarity"}


@router.get("/s3-presigned")
async def s3_presigned(filename: str, user: dict = Depends(get_current_user)):
    if not (settings.USE_S3 and settings.S3_BUCKET):
        return {"mode": "local", "note": "Set USE_S3=true + bucket for real presigned URLs"}
    import boto3
    s3 = boto3.client("s3", region_name=settings.AWS_REGION,
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    url = s3.generate_presigned_url("put_object", Params={"Bucket": settings.S3_BUCKET, "Key": f"uploads/{filename}"}, ExpiresIn=3600)
    return {"url": url}
