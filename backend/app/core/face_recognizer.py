import cv2
import time
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import face_recognition

from app.config import settings
from app.database import get_all_authorized_faces, insert_authorized_face

logger = logging.getLogger(__name__)

class FaceRecognizerEngine:
    """
    Facial Recognition & Access Control Engine:
    - Detects faces in surveillance frames
    - Computes 128-dimensional deep face embeddings
    - Compares against authorized database
    - Flags unauthorized / unrecognized intruders
    """
    def __init__(self):
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        self.known_face_roles: List[str] = []
        self.frame_counter = 0
        self.cached_faces: List[Dict[str, Any]] = []

        self.load_known_faces()

    def load_known_faces(self):
        """Loads all authorized face embeddings from SQLite database"""
        self.known_face_encodings.clear()
        self.known_face_names.clear()
        self.known_face_roles.clear()

        faces_db = get_all_authorized_faces()
        if len(faces_db) == 0:
            # Seed default demo security personnel so face recognition is functional immediately
            self._seed_demo_faces()
            faces_db = get_all_authorized_faces()

        for f in faces_db:
            if f.get("embedding") and len(f["embedding"]) == 128:
                self.known_face_encodings.append(np.array(f["embedding"], dtype=float))
                self.known_face_names.append(f["name"])
                self.known_face_roles.append(f.get("role", "Authorized"))

        logger.info(f"Loaded {len(self.known_face_encodings)} authorized faces.")

    def _seed_demo_faces(self):
        """Creates initial demo authorized faces with synthetic or sample embeddings"""
        logger.info("Seeding demo authorized personnel...")
        # Create dummy 128-d unit vectors for demonstration
        rng = np.random.RandomState(42)
        demo_vec1 = rng.randn(128)
        demo_vec1 = demo_vec1 / np.linalg.norm(demo_vec1)

        demo_vec2 = rng.randn(128)
        demo_vec2 = demo_vec2 / np.linalg.norm(demo_vec2)

        insert_authorized_face(
            name="Officer Alex",
            role="Chief of Security",
            department="Surveillance Division",
            photo_path="",
            embedding=demo_vec1.tolist()
        )
        insert_authorized_face(
            name="Dr. Elena Vance",
            role="Authorized Staff",
            department="AI Operations",
            photo_path="",
            embedding=demo_vec2.tolist()
        )

    def enroll_from_frame(self, name: str, role: str, department: str, frame: np.ndarray) -> Tuple[bool, str]:
        """Enrolls a new face from a captured BGR video frame or image"""
        if frame is None:
            return False, "Invalid image data"

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        if len(face_locations) == 0:
            return False, "No face detected in the provided image. Please face the camera directly."

        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if len(encodings) == 0:
            return False, "Could not extract face embedding."

        encoding = encodings[0].tolist()

        # Save photo to disk
        top, right, bottom, left = face_locations[0]
        face_crop = frame[max(0, top-20):min(frame.shape[0], bottom+20), max(0, left-20):min(frame.shape[1], right+20)]
        photo_filename = f"face_{int(time.time())}_{name.replace(' ', '_')}.jpg"
        photo_path = Path(settings.FACES_DIR) / photo_filename
        cv2.imwrite(str(photo_path), face_crop)

        # Insert to DB and reload
        insert_authorized_face(name, role, department, str(photo_path), encoding)
        self.load_known_faces()
        return True, f"Successfully enrolled {name} ({role})"

    def process(self, frame: np.ndarray) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs face recognition every N frames for CPU performance optimization.
        Returns:
            face_results: detected faces with name, role, status (AUTHORIZED / UNAUTHORIZED)
            threats: alert items for unrecognized intruders
        """
        self.frame_counter += 1
        threats: List[Dict[str, Any]] = []

        # Run face recognition on interval to keep 30 FPS
        if self.frame_counter % settings.FACE_CHECK_INTERVAL_FRAMES != 0 and len(self.cached_faces) > 0:
            return self.cached_faces, threats

        if frame is None:
            return [], []

        h, w, _ = frame.shape
        # Downsample frame for fast face detection
        scale = 0.5
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect face bounding boxes
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        current_faces = []

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale coordinates back up to original frame dimensions
            top = int(top / scale)
            right = int(right / scale)
            bottom = int(bottom / scale)
            left = int(left / scale)

            name = "UNKNOWN INTRUDER"
            role = "Unauthorized"
            is_authorized = False
            best_distance = 1.0

            if len(self.known_face_encodings) > 0:
                distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = int(np.argmin(distances))
                best_distance = float(distances[best_match_index])

                if best_distance <= settings.FACE_RECOGNITION_TOLERANCE:
                    name = self.known_face_names[best_match_index]
                    role = self.known_face_roles[best_match_index]
                    is_authorized = True

            face_info = {
                "bbox": [left, top, right, bottom],
                "name": name,
                "role": role,
                "is_authorized": is_authorized,
                "confidence": round(1.0 - best_distance, 3)
            }
            current_faces.append(face_info)

            # Generate security alert for unauthorized person in secure area
            if not is_authorized:
                threats.append({
                    "threat_type": "UNAUTHORIZED_PERSON",
                    "severity": "MEDIUM",
                    "confidence": round(0.75 + (1.0 - min(1.0, best_distance)) * 0.2, 3),
                    "track_id": None,
                    "bbox": [left, top, right, bottom],
                    "description": f"Unrecognized individual detected without clearance at surveillance checkpoint",
                    "name": name
                })

        self.cached_faces = current_faces
        return current_faces, threats
