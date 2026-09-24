from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class IncidentCreate(BaseModel):
    camera_id: str
    threat_type: str
    severity: str
    confidence: float
    track_id: Optional[int] = None
    description: str
    screenshot_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IncidentResponse(BaseModel):
    id: int
    timestamp: str
    camera_id: str
    threat_type: str
    severity: str
    confidence: float
    track_id: Optional[int]
    description: Optional[str]
    screenshot_path: Optional[str]
    status: str
    metadata_json: Optional[str]
    created_at: str

class IncidentUpdateStatus(BaseModel):
    status: str  # 'ACKNOWLEDGED', 'RESOLVED', 'FALSE_ALARM'

class FaceEnrollRequest(BaseModel):
    name: str
    role: str
    department: Optional[str] = "General"
    image_base64: Optional[str] = None

class FaceResponse(BaseModel):
    id: int
    name: str
    role: str
    department: Optional[str]
    photo_path: Optional[str]
    created_at: str

class CameraItem(BaseModel):
    id: str
    name: str
    source_type: str
    source_url: str
    location: Optional[str]
    active: int

class CameraSwitchRequest(BaseModel):
    camera_id: str
    source_type: Optional[str] = None
    source_url: Optional[str] = None

class SystemStatusResponse(BaseModel):
    system: str
    version: str
    fps: float
    camera_id: str
    source_type: str
    persons_detected: int
    active_threats: int
    threat_level: str
    modules_active: Dict[str, bool]
