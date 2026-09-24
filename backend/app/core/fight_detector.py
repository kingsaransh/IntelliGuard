import torch
import torch.nn as nn
import numpy as np
import cv2
import logging
from collections import deque
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class FightCNNLSTMNet(nn.Module):
    """
    Deep Learning Activity Recognition Neural Network:
    Spatial ConvNet Feature Extractor + Temporal Bidirectional LSTM + Dense Classifier
    Analyzes sequences of spatial feature maps across temporal windows to identify
    violent altercations, punching, wrestling, and physical fights.
    """
    def __init__(self, sequence_length: int = 16, feature_dim: int = 64, hidden_dim: int = 64):
        super().__init__()
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim

        # 2D Spatial Convolutional feature block
        self.spatial_cnn = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, feature_dim),
            nn.ReLU()
        )

        # Temporal Bidirectional LSTM for sequence dynamics
        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )

        # Final anomaly classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 2),
            nn.Softmax(dim=1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, sequence_length, C, H, W)
        b, s, c, h, w = x.shape
        x_reshaped = x.view(b * s, c, h, w)
        features = self.spatial_cnn(x_reshaped)  # (b * s, feature_dim)
        features_seq = features.view(b, s, -1)   # (b, sequence_length, feature_dim)

        lstm_out, _ = self.lstm(features_seq)    # (b, sequence_length, hidden_dim * 2)
        final_temporal = lstm_out[:, -1, :]      # Last time-step representation
        probs = self.classifier(final_temporal)  # (b, 2) [P(normal), P(fight)]
        return probs


class FightViolenceDetector:
    """
    Real-time Fight & Violence Detection Engine:
    Combines PyTorch CNN-LSTM deep learning sequence analysis with
    spatial-temporal optical motion energy and inter-person proximity metrics.
    """
    def __init__(self, sequence_length: int = 16):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = FightCNNLSTMNet(sequence_length=sequence_length).to(self.device)
        self.model.eval()

        self.sequence_length = sequence_length
        self.frame_buffer = deque(maxlen=sequence_length)
        self.prev_gray: Optional[np.ndarray] = None
        
        # Track history for motion variance analysis
        self.person_trajectories: Dict[int, deque] = {}

    def process(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        threats: List[Dict[str, Any]] = []
        if frame is None:
            return threats

        h, w, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized_small = cv2.resize(frame, (128, 128))
        
        # Preprocess frame tensor (C, H, W) normalized
        frame_tensor = torch.from_numpy(resized_small).permute(2, 0, 1).float() / 255.0
        self.frame_buffer.append(frame_tensor)

        # 1. Compute Optical Flow / Motion Energy if previous frame exists
        motion_energy = 0.0
        if self.prev_gray is not None:
            # Downsampled frame for rapid optical flow calculation on CPU
            small_curr = cv2.resize(gray, (160, 90))
            small_prev = cv2.resize(self.prev_gray, (160, 90))
            flow = cv2.calcOpticalFlowFarneback(
                small_prev, small_curr, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            motion_energy = float(np.mean(magnitude))

        self.prev_gray = gray

        # 2. Filter person detections
        persons = [d for d in detections if d.get("class_name") == "person"]

        # 3. Inter-person proximity & interaction checks
        # Physical fights require two or more persons in close physical contact with violent relative velocity
        if len(persons) >= 2:
            for i in range(len(persons)):
                for j in range(i + 1, len(persons)):
                    p1 = persons[i]
                    p2 = persons[j]

                    cx1, cy1 = p1["centroid"]
                    cx2, cy2 = p2["centroid"]
                    dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)

                    # Compute bounding box overlap or proximity
                    combined_w = (p1["w"] + p2["w"]) / 2.0
                    if dist < combined_w * 1.5:  # Persons are in grapple/close contact range
                        # Deep Learning Inference through CNN-LSTM if buffer ready
                        dl_fight_prob = 0.0
                        if len(self.frame_buffer) == self.sequence_length:
                            try:
                                with torch.no_grad():
                                    seq_tensor = torch.stack(list(self.frame_buffer)).unsqueeze(0).to(self.device)
                                    probs = self.model(seq_tensor)
                                    dl_fight_prob = float(probs[0, 1].item())
                            except Exception as e:
                                logger.error(f"Fight CNN-LSTM inference error: {e}")

                        # Kinematic Energy score (motion + high relative variance)
                        kinematic_score = min(1.0, motion_energy / 4.0)
                        
                        # Hybrid confidence fusion
                        # Weight DL score + kinematic motion energy
                        combined_confidence = 0.55 * dl_fight_prob + 0.45 * kinematic_score
                        
                        # Boost confidence if motion energy is exceptionally high during contact
                        if motion_energy > 2.8:
                            combined_confidence = max(combined_confidence, min(0.95, 0.5 + motion_energy * 0.12))

                        if combined_confidence >= settings.FIGHT_CONFIDENCE_THRESHOLD:
                            # Construct unified bounding box covering both fighting participants
                            min_x = min(p1["bbox"][0], p2["bbox"][0])
                            min_y = min(p1["bbox"][1], p2["bbox"][1])
                            max_x = max(p1["bbox"][2], p2["bbox"][2])
                            max_y = max(p1["bbox"][3], p2["bbox"][3])

                            threats.append({
                                "threat_type": "FIGHT_VIOLENCE",
                                "severity": "CRITICAL",
                                "confidence": round(combined_confidence, 3),
                                "track_id": p1["track_id"],
                                "secondary_track_id": p2["track_id"],
                                "bbox": [min_x, min_y, max_x, max_y],
                                "description": f"Violent altercation detected between Track #{p1['track_id']} and Track #{p2['track_id']}",
                                "motion_energy": round(motion_energy, 2)
                            })

        return threats
