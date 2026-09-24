import cv2
import time
import math
import random
import logging
import threading
import numpy as np
from typing import Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

class SyntheticThreatSimulator:
    """
    Generates dynamic, procedural CCTV security footage with simulated scenarios:
    - Normal walking pedestrians
    - Sudden fall accident (person collapses, stays down)
    - Physical altercation / fight struggle (violent high-motion rapid interaction)
    - Abandoned baggage / unattended suitcase (person leaves luggage and walks away)
    - Facial access checkpoint
    """
    def __init__(self, width: int = 960, height: int = 540):
        self.width = width
        self.height = height
        self.frame_count = 0
        self.cycle_length = 900  # ~36 seconds at 25 fps cycle
        
        # State variables for actors
        self.actors = [
            {"id": 1, "x": 100, "y": 280, "vx": 2.2, "vy": 0.0, "w": 44, "h": 120, "color": (50, 180, 70), "label": "Officer Alex", "role": "Security", "is_face": True},
            {"id": 2, "x": 800, "y": 290, "vx": -2.0, "vy": 0.0, "w": 46, "h": 125, "color": (210, 130, 40), "label": "Civilian", "role": "Visitor", "is_face": True},
        ]
        
        # Bag state
        self.bag = {"active": False, "x": 480, "y": 380, "w": 36, "h": 32, "owner_id": 2}

    def render_background(self, img: np.ndarray):
        # Security facility lobby / corridor background
        # Ceiling & walls
        img[0:180, :] = (24, 28, 38)
        # Wall panelling
        img[180:260, :] = (38, 44, 58)
        # Floor with perspective tiles
        img[260:, :] = (50, 54, 68)

        # Draw perspective floor grid lines
        for x in range(0, self.width, 100):
            cv2.line(img, (x, 260), (int(x * 1.5 - 200), self.height), (60, 66, 82), 1)
        for y in range(260, self.height, 50):
            cv2.line(img, (0, y), (self.width, y), (60, 66, 82), 1)

        # Entrance door / turnstiles
        cv2.rectangle(img, (self.width // 2 - 120, 100), (self.width // 2 + 120, 260), (30, 35, 48), -1)
        cv2.rectangle(img, (self.width // 2 - 120, 100), (self.width // 2 + 120, 260), (80, 90, 110), 2)
        cv2.putText(img, "SECURE SECTOR 04", (self.width // 2 - 95, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (140, 160, 180), 1)

        # Camera watermark & timestamp
        now = time.strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(img, f"CAM-01 [LIVE] :: {now}", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)
        cv2.putText(img, "INTELLIGUARD REAL-TIME DL SURVEILLANCE", (25, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 180, 200), 1)

    def generate_frame(self) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.render_background(frame)
        self.frame_count += 1
        phase = self.frame_count % self.cycle_length

        # -------------------------------------------------------------
        # Scenario Timeline in the 36-second cycle:
        # 0 - 200: Normal Patrol (Officer Alex & Visitor walking)
        # 200 - 450: Sudden Fall Accident (Visitor slips, collapses, stays down)
        # 450 - 650: Unattended Luggage Incident (Bag left stationary)
        # 650 - 900: Violent Physical Altercation (Intense grapple & rapid struggle)
        # -------------------------------------------------------------

        if phase < 200:
            # Normal walking
            scenario_name = "NORMAL SURVEILLANCE"
            scenario_color = (0, 255, 100)
            self._simulate_walking(frame)

        elif phase < 450:
            # Fall Accident scenario
            scenario_name = "SIMULATED INCIDENT: ACCIDENTAL FALL"
            scenario_color = (0, 180, 255)
            self._simulate_fall(frame, phase - 200)

        elif phase < 650:
            # Abandoned object scenario
            scenario_name = "SIMULATED INCIDENT: ABANDONED LUGGAGE"
            scenario_color = (0, 200, 255)
            self._simulate_abandoned_bag(frame, phase - 450)

        else:
            # Fight / Violence altercation scenario
            scenario_name = "SIMULATED INCIDENT: PHYSICAL ALTERCATION / FIGHT"
            scenario_color = (0, 0, 255)
            self._simulate_fight(frame, phase - 650)

        # Draw HUD banner
        cv2.rectangle(frame, (self.width - 450, 15), (self.width - 20, 48), (20, 24, 32), -1)
        cv2.rectangle(frame, (self.width - 450, 15), (self.width - 20, 48), scenario_color, 1)
        cv2.putText(frame, scenario_name, (self.width - 435, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.48, scenario_color, 1)

        return frame

    def _draw_person(self, frame: np.ndarray, x: int, y: int, w: int, h: int, color: Tuple[int, int, int], is_horizontal: bool = False):
        if not is_horizontal:
            # Normal upright person
            # Head
            head_r = int(w * 0.28)
            head_center = (x + w // 2, y + head_r + 4)
            cv2.circle(frame, head_center, head_r, (210, 190, 175), -1)
            cv2.circle(frame, head_center, head_r, (40, 40, 40), 1)

            # Torso
            torso_top = y + head_r * 2 + 4
            torso_h = int(h * 0.45)
            cv2.rectangle(frame, (x + 6, torso_top), (x + w - 6, torso_top + torso_h), color, -1)

            # Limbs / Legs
            leg_w = max(5, (w - 18) // 2)
            cv2.rectangle(frame, (x + 8, torso_top + torso_h), (x + 8 + leg_w, y + h), (40, 40, 50), -1)
            cv2.rectangle(frame, (x + w - 8 - leg_w, torso_top + torso_h), (x + w - 8, y + h), (40, 40, 50), -1)
        else:
            # Person collapsed horizontally on the floor
            # Head on ground
            cv2.circle(frame, (x + 18, y + h // 2), int(h * 0.35), (210, 190, 175), -1)
            # Torso lying flat
            cv2.rectangle(frame, (x + 28, y + 4), (x + int(w * 0.7), y + h - 4), color, -1)
            # Legs extended
            cv2.rectangle(frame, (x + int(w * 0.7), y + 6), (x + w - 4, y + h // 2), (40, 40, 50), -1)

    def _simulate_walking(self, frame):
        for a in self.actors:
            a["x"] += a["vx"]
            if a["x"] > self.width - 120:
                a["vx"] = -abs(a["vx"])
            elif a["x"] < 100:
                a["vx"] = abs(a["vx"])
            self._draw_person(frame, int(a["x"]), int(a["y"]), a["w"], a["h"], a["color"])

    def _simulate_fall(self, frame, subphase):
        # Actor 1 patrols on left
        a1 = self.actors[0]
        a1["x"] = 220 + 30 * math.sin(self.frame_count * 0.05)
        self._draw_person(frame, int(a1["x"]), int(a1["y"]), a1["w"], a1["h"], a1["color"])

        # Actor 2 walks, suddenly stumbles at subphase 30, collapses by subphase 50, stays down
        fall_x = 550
        if subphase < 30:
            # Walking before fall
            x = 480 + subphase * 2.3
            self._draw_person(frame, int(x), 290, 46, 125, (210, 130, 40), is_horizontal=False)
        elif subphase < 55:
            # Descending / Falling rapidly down
            prog = (subphase - 30) / 25.0
            cur_y = int(290 + prog * 60)
            cur_w = int(46 + prog * 70)  # expands horizontally
            cur_h = int(125 - prog * 75) # shrinks vertically
            self._draw_person(frame, fall_x, cur_y, cur_w, cur_h, (210, 130, 40), is_horizontal=(prog > 0.6))
        else:
            # Collapsed horizontal on ground
            self._draw_person(frame, fall_x, 350, 120, 42, (210, 130, 40), is_horizontal=True)

    def _simulate_abandoned_bag(self, frame, subphase):
        # Person 1 walks away to the far right
        # Bag stays stationary at x=450, y=360
        bag_x, bag_y = 450, 360
        # Draw backpack / duffel bag
        cv2.rectangle(frame, (bag_x, bag_y), (bag_x + 40, bag_y + 32), (180, 60, 40), -1)
        cv2.rectangle(frame, (bag_x, bag_y), (bag_x + 40, bag_y + 32), (240, 100, 80), 2)
        # Bag handle & straps
        cv2.ellipse(frame, (bag_x + 20, bag_y), (10, 8), 0, 180, 360, (250, 200, 100), 2)

        # Person walking away into the distance
        person_x = int(520 + subphase * 2.5)
        if person_x < self.width + 50:
            self._draw_person(frame, person_x, 280, 44, 120, (60, 140, 200))

    def _simulate_fight(self, frame, subphase):
        # Two actors close together with erratic violent motion
        center_x = 480
        jitter1 = int(18 * math.sin(self.frame_count * 0.8) + random.randint(-4, 4))
        jitter2 = int(18 * math.cos(self.frame_count * 0.7) + random.randint(-4, 4))
        
        x1 = center_x - 30 + jitter1
        x2 = center_x + 10 + jitter2

        # Draw fighting actors
        self._draw_person(frame, x1, 285 + random.randint(-3, 3), 48, 122, (200, 50, 50))
        self._draw_person(frame, x2, 288 + random.randint(-3, 3), 48, 120, (50, 80, 210))

        # Dynamic motion impact flashes during fight
        if subphase % 10 < 3:
            impact_x = center_x + random.randint(-15, 15)
            impact_y = 310 + random.randint(-10, 10)
            cv2.circle(frame, (impact_x, impact_y), random.randint(14, 26), (255, 255, 200), -1)


class VideoStreamManager:
    """
    Threaded video ingestion manager. Supports:
    - Webcam index (0, 1, ...)
    - Video files (.mp4, .avi, etc.)
    - Procedural synthetic simulator ('demo')
    """
    def __init__(self, source: str = "demo"):
        self.source = source
        self.cap: Optional[cv2.VideoCapture] = None
        self.simulator = SyntheticThreatSimulator(settings.STREAM_WIDTH, settings.STREAM_HEIGHT)
        self.current_frame: Optional[np.ndarray] = None
        self.is_running = False
        self.lock = threading.Lock()
        self.fps = 0.0
        self.last_frame_time = time.time()
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._initialize_capture()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Video stream started with source: {self.source}")

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Video stream stopped.")

    def change_source(self, new_source: str):
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.source = new_source
            self._initialize_capture()
        logger.info(f"Video source switched to: {new_source}")

    def _initialize_capture(self):
        if self.source == "demo":
            self.cap = None
            return

        # Check if source is webcam integer index
        if self.source.isdigit():
            cam_idx = int(self.source)
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else cv2.CAP_ANY)
        else:
            self.cap = cv2.VideoCapture(self.source)

        if self.cap and not self.cap.isOpened():
            logger.warning(f"Could not open source '{self.source}', falling back to Synthetic Demo simulator.")
            self.source = "demo"
            self.cap = None
        elif self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.STREAM_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.STREAM_HEIGHT)

    def _capture_loop(self):
        frame_interval = 1.0 / settings.STREAM_FPS
        while self.is_running:
            start_t = time.time()
            frame = None

            if self.source == "demo" or self.cap is None:
                frame = self.simulator.generate_frame()
            else:
                ret, captured = self.cap.read()
                if not ret or captured is None:
                    # If video file ended, loop back
                    if not self.source.isdigit():
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, captured = self.cap.read()
                    if not ret or captured is None:
                        # Fallback to demo if webcam fails
                        frame = self.simulator.generate_frame()
                    else:
                        frame = cv2.resize(captured, (settings.STREAM_WIDTH, settings.STREAM_HEIGHT))
                else:
                    frame = cv2.resize(captured, (settings.STREAM_WIDTH, settings.STREAM_HEIGHT))

            if frame is not None:
                now = time.time()
                dt = now - self.last_frame_time
                if dt > 0:
                    self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
                self.last_frame_time = now

                with self.lock:
                    self.current_frame = frame.copy()

            # Maintain smooth playback rate
            elapsed = time.time() - start_t
            sleep_time = max(0.001, frame_interval - elapsed)
            time.sleep(sleep_time)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
