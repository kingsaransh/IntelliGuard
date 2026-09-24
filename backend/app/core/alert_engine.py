import cv2
import time
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.database import insert_incident

logger = logging.getLogger(__name__)

class AlertEngine:
    """
    Central Incident & Threat Notification Engine:
    - Implements cooldown timers per incident type and track ID
    - Annotates and exports high-resolution incident screenshots
    - Stores incident metadata in SQLite
    - Dispatches alerts to active WebSocket sessions and external handlers
    """
    def __init__(self):
        # (threat_type, track_id) -> last_alert_time
        self.last_alerts: Dict[str, float] = {}
        self.websocket_listeners: List[Any] = []

    def register_websocket(self, ws):
        self.websocket_listeners.append(ws)
        logger.info(f"WebSocket client connected. Total listeners: {len(self.websocket_listeners)}")

    def unregister_websocket(self, ws):
        if ws in self.websocket_listeners:
            self.websocket_listeners.remove(ws)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.websocket_listeners)}")

    async def broadcast_ws(self, message: Dict[str, Any]):
        dead_sockets = []
        payload_str = json.dumps(message)
        for ws in self.websocket_listeners:
            try:
                await ws.send_text(payload_str)
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            if ws in self.websocket_listeners:
                self.websocket_listeners.remove(ws)

    def process_threats(self, threats: List[Dict[str, Any]], frame: Optional[np.ndarray], camera_id: str) -> List[Dict[str, Any]]:
        dispatched_incidents: List[Dict[str, Any]] = []
        if not threats:
            return dispatched_incidents

        now = time.time()

        for threat in threats:
            threat_type = threat["threat_type"]
            track_id = threat.get("track_id")
            cooldown_key = f"{camera_id}_{threat_type}_{track_id}"

            last_time = self.last_alerts.get(cooldown_key, 0.0)
            if now - last_time < settings.ALERT_COOLDOWN_SEC:
                # In cooldown, skip duplicate alarm
                continue

            self.last_alerts[cooldown_key] = now

            # 1. Save annotated screenshot evidence
            screenshot_rel_path = None
            if frame is not None:
                screenshot_rel_path = self._save_incident_screenshot(frame, threat)

            # 2. Persist incident to SQLite
            incident_id = insert_incident(
                camera_id=camera_id,
                threat_type=threat_type,
                severity=threat.get("severity", "HIGH"),
                confidence=threat.get("confidence", 0.85),
                track_id=track_id,
                description=threat.get("description", "Threat detected"),
                screenshot_path=screenshot_rel_path,
                metadata=threat
            )

            threat_record = {
                "id": incident_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "camera_id": camera_id,
                "threat_type": threat_type,
                "severity": threat.get("severity", "HIGH"),
                "confidence": threat.get("confidence", 0.85),
                "track_id": track_id,
                "description": threat.get("description", ""),
                "screenshot_path": screenshot_rel_path,
                "status": "NEW"
            }
            dispatched_incidents.append(threat_record)

            logger.warning(f"🚨 [ALERT DISPATCHED] ID={incident_id} Type={threat_type} Severity={threat.get('severity')} Conf={threat.get('confidence')}")

        return dispatched_incidents

    def _save_incident_screenshot(self, frame: np.ndarray, threat: Dict[str, Any]) -> str:
        try:
            annotated = frame.copy()
            h, w, _ = annotated.shape
            bbox = threat.get("bbox")
            threat_type = threat.get("threat_type", "INCIDENT")
            severity = threat.get("severity", "HIGH")
            conf = threat.get("confidence", 0.0)

            # Draw prominent threat target box
            if bbox:
                x1, y1, x2, y2 = bbox
                color = (0, 0, 255) if severity == "CRITICAL" else (0, 140, 255)
                # Outer glow and rectangle
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
                # Corner reticles
                c_len = min(20, (x2 - x1) // 3)
                cv2.line(annotated, (x1, y1), (x1 + c_len, y1), (255, 255, 255), 2)
                cv2.line(annotated, (x1, y1), (x1, y1 + c_len), (255, 255, 255), 2)
                cv2.line(annotated, (x2, y2), (x2 - c_len, y2), (255, 255, 255), 2)
                cv2.line(annotated, (x2, y2), (x2, y2 - c_len), (255, 255, 255), 2)

                # Threat tag banner
                tag = f"ALERT: {threat_type} [{int(conf * 100)}%]"
                cv2.rectangle(annotated, (x1, max(0, y1 - 28)), (x1 + len(tag) * 11, max(0, y1)), color, -1)
                cv2.putText(annotated, tag, (x1 + 4, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Add incident timestamp banner at bottom
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            banner_text = f"INTELLIGUARD EVIDENCE VAULT | {threat_type} | CONF: {conf:.2f} | {now_str}"
            cv2.rectangle(annotated, (0, h - 35), (w, h), (15, 18, 26), -1)
            cv2.putText(annotated, banner_text, (20, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 1)

            filename = f"evidence_{int(time.time())}_{threat_type.lower()}.jpg"
            filepath = Path(settings.INCIDENTS_DIR) / filename
            cv2.imwrite(str(filepath), annotated)

            return f"/api/incidents/screenshot/{filename}"
        except Exception as e:
            logger.error(f"Error saving incident screenshot: {e}")
            return ""
