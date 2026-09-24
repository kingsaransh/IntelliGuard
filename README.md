# 🛡️ IntelliGuard – Real-Time AI Safety & Anomaly Detection System

**IntelliGuard** is an enterprise-grade AI surveillance and anomaly detection platform designed for real-time video stream analysis. It identifies abnormal and hazardous events (**violent fights, accidental falls, unattended/abandoned luggage, and unauthorized intruder faces**) while providing a live Security Operations Center (SOC) dashboard, persistent SQLite incident evidence vault, and automated alert dispatch.

---

## 🚀 Key Features

| Feature | Technology / Model | Description |
|---|---|---|
| 🎥 **Real-time Video Pipeline** | OpenCV (Multi-threaded) | Decoupled capture and inference pipeline supporting Webcams, RTSP streams, uploaded video files, and built-in procedural synthetic threat simulator. |
| 👤 **Person Detection & Tracking** | YOLOv8n + ByteTrack | Ultra-fast human detection with persistent track IDs, spatial velocity vectors, and normalized aspect ratios. |
| 🥊 **Fight / Violence Detection** | PyTorch CNN-LSTM + Optical Flow | Spatial ConvNet + Temporal Bidirectional LSTM analyzing sequence dynamics and rapid kinetic energy between individuals. |
| 🚨 **Fall / Emergency Detection** | Kinematic & Geometric Inversion | Detects rapid downward centroid plunge ($dy/dt$), aspect ratio flip ($H/W < 0.85$), and ground persistence timer to identify collapsed individuals. |
| 🧍 **Abandoned Luggage Detection** | Proximity & Stationary Timer | Tracks backpacks, handbags, and suitcases. Measures distance to nearest person and triggers alarm if left unattended for $> 8$ seconds. |
| 🔐 **Facial Access Control** | 128-d Deep Face Embeddings | Recognizes authorized personnel (Security Officers, Staff) and highlights unrecognized intruders in red. Includes live face enrollment via dashboard. |
| 📊 **Security Operations Dashboard** | React + Vite + Vanilla CSS | Futuristic dark cyber SOC interface with live video feed, scanlines, HUD, radar alert feed, real-time FPS meter, and anomaly breakdown charts. |
| 🔔 **Audio Alarms & Notifications** | Web Audio API + WebSockets | Synthesized high-tech alarm chimes and push alerts streamed via WebSockets with anti-spam cooldown de-duplication. |
| 🗃️ **Incident Evidence Vault** | SQLite + Annotated Screenshots | Automatically captures full-resolution evidence snapshots with bounding boxes, confidence scores, and timestamps. Supports CSV report export. |

---

## 🏛️ Deep Learning Architecture

