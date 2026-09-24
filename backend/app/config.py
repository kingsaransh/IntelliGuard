import os
from pathlib import Path
from pydantic import BaseModel

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INCIDENTS_DIR = DATA_DIR / "incidents"
FACES_DIR = DATA_DIR / "faces"
MEDIA_DIR = BASE_DIR / "sample_media"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
FACES_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    # System
    APP_NAME: str = "IntelliGuard AI Surveillance & Anomaly Detection"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_PATH: str = str(DATA_DIR / "intelliguard.db")

    # Storage Paths
    INCIDENTS_DIR: str = str(INCIDENTS_DIR)
    FACES_DIR: str = str(FACES_DIR)
    MEDIA_DIR: str = str(MEDIA_DIR)

    # Video & Stream Settings
    STREAM_WIDTH: int = 960
    STREAM_HEIGHT: int = 540
    STREAM_FPS: int = 25
    DEFAULT_SOURCE: str = "demo"  # 'demo', '0' (webcam), or path to video file

    # YOLO Detection Settings
    YOLO_MODEL_NAME: str = "yolov8n.pt"
    DETECTION_CONFIDENCE: float = 0.40
    TRACKER_TYPE: str = "bytetrack.yaml"

    # Threat Detection Thresholds
    FIGHT_CONFIDENCE_THRESHOLD: float = 0.65
    FALL_CONFIDENCE_THRESHOLD: float = 0.70
    FALL_ASPECT_RATIO_MAX: float = 0.85     # Height / Width < 0.85 indicates horizontal lying
    FALL_MIN_GROUND_FRAMES: int = 8         # Person must stay on ground for sustained period
    
    ABANDONED_OBJECT_DISTANCE_PX: float = 120.0  # Pixel separation threshold from owner
    ABANDONED_OBJECT_TIME_SEC: float = 8.0       # Seconds unattended to trigger alert (short for demo)

    FACE_RECOGNITION_TOLERANCE: float = 0.55     # Lower is stricter face match
    FACE_CHECK_INTERVAL_FRAMES: int = 6          # Run face embedding every N frames for CPU speed

    # Alert Cooldowns (seconds) to prevent notification spamming
    ALERT_COOLDOWN_SEC: float = 10.0

settings = Settings()
