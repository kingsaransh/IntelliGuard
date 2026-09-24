import logging
from pydantic import BaseModel
from fastapi import APIRouter

from app.config import settings
from app.core.pipeline import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])

class ModuleToggleRequest(BaseModel):
    module_name: str
    enabled: bool

class TriggerTestAlertRequest(BaseModel):
    threat_type: str = "FIGHT_VIOLENCE"
    severity: str = "CRITICAL"
    description: str = "Manual simulated threat alarm triggered by operator"

@router.get("/status")
def get_system_status():
    """Retrieve system health, FPS, and detection telemetry"""
    telemetry = pipeline.get_telemetry()
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "OPERATIONAL",
        "fps": telemetry["fps"],
        "camera_id": telemetry["camera_id"],
        "persons_detected": telemetry["persons_detected"],
        "active_threats_count": telemetry["active_threats_count"],
        "threat_level": telemetry["threat_level"],
        "modules_active": telemetry["modules_active"]
    }

@router.post("/toggle_module")
def toggle_detection_module(payload: ModuleToggleRequest):
    """Enable or disable individual deep learning detection modules dynamically"""
    if payload.module_name in pipeline.features_enabled:
        pipeline.features_enabled[payload.module_name] = payload.enabled
        return {
            "status": "success",
            "module_name": payload.module_name,
            "enabled": payload.enabled
        }
    return {"status": "error", "message": f"Module {payload.module_name} not found"}

@router.post("/test_alert")
def trigger_test_alert(payload: TriggerTestAlertRequest):
    """Trigger a test alert to verify notification dispatch and audio alarm chime"""
    mock_threat = [{
        "threat_type": payload.threat_type,
        "severity": payload.severity,
        "confidence": 0.99,
        "track_id": 999,
        "bbox": [100, 100, 300, 400],
        "description": payload.description
    }]
    frame = pipeline.stream_manager.get_latest_frame()
    dispatched = pipeline.alert_engine.process_threats(mock_threat, frame, pipeline.current_camera_id)
    return {
        "status": "success",
        "dispatched": dispatched
    }
