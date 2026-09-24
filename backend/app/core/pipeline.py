import cv2
import time
import asyncio
import logging
import threading
import numpy as np
from typing import Optional, Dict, Any, List

from app.config import settings
from app.core.video_stream import VideoStreamManager
from app.core.detector import ObjectDetector
from app.core.fight_detector import FightViolenceDetector
from app.core.fall_detector import FallDetector
from app.core.abandoned_detector import AbandonedObjectDetector
from app.core.face_recognizer import FaceRecognizerEngine
from app.core.alert_engine import AlertEngine

logger = logging.getLogger(__name__)

class MasterPipeline:
    """
    Central AI Surveillance Orchestrator.
    Integrates all deep learning detection modules, video capture,
    HUD rendering, and real-time incident dispatching.
    """
    def __init__(self):
        self.stream_manager = VideoStreamManager(source=settings.DEFAULT_SOURCE)
        self.detector = ObjectDetector()
        self.fight_detector = FightViolenceDetector()
        self.fall_detector = FallDetector()
        self.abandoned_detector = AbandonedObjectDetector()
        self.face_recognizer = FaceRecognizerEngine()
        self.alert_engine = AlertEngine()

        self.current_camera_id = "cam-1"
        self.is_running = False
        self.processed_jpeg: Optional[bytes] = None
        self.lock = threading.Lock()
        
        # Telemetry stats
        self.fps = 0.0
        self.person_count = 0
        self.active_threats: List[Dict[str, Any]] = []
        self.last_pipeline_time = time.time()
        
        # Feature toggles
        self.features_enabled = {
            "person_tracking": True,
            "fight_detection": True,
            "fall_detection": True,
            "abandoned_detection": True,
            "face_recognition": True
        }

        self.worker_thread: Optional[threading.Thread] = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.stream_manager.start()
        self.worker_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Master AI Surveillance Pipeline started.")

    def stop(self):
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        self.stream_manager.stop()
        logger.info("Master AI Surveillance Pipeline stopped.")

    def change_camera(self, camera_id: str, source_type: str, source_url: str):
        self.current_camera_id = camera_id
        actual_source = "demo" if source_type == "demo" else source_url
        self.stream_manager.change_source(actual_source)
        logger.info(f"Pipeline switched to Camera: {camera_id} ({source_type})")

    def _processing_loop(self):
        while self.is_running:
            start_time = time.time()
            frame = self.stream_manager.get_latest_frame()

            if frame is None:
                time.sleep(0.01)
                continue

            annotated_frame = frame.copy()
            current_threats: List[Dict[str, Any]] = []

            # 1. YOLO Object Detection & Tracking
            detections = []
            if self.features_enabled["person_tracking"]:
                detections = self.detector.detect_and_track(frame)
                self.person_count = len([d for d in detections if d.get("class_name") == "person"])
            else:
                self.person_count = 0

            # 2. Fight / Violence Altercation Detection
            if self.features_enabled["fight_detection"]:
                fight_threats = self.fight_detector.process(frame, detections)
                current_threats.extend(fight_threats)

            # 3. Fall & Emergency Detection
            if self.features_enabled["fall_detection"]:
                fall_threats = self.fall_detector.process(frame, detections)
                current_threats.extend(fall_threats)

            # 4. Abandoned Object Detection
            if self.features_enabled["abandoned_detection"]:
                bag_threats = self.abandoned_detector.process(frame, detections)
                current_threats.extend(bag_threats)

            # 5. Face Recognition & Clearance
            faces = []
            if self.features_enabled["face_recognition"]:
                faces, face_threats = self.face_recognizer.process(frame)
                current_threats.extend(face_threats)

            # 6. Process New Threats & Save Incidents
            new_incidents = self.alert_engine.process_threats(current_threats, frame, self.current_camera_id)
            self.active_threats = current_threats

            # 7. Render Rich Cyber-SOC Visual HUD Overlay
            self._render_hud_overlay(annotated_frame, detections, faces, current_threats)

            # 8. Encode JPEG for MJPEG stream
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                with self.lock:
                    self.processed_jpeg = buffer.tobytes()

            # Calculate FPS
            dt = time.time() - start_time
            if dt > 0:
                self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)

            # Small yield for threading responsiveness
            time.sleep(0.005)

    def _render_hud_overlay(self, img: np.ndarray, detections: List[Dict[str, Any]], faces: List[Dict[str, Any]], threats: List[Dict[str, Any]]):
        h, w, _ = img.shape
        threat_track_ids = {t.get("track_id") for t in threats if t.get("track_id") is not None}

        # Draw Object / Person Bounding Boxes
        for d in detections:
            track_id = d["track_id"]
            cls_name = d["class_name"]
            x1, y1, x2, y2 = d["bbox"]
            conf = d["confidence"]

            if track_id in threat_track_ids:
                # Highlight in crimson alert
                color = (0, 0, 255)
                box_thickness = 3
            elif cls_name == "person":
                color = (0, 240, 120)  # Neon green
                box_thickness = 2
            else:
                color = (255, 180, 50)  # Amber for bags
                box_thickness = 2

            # Draw rounded/corner styled box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, box_thickness)
            
            # Corner accents
            c_len = min(14, (x2 - x1) // 4)
            cv2.line(img, (x1, y1), (x1 + c_len, y1), (255, 255, 255), 2)
            cv2.line(img, (x1, y1), (x1, y1 + c_len), (255, 255, 255), 2)

            # Label tag
            label = f"#{track_id} {cls_name.upper()} {int(conf*100)}%"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(img, (x1, max(0, y1 - 20)), (x1 + label_size[0] + 8, max(0, y1)), color, -1)
            cv2.putText(img, label, (x1 + 4, max(14, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (10, 15, 25), 1)

        # Draw Face Recognition Tags
        for face in faces:
            left, top, right, bottom = face["bbox"]
            is_auth = face["is_authorized"]
            name = face["name"]
            role = face["role"]

            f_color = (0, 240, 255) if is_auth else (0, 50, 255)  # Cyan for authorized, Red for unauthorized
            cv2.rectangle(img, (left, top), (right, bottom), f_color, 2)
            
            tag = f"{name} ({role})"
            cv2.rectangle(img, (left, max(0, top - 20)), (left + len(tag) * 8 + 6, max(0, top)), f_color, -1)
            cv2.putText(img, tag, (left + 3, max(14, top - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (10, 15, 25), 1)

        # Draw Active Threat Flashes and Banners
        for t in threats:
            bbox = t.get("bbox")
            threat_type = t.get("threat_type")
            conf = t.get("confidence", 0.0)

            if bbox:
                x1, y1, x2, y2 = bbox
                # Glowing outer border
                cv2.rectangle(img, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), (0, 0, 255), 2)
                alert_text = f"THREAT: {threat_type} ({int(conf*100)}%)"
                cv2.rectangle(img, (x1, max(0, y1 - 45)), (x1 + len(alert_text) * 11, max(0, y1 - 20)), (0, 0, 255), -1)
                cv2.putText(img, alert_text, (x1 + 6, max(14, y1 - 26)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)

        # Top System HUD Telemetry Ribbon
        hud_bg = (15, 20, 28)
        cv2.rectangle(img, (0, 0), (w, 36), hud_bg, -1)
        cv2.line(img, (0, 36), (w, 36), (0, 240, 255), 1)

        # Telemetry metrics
        fps_text = f"FPS: {self.fps:.1f}"
        cam_text = f"ID: {self.current_camera_id.upper()}"
        persons_text = f"PERSONS: {self.person_count}"
        threats_count = len(threats)
        threat_text = f"THREATS: {threats_count}"
        threat_color = (0, 0, 255) if threats_count > 0 else (0, 240, 100)

        cv2.putText(img, "INTELLIGUARD AI CORE", (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 2)
        cv2.putText(img, cam_text, (240, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 200, 220), 1)
        cv2.putText(img, fps_text, (370, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 200), 1)
        cv2.putText(img, persons_text, (480, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 220, 240), 1)
        cv2.putText(img, threat_text, (620, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, threat_color, 2)

        # Blinking REC dot
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(img, (w - 30, 18), 7, (0, 0, 255), -1)
            cv2.putText(img, "REC", (w - 75, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 2)

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self.lock:
            return self.processed_jpeg

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "camera_id": self.current_camera_id,
            "fps": round(self.fps, 1),
            "persons_detected": self.person_count,
            "active_threats_count": len(self.active_threats),
            "active_threats": self.active_threats,
            "threat_level": "CRITICAL" if any(t.get("severity") == "CRITICAL" for t in self.active_threats)
                            else ("HIGH" if len(self.active_threats) > 0 else "NORMAL"),
            "modules_active": self.features_enabled
        }

# Global singleton instance
pipeline = MasterPipeline()