```
                       ┌────────────────────────────────────────────────────────┐
                       │                   VIDEO INPUT STREAM                   │
                       │    (Webcam / Video File / Synthetic Threat Demo)       │
                       └───────────────────────────┬────────────────────────────┘
                                                   │
                                                   ▼
                       ┌────────────────────────────────────────────────────────┐
                       │          OpenCV Video Ingestion & Processing           │
                       │        - Frame Queue (Multi-threaded producer)         │
                       │        - Motion Differencing & Optical Flow            │
                       └───────────────────────────┬────────────────────────────┘
                                                   │
                                                   ▼
                       ┌────────────────────────────────────────────────────────┐
                       │        YOLOv8 Object Detection & ByteTrack Tracker     │
                       │        - Person Detection (Class 0)                    │
                       │        - Bag/Luggage Detection (Classes 24, 26, 28)    │
                       │        - Track ID assignment & trajectory history      │
                       └───────────────────────────┬────────────────────────────┘
                                                   │
     ┌──────────────────────┬──────────────────────┼──────────────────────┬──────────────────────┐
     │                      │                      │                      │                      │
     ▼                      ▼                      ▼                      ▼                      ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ CNN + LSTM   │     │ Fall         │     │ Abandoned    │     │ Face         │     │ Crowd / Density  │
│ Fight &      │     │ Detection    │     │ Object       │     │ Recognition  │     │ Anomaly          │
│ Violence Net │     │ (Velocity +  │     │ (Stationary  │     │ (128-d       │     │ Detection        │
│ (PyTorch)    │     │ Aspect Ratio)│     │ Time Track)  │     │ Embeddings)  │     │ (Loitering/Surge)│
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └────────┬─────────┘
       │                    │                    │                    │                      │
       └────────────────────┼────────────────────┼────────────────────┴──────────────────────┘
                            │
                            ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │                     IntelliGuard Alert & Incident Engine                │
     │      - Severity Classification (INFO, LOW, MEDIUM, HIGH, CRITICAL)     │
     │      - Cooldown & De-duplication                                       │
     │      - Auto-capture annotated evidence screenshot                      │
     │      - SQLite Incident Store (timestamps, track IDs, confidence)       │
     │      - Multi-channel notification dispatcher (WebSockets, Telegram)    │
     └──────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │            FastAPI Backend + React Cyber SOC Dashboard                 │
     │      - Low-latency MJPEG Live Stream with Dynamic Overlay Canvas       │
     │      - Real-time WebSocket Alert Feed with Audio Chime Alarms          │
     │      - Incident Evidence Gallery & Export                              │
     │      - Face Whitelist / Blacklist Enrollment Interface                 │
     │      - Multi-Camera Configuration & Mode Switcher                      │
     └────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start: How to Run

### Method 1: Turnkey One-Click Launcher (Recommended)
Simply run the root launcher:
```bash
python run.py
```
*Or double click `run.bat` on Windows.*

This will:
1. Initialize the SQLite database and evidence directories.
2. Launch the FastAPI server with YOLOv8, CNN-LSTM, Fall, Bag, and Face modules on `http://localhost:8000`.
3. Automatically open the **IntelliGuard SOC Dashboard** in your default browser.

---

### Method 2: Development Mode (with Vite HMR)
If you wish to run the backend and frontend with live hot-reloading:

**Terminal 1 (Backend):**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🎮 Input Modes

1. **Synthetic Threat Simulator (Instant Demo)**:
   - Built-in procedural security simulation demonstrating all 4 anomaly types in a smooth 36-second cycle (normal walking $\to$ accidental slip/fall $\to$ abandoned luggage $\to$ violent physical fight).
   - Works immediately out of the box without requiring external video files or cameras.
2. **Live Webcam**:
   - Switches feed to your local laptop or USB webcam (`cam-2` / index 0).
3. **Upload Surveillance Video**:
   - Drag & drop any `.mp4` or `.avi` video through the dashboard ("CAM FEED" $\to$ "CHOOSE VIDEO") to run real-time inference on custom CCTV footage.

---

## 🛡️ API Endpoints

- `GET /api/stream/video_feed`: Real-time multipart MJPEG surveillance stream.
- `WS /api/stream/ws`: Bi-directional WebSocket telemetry stream (FPS, threat level, live detections).
- `GET /api/incidents`: Filtered incident logs (query by threat type, severity, limit).
- `PUT /api/incidents/{id}/status`: Acknowledge or resolve an incident.
- `GET /api/incidents/screenshot/{filename}`: Retrieve full-resolution annotated incident screenshot.
- `GET /api/incidents/export`: Download all incidents as a CSV report.
- `GET /api/faces`: List authorized personnel.
- `POST /api/faces/enroll_base64`: Enroll a new authorized person via camera snapshot or photo upload.
- `DELETE /api/faces/{id}`: Revoke access authorization.
- `GET /api/cameras`: List all configured surveillance feeds.
- `POST /api/cameras/switch`: Switch active feed source (webcam, demo, video file).
- `POST /api/cameras/upload_video`: Upload video file for inference.
- `GET /api/system/status`: Real-time system health and FPS diagnostics.
- `POST /api/system/toggle_module`: Toggle specific detectors on/off.
- `POST /api/system/test_alert`: Trigger simulated test alarm.

---

## 🧪 Automated Testing

Run the comprehensive unit test suite:
```bash
cd backend
python tests/test_pipeline.py
```
Verifies database CRUD, YOLO fallback tracking, CNN-LSTM forward pass, fall aspect ratio kinematics, and abandoned luggage stationary counter.
