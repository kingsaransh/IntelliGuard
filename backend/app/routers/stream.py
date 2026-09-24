import time
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.core.pipeline import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stream", tags=["stream"])

def generate_video_stream():
    """Generator for multipart MJPEG video stream"""
    while True:
        frame_bytes = pipeline.get_latest_jpeg()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS

@router.get("/video_feed")
def get_video_feed():
    """Serves real-time MJPEG live surveillance stream"""
    return StreamingResponse(
        generate_video_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.websocket("/ws")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for bi-directional live telemetry:
    Pushes real-time alerts, FPS, threat level, and detections directly to the browser
    """
    await websocket.accept()
    pipeline.alert_engine.register_websocket(websocket)
    try:
        while True:
            telemetry = pipeline.get_telemetry()
            await websocket.send_json(telemetry)
            await asyncio.sleep(0.2)  # 5 updates per second
    except WebSocketDisconnect:
        pipeline.alert_engine.unregister_websocket(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        pipeline.alert_engine.unregister_websocket(websocket)
