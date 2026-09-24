import time
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from collections import deque
from app.config import settings

logger = logging.getLogger(__name__)

class FallDetector:
    """
    Real-Time Fall and Medical Emergency Detection Engine.
    Detects sudden collapse, slip, and prolonged ground incapacitation by analyzing:
    1. Centroid Vertical Velocity (rapid downward plunge)
    2. Geometric Aspect Ratio Inversion (H/W flips from ~2.5+ to < 0.85)
    3. Ground Persistence (subject remains immobilized horizontally)
    """
    def __init__(self, history_length: int = 30):
        self.history_length = history_length
        # track_id -> deque of (timestamp, centroid_y, aspect_ratio, bbox)
        self.tracks_history: Dict[int, deque] = {}
        # track_id -> consecutive frames detected lying down
        self.lying_down_frames: Dict[int, int] = {}

    def process(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        threats: List[Dict[str, Any]] = []
        if frame is None:
            return threats

        current_time = time.time()
        active_track_ids = set()

        # Filter person detections
        persons = [d for d in detections if d.get("class_name") == "person"]

        for person in persons:
            track_id = person["track_id"]
            active_track_ids.add(track_id)

            cx, cy = person["centroid"]
            aspect_ratio = person["aspect_ratio"]  # h / w
            bbox = person["bbox"]

            if track_id not in self.tracks_history:
                self.tracks_history[track_id] = deque(maxlen=self.history_length)
                self.lying_down_frames[track_id] = 0

            history = self.tracks_history[track_id]
            history.append((current_time, cy, aspect_ratio, bbox))

            # Need at least 5 frames to measure velocity
            if len(history) < 5:
                continue

            # 1. Measure Vertical Descent Velocity
            old_time, old_cy, old_ar, _ = history[0]
            dt = current_time - old_time
            if dt > 0:
                vel_y = (cy - old_cy) / dt  # Positive means moving downwards
            else:
                vel_y = 0.0

            # 2. Check Horizontal Orientation (Aspect Ratio < 0.85 indicates lying down)
            is_horizontal = aspect_ratio < settings.FALL_ASPECT_RATIO_MAX

            if is_horizontal:
                self.lying_down_frames[track_id] += 1
            else:
                # If upright, reset lying counter gradually
                self.lying_down_frames[track_id] = max(0, self.lying_down_frames[track_id] - 2)

            consecutive_lying = self.lying_down_frames[track_id]

            # 3. Decision Logic:
            # Case A: Rapid downward velocity followed by horizontal state
            # Case B: Sustained horizontal posture on floor (> settings.FALL_MIN_GROUND_FRAMES)
            is_rapid_fall = (vel_y > 45.0 and is_horizontal)
            is_sustained_down = (consecutive_lying >= settings.FALL_MIN_GROUND_FRAMES)

            if is_rapid_fall or is_sustained_down:
                # Compute confidence score
                conf_ar = min(1.0, max(0.0, (1.0 - aspect_ratio) * 1.5))
                conf_time = min(1.0, consecutive_lying / 15.0)
                conf_vel = min(1.0, max(0.0, vel_y / 80.0))
                
                confidence = 0.5 * conf_ar + 0.3 * conf_time + 0.2 * conf_vel
                confidence = round(min(0.98, max(0.72, confidence)), 3)

                threats.append({
                    "threat_type": "FALL_DETECTED",
                    "severity": "CRITICAL" if consecutive_lying > 15 else "HIGH",
                    "confidence": confidence,
                    "track_id": track_id,
                    "bbox": bbox,
                    "description": f"Person fall/collapse detected (Track #{track_id}, Aspect Ratio: {aspect_ratio:.2f}, Ground Time: {consecutive_lying} frames)",
                    "aspect_ratio": aspect_ratio,
                    "ground_frames": consecutive_lying
                })

        # Cleanup disappeared tracks
        for tid in list(self.tracks_history.keys()):
            if tid not in active_track_ids:
                if len(self.tracks_history[tid]) > 0:
                    last_time = self.tracks_history[tid][-1][0]
                    if current_time - last_time > 5.0:
                        del self.tracks_history[tid]
                        if tid in self.lying_down_frames:
                            del self.lying_down_frames[tid]

        return threats
