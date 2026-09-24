import cv2
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO
from app.config import settings

logger = logging.getLogger(__name__)

# Target COCO class IDs:
# 0: person
# 24: backpack, 26: handbag, 28: suitcase
TARGET_CLASSES = {0: "person", 24: "backpack", 26: "handbag", 28: "suitcase"}

class CentroidTracker:
    """
    Lightweight fallback multi-object tracker for CPU real-time tracking
    Maintains persistent track IDs and trajectories across frames.
    """
    def __init__(self, max_disappeared: int = 30, max_distance: float = 80.0):
        self.next_id = 1
        self.objects: Dict[int, np.ndarray] = {}  # id -> centroid [cx, cy]
        self.disappeared: Dict[int, int] = {}
        self.history: Dict[int, List[Tuple[int, int]]] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, rects: List[Tuple[int, int, int, int]]) -> Dict[int, Tuple[int, int, int, int]]:
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
            return {}

        input_centroids = np.zeros((len(rects), 2), dtype=float)
        for i, (x1, y1, x2, y2) in enumerate(rects):
            input_centroids[i] = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

        if len(self.objects) == 0:
            assigned = {}
            for i in range(len(rects)):
                oid = self._register(input_centroids[i])
                assigned[oid] = rects[i]
            return assigned

        object_ids = list(self.objects.keys())
        object_centroids = np.array(list(self.objects.values()))

        # Compute pairwise distance matrix
        D = np.linalg.norm(object_centroids[:, np.newaxis] - input_centroids, axis=2)
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()
        assigned = {}

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if D[row, col] > self.max_distance:
                continue

            oid = object_ids[row]
            self.objects[oid] = input_centroids[col]
            self.disappeared[oid] = 0
            if oid not in self.history:
                self.history[oid] = []
            self.history[oid].append((int(input_centroids[col][0]), int(input_centroids[col][1])))
            if len(self.history[oid]) > 40:
                self.history[oid].pop(0)

            assigned[oid] = rects[col]
            used_rows.add(row)
            used_cols.add(col)

        unused_cols = set(range(len(rects))) - used_cols
        for col in unused_cols:
            oid = self._register(input_centroids[col])
            assigned[oid] = rects[col]

        unused_rows = set(range(len(object_ids))) - used_rows
        for row in unused_rows:
            oid = object_ids[row]
            self.disappeared[oid] += 1
            if self.disappeared[oid] > self.max_disappeared:
                self._deregister(oid)

        return assigned

    def _register(self, centroid: np.ndarray) -> int:
        oid = self.next_id
        self.objects[oid] = centroid
        self.disappeared[oid] = 0
        self.history[oid] = [(int(centroid[0]), int(centroid[1]))]
        self.next_id += 1
        return oid

    def _deregister(self, object_id: int):
        if object_id in self.objects:
            del self.objects[object_id]
        if object_id in self.disappeared:
            del self.disappeared[object_id]
        if object_id in self.history:
            del self.history[object_id]


class ObjectDetector:
    """
    YOLOv8 Object Detection & Tracking system
    Detects humans and bags with persistent ByteTrack tracking IDs.
    """
    def __init__(self):
        logger.info(f"Loading YOLO model: {settings.YOLO_MODEL_NAME}...")
        try:
            self.model = YOLO(settings.YOLO_MODEL_NAME)
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            self.model = None

        self.backup_tracker = CentroidTracker()
        self.target_class_ids = list(TARGET_CLASSES.keys())

    def detect_and_track(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        detections: List[Dict[str, Any]] = []
        if self.model is None or frame is None:
            return detections

        try:
            # Run YOLO track with ByteTrack
            results = self.model.track(
                source=frame,
                classes=self.target_class_ids,
                conf=settings.DETECTION_CONFIDENCE,
                persist=True,
                tracker=settings.TRACKER_TYPE,
                verbose=False
            )

            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        xyxy = box.xyxy[0].cpu().numpy().astype(int)
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        
                        track_id = int(box.id[0].item()) if box.id is not None else (i + 1)
                        class_name = TARGET_CLASSES.get(cls_id, "object")

                        x1, y1, x2, y2 = xyxy
                        w = x2 - x1
                        h = y2 - y1
                        cx = x1 + w // 2
                        cy = y1 + h // 2
                        aspect_ratio = float(h) / max(1.0, float(w))

                        detections.append({
                            "track_id": track_id,
                            "class_id": cls_id,
                            "class_name": class_name,
                            "confidence": round(conf, 3),
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "centroid": [cx, cy],
                            "w": w,
                            "h": h,
                            "aspect_ratio": round(aspect_ratio, 3)
                        })

        except Exception as e:
            # Fallback to standard detect + centroid tracking if tracker encountered issue
            try:
                raw_results = self.model(frame, classes=self.target_class_ids, conf=settings.DETECTION_CONFIDENCE, verbose=False)
                if raw_results and len(raw_results) > 0:
                    boxes = raw_results[0].boxes
                    rects = []
                    meta = []
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy().astype(int)
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        rects.append(tuple(xyxy))
                        meta.append((cls_id, conf))

                    assigned = self.backup_tracker.update(rects)
                    for oid, bbox in assigned.items():
                        x1, y1, x2, y2 = bbox
                        w = x2 - x1
                        h = y2 - y1
                        detections.append({
                            "track_id": oid,
                            "class_id": 0,
                            "class_name": "person",
                            "confidence": 0.85,
                            "bbox": [x1, y1, x2, y2],
                            "centroid": [x1 + w // 2, y1 + h // 2],
                            "w": w,
                            "h": h,
                            "aspect_ratio": round(float(h) / max(1.0, float(w)), 3)
                        })
            except Exception as inner_e:
                logger.error(f"Detector fallback error: {inner_e}")

        return detections
