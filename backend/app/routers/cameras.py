import shutil
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config import settings
from app.database import get_cameras_list, set_active_camera
from app.models import CameraItem, CameraSwitchRequest
from app.core.pipeline import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cameras", tags=["cameras"])

@router.get("", response_model=List[CameraItem])
def list_cameras():
    """List all configured surveillance cameras"""
    return get_cameras_list()

@router.post("/switch")
def switch_active_camera(payload: CameraSwitchRequest):
    """Switch active surveillance feed source"""
    cameras = get_cameras_list()
    target_cam = next((c for c in cameras if c["id"] == payload.camera_id), None)
    
    if not target_cam:
        raise HTTPException(status_code=404, detail="Camera ID not found")

    source_type = payload.source_type or target_cam["source_type"]
    source_url = payload.source_url or target_cam["source_url"]

    pipeline.change_camera(payload.camera_id, source_type, source_url)
    set_active_camera(payload.camera_id)

    return {
        "status": "success",
        "camera_id": payload.camera_id,
        "source_type": source_type,
        "source_url": source_url
    }

@router.post("/upload_video")
async def upload_surveillance_video(file: UploadFile = File(...)):
    """Upload custom video footage for anomaly detection and inference"""
    dest_path = Path(settings.MEDIA_DIR) / file.filename
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

    # Switch pipeline to this video file
    pipeline.change_camera("cam-uploaded", "file", str(dest_path))
    return {
        "status": "success",
        "message": f"Uploaded {file.filename} and set as active surveillance source",
        "file_path": str(dest_path)
    }
