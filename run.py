import os
import sys
import time
import webbrowser
import logging
import subprocess
from pathlib import Path

# Set working directory to project root
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IntelliGuardRunner")

def print_banner():
    banner = r"""
==========================================================================
    ___       __       ____ _ ____                     __
   / (_)___  / /____  / / /(_) __ \__  ______ ________/ /
  / / / __ \/ __/ _ \/ / / / / / / / / / / __ `/ ___/ __  / 
 / / / / / / /_/  __/ / / / / /_/ / /_/ / /_/ / /  / /_/ /  
/_/_/_/ /_/\__/\___/_/_/_/_/\___\_\__,_/\__,_/_/   \__,_/   
                                                            
      REAL-TIME AI SAFETY & ANOMALY DETECTION SYSTEM v2.0
==========================================================================
 [*] YOLOv8 Multi-Object Detection & ByteTrack Persistent Tracking
 [*] PyTorch CNN-LSTM Deep Learning Fight & Violence Detection
 [*] Kinematic & Ground-Persistence Accidental Fall Detection
 [*] Stationary Elapsed Timer Abandoned Luggage Tracker
 [*] 128-d Embedding Facial Recognition & Clearance Whitelist
 [*] High-Tech SOC Cyber Dashboard & Real-Time Audio Alarms
==========================================================================
"""
    print(banner)

def verify_frontend_build():
    """Builds frontend if dist/ doesn't exist yet"""
    if not (FRONTEND_DIST / "index.html").exists():
        logger.info("Building frontend static assets...")
        frontend_dir = ROOT_DIR / "frontend"
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
            logger.info("Frontend build complete.")
        except Exception as e:
            logger.warning(f"Could not build frontend: {e}. FastAPI will run API-only mode.")

def main():
    print_banner()

    # Add backend to sys.path
    sys.path.insert(0, str(BACKEND_DIR))

    # Verify frontend assets
    verify_frontend_build()

    port = 8000
    url = f"http://localhost:{port}"

    logger.info(f"Starting IntelliGuard server on {url}...")

    # Open browser after short delay
    def open_browser():
        time.sleep(2.0)
        logger.info(f"Opening IntelliGuard Dashboard in default browser: {url}")
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch Uvicorn server
    try:
        import uvicorn
        uvicorn.run("app.main:app", app_dir=str(BACKEND_DIR), host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("IntelliGuard stopped by user.")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")

if __name__ == "__main__":
    main()
