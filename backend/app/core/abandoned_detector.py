import time
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

class AbandonedObjectDetector:
    """
    Suspicious Unattended Baggage / Abandoned Object Detection Engine.
    Monitors bags, backpacks, and luggage:
    1. Identifies if luggage has no owner within proximity threshold.
    2. Measures continuous stationary elapsed time.
    3. Triggers alert if unattended time exceeds threshold.
    """
    def __init__(self):
        # track_id -> {first_seen, last_seen, last_centroid, unattended_start_time, is_unattended}
        self.tracked_objects: Dict[int, Dict[str, Any]] = {}

    def process(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        threats: List[Dict[str, Any]] = []
        if frame is None:
            return threats

        current_time = time.time()
        
        # Separate persons and luggage
        persons = [d for d in detections if d.get("class_name") == "person"]
        bags = [d for d in detections if d.get("class_name") in ("backpack", "handbag", "suitcase")]

        # Also, in synthetic simulator, a simulated bag detection might appear as an object
        # We can also detect custom unattended regions if simulated
        active_bag_ids = set()

        for bag in bags:
            track_id = bag["track_id"]
            active_bag_ids.add(track_id)
            bx, by = bag["centroid"]
            bbox = bag["bbox"]

            # Initialize track if new
            if track_id not in self.tracked_objects:
                self.tracked_objects[track_id] = {
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "last_centroid": (bx, by),
                    "unattended_start": None,
                    "stationary_count": 0,
                    "bbox": bbox
                }

            obj = self.tracked_objects[track_id]
            obj["last_seen"] = current_time
            obj["bbox"] = bbox

            # Check if bag is stationary (centroid displacement is minimal)
            last_bx, last_by = obj["last_centroid"]
            disp = np.sqrt((bx - last_bx)**2 + (by - last_by)**2)
            if disp < 15.0:
                obj["stationary_count"] += 1
            else:
                obj["stationary_count"] = max(0, obj["stationary_count"] - 1)
                obj["unattended_start"] = None  # Moved by someone

            obj["last_centroid"] = (bx, by)

            # Find distance to nearest person
            min_person_dist = float("inf")
            for person in persons:
                px, py = person["centroid"]
                dist = np.sqrt((bx - px)**2 + (by - py)**2)
                if dist < min_person_dist:
                    min_person_dist = dist

            is_separated = (min_person_dist > settings.ABANDONED_OBJECT_DISTANCE_PX)

            if is_separated and obj["stationary_count"] >= 5:
                # Bag is alone and stationary
                if obj["unattended_start"] is None:
                    obj["unattended_start"] = current_time

                elapsed_unattended = current_time - obj["unattended_start"]

                if elapsed_unattended >= settings.ABANDONED_OBJECT_TIME_SEC:
                    confidence = min(0.96, 0.70 + (elapsed_unattended - settings.ABANDONED_OBJECT_TIME_SEC) * 0.05)
                    threats.append({
                        "threat_type": "ABANDONED_OBJECT",
                        "severity": "HIGH",
                        "confidence": round(confidence, 3),
                        "track_id": track_id,
                        "bbox": bbox,
                        "description": f"Unattended {bag.get('class_name', 'bag')} detected stationary for {int(elapsed_unattended)}s with no owner nearby",
                        "elapsed_seconds": int(elapsed_unattended),
                        "distance_to_nearest_person": int(min_person_dist)
                    })
            else:
                # An owner is within range
                obj["unattended_start"] = None

        # Clean up expired bags
        for tid in list(self.tracked_objects.keys()):
            if tid not in active_bag_ids:
                if current_time - self.tracked_objects[tid]["last_seen"] > 8.0:
                    del self.tracked_objects[tid]

        return threats
