import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Incidents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        camera_id TEXT NOT NULL,
        threat_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        confidence REAL NOT NULL,
        track_id INTEGER,
        description TEXT,
        screenshot_path TEXT,
        status TEXT DEFAULT 'NEW',
        metadata_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Authorized Faces Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authorized_faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT,
        photo_path TEXT,
        embedding_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Cameras Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cameras (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_url TEXT NOT NULL,
        location TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Populate default camera if empty
    cursor.execute("SELECT COUNT(*) FROM cameras")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO cameras (id, name, source_type, source_url, location, active)
        VALUES 
        ('cam-1', 'Sector Alpha - Main Entrance', 'demo', 'demo', 'Building A North Gate', 1),
        ('cam-2', 'Sector Beta - Corridor & Lobby', 'webcam', '0', 'Lobby Security Desk', 0),
        ('cam-3', 'Sector Gamma - Perimeter West', 'demo', 'demo', 'Perimeter Fence B', 0)
        """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

# Incident CRUD helpers
def insert_incident(
    camera_id: str,
    threat_type: str,
    severity: str,
    confidence: float,
    track_id: Optional[int],
    description: str,
    screenshot_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_str = json.dumps(metadata or {})

    cursor.execute("""
    INSERT INTO incidents (timestamp, camera_id, threat_type, severity, confidence, track_id, description, screenshot_path, status, metadata_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?)
    """, (now_str, camera_id, threat_type, severity, confidence, track_id, description, screenshot_path, meta_str))
    
    incident_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return incident_id

def get_incidents(limit: int = 50, threat_type: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM incidents WHERE 1=1"
    params = []

    if threat_type and threat_type != "ALL":
        query += " AND threat_type = ?"
        params.append(threat_type)
    if severity and severity != "ALL":
        query += " AND severity = ?"
        params.append(severity)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

def update_incident_status(incident_id: int, status: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE incidents SET status = ? WHERE id = ?", (status, incident_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Face Enrollment CRUD helpers
def insert_authorized_face(name: str, role: str, department: str, photo_path: str, embedding: List[float]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO authorized_faces (name, role, department, photo_path, embedding_json)
    VALUES (?, ?, ?, ?, ?)
    """, (name, role, department, photo_path, json.dumps(embedding)))
    face_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return face_id

def get_all_authorized_faces() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role, department, photo_path, embedding_json, created_at FROM authorized_faces ORDER BY id DESC")
    rows = cursor.fetchall()
    faces = []
    for r in rows:
        d = dict(r)
        try:
            d["embedding"] = json.loads(d["embedding_json"])
        except Exception:
            d["embedding"] = []
        del d["embedding_json"]
        faces.append(d)
    conn.close()
    return faces

def delete_authorized_face(face_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM authorized_faces WHERE id = ?", (face_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Camera CRUD helpers
def get_cameras_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cameras ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_active_camera(camera_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE cameras SET active = 0")
    cursor.execute("UPDATE cameras SET active = 1 WHERE id = ?", (camera_id,))
    conn.commit()
    conn.close()
    return True
