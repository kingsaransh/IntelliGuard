import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
import torch

from app.core.detector import CentroidTracker
from app.core.fight_detector import FightCNNLSTMNet, FightViolenceDetector
from app.core.fall_detector import FallDetector
from app.core.abandoned_detector import AbandonedObjectDetector
from app.database import init_db, insert_incident, get_incidents

class TestIntelliGuardPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_crud(self):
        inc_id = insert_incident(
            camera_id="cam-test",
            threat_type="TEST_THREAT",
            severity="HIGH",
            confidence=0.95,
            track_id=10,
            description="Test incident event"
        )
        self.assertIsInstance(inc_id, int)
        self.assertGreater(inc_id, 0)

        incidents = get_incidents(limit=5, threat_type="TEST_THREAT")
        self.assertGreaterEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["threat_type"], "TEST_THREAT")

    def test_centroid_tracker(self):
        tracker = CentroidTracker(max_distance=100.0)
        # Frame 1: One box
        boxes1 = [(100, 100, 150, 220)]
        res1 = tracker.update(boxes1)
        self.assertEqual(len(res1), 1)
        oid = list(res1.keys())[0]

        # Frame 2: Box moves slightly
        boxes2 = [(105, 102, 155, 222)]
        res2 = tracker.update(boxes2)
        self.assertEqual(len(res2), 1)
        self.assertEqual(list(res2.keys())[0], oid)

    def test_fight_cnn_lstm_forward(self):
        model = FightCNNLSTMNet(sequence_length=8)
        # Batch: 1, Sequence: 8, Channels: 3, Height: 128, Width: 128
        dummy_input = torch.randn(1, 8, 3, 128, 128)
        with torch.no_grad():
            output = model(dummy_input)
        self.assertEqual(output.shape, (1, 2))
        # Probabilities sum to 1
        self.assertAlmostEqual(float(torch.sum(output).item()), 1.0, places=4)

    def test_fall_detector_logic(self):
        fall_det = FallDetector()
        frame = np.zeros((540, 960, 3), dtype=np.uint8)

        # Simulate person walking upright for 5 frames
        for _ in range(5):
            detections = [{
                "track_id": 1,
                "class_name": "person",
                "bbox": [100, 200, 150, 350],
                "centroid": [125, 275],
                "w": 50,
                "h": 150,
                "aspect_ratio": 3.0,
                "confidence": 0.9
            }]
            threats = fall_det.process(frame, detections)
            self.assertEqual(len(threats), 0)

        # Simulate person collapsing horizontally (aspect ratio flips to 0.27 and vertical drop)
        threats_found = False
        for i in range(12):
            detections = [{
                "track_id": 1,
                "class_name": "person",
                "bbox": [100, 350, 250, 390],
                "centroid": [175, 370],
                "w": 150,
                "h": 40,
                "aspect_ratio": 0.27,  # Very horizontal
                "confidence": 0.9
            }]
            threats = fall_det.process(frame, detections)
            if any(t["threat_type"] == "FALL_DETECTED" for t in threats):
                threats_found = True
                break

        self.assertTrue(threats_found, "Fall detector should trigger when person collapses horizontally")

    def test_abandoned_object_detector(self):
        bag_det = AbandonedObjectDetector()
        frame = np.zeros((540, 960, 3), dtype=np.uint8)

        # Bag detected at (400, 300), no person near it
        detections = [{
            "track_id": 5,
            "class_name": "backpack",
            "bbox": [380, 280, 420, 320],
            "centroid": [400, 300],
            "w": 40,
            "h": 40,
            "aspect_ratio": 1.0,
            "confidence": 0.88
        }]

        # Run for multiple cycles and verify it accumulates stationary unattended count
        for _ in range(6):
            threats = bag_det.process(frame, detections)
        
        self.assertIn(5, bag_det.tracked_objects)
        self.assertGreaterEqual(bag_det.tracked_objects[5]["stationary_count"], 5)

if __name__ == "__main__":
    unittest.main()
