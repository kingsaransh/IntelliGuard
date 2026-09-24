import io
import csv
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse

from app.config import settings
from app.database import get_incidents, update_incident_status
from app.models import IncidentResponse, IncidentUpdateStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/incidents", tags=["incidents"])

@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    limit: int = Query(50, ge=1, le=500),
    threat_type: Optional[str] = "ALL",
    severity: Optional[str] = "ALL"
):
    """Retrieve filtered incident log"""
    return get_incidents(limit=limit, threat_type=threat_type, severity=severity)

@router.put("/{incident_id}/status")
def change_incident_status(incident_id: int, payload: IncidentUpdateStatus):
    """Acknowledge or resolve an incident"""
    success = update_incident_status(incident_id, payload.status)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "success", "id": incident_id, "new_status": payload.status}

@router.get("/screenshot/{filename}")
def get_incident_screenshot(filename: str):
    """Serve annotated incident screenshot evidence image"""
    filepath = Path(settings.INCIDENTS_DIR) / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Incident screenshot not found")
    return FileResponse(str(filepath), media_type="image/jpeg")

@router.get("/export")
def export_incidents_csv():
    """Export all incidents as CSV report"""
    incidents = get_incidents(limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Timestamp", "Camera ID", "Threat Type", "Severity", "Confidence", "Track ID", "Description", "Status"])
    for inc in incidents:
        writer.writerow([
            inc["id"],
            inc["timestamp"],
            inc["camera_id"],
            inc["threat_type"],
            inc["severity"],
            inc["confidence"],
            inc["track_id"] or "N/A",
            inc["description"] or "",
            inc["status"]
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=intelliguard_incident_report.csv"}
    )
