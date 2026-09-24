import base64
import cv2
import numpy as np
import logging
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.database import get_all_authorized_faces, delete_authorized_face
from app.models import FaceResponse, FaceEnrollRequest
from app.core.pipeline import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/faces", tags=["faces"])

@router.get("", response_model=List[FaceResponse])
def list_authorized_faces():
    """Retrieve list of authorized personnel"""
    return get_all_authorized_faces()

@router.post("/enroll")
async def enroll_face_upload(
    name: str = Form(...),
    role: str = Form(...),
    department: str = Form("Security"),
    file: UploadFile = File(...)
):
    """Enroll a new authorized person via image upload"""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")

    success, msg = pipeline.face_recognizer.enroll_from_frame(name, role, department, img)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"status": "success", "message": msg}

@router.post("/enroll_base64")
def enroll_face_base64(payload: FaceEnrollRequest):
    """Enroll a new authorized person using base64 image (e.g. from webcam capture)"""
    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="No image provided")

    try:
        # Strip data URL prefix if present
        b64_data = payload.image_base64
        if "," in b64_data:
            b64_data = b64_data.split(",")[1]

        image_bytes = base64.b64decode(b64_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode base64 image: {e}")

    success, msg = pipeline.face_recognizer.enroll_from_frame(
        payload.name, payload.role, payload.department or "General", img
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"status": "success", "message": msg}

@router.delete("/{face_id}")
def remove_authorized_face(face_id: int):
    """Remove a person from the authorized access list"""
    success = delete_authorized_face(face_id)
    if not success:
        raise HTTPException(status_code=404, detail="Face record not found")
    pipeline.face_recognizer.load_known_faces()
    return {"status": "success", "message": "Face record removed"}
