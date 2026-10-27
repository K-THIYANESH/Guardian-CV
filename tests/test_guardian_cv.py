"""
Guardian CV - Comprehensive Test Suite
=======================================
Validates:
1. OpenCV 5 runtime verification and substantive operations
2. Scenario A: Degraded quality handling & branch limitation
3. Scenario B: Significant visual change detection & follow-up spectral edge action
4. Scenario D: Nominal matching baseline with 0 false-positive candidate regions
5. Full API End-to-End integration test
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import unittest
import numpy as np
import cv2
import json
import base64
from guardian_swarm.core.vision_engine import GuardianVisionEngine
from guardian_swarm.agents.adaptive_inspector import AdaptiveInspectionAgent
from guardian_swarm.web.server import app

class TestGuardianCVSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = GuardianVisionEngine()
        cls.agent = AdaptiveInspectionAgent(vision_engine=cls.engine)
        cls.client = app.test_client()

    def test_01_opencv5_runtime_verified(self):
        info = self.engine.get_runtime_info()
        self.assertTrue(info["is_opencv_5"], f"OpenCV must be 5.x, got: {info['opencv_version']}")
        self.assertIn("5.0", info["opencv_version"])

    def test_02_scenario_a_quality_assessment(self):
        # Create an extremely blurry/flat image
        flat_img = np.full((300, 400, 3), 128, dtype=np.uint8)
        quality = self.engine.assess_quality(flat_img)
        self.assertTrue(quality["is_blurry"])
        self.assertFalse(quality["is_usable"])

        _, ref_buf = cv2.imencode(".jpg", flat_img)
        _, curr_buf = cv2.imencode(".jpg", flat_img)

        result = self.agent.run_investigation(ref_buf.tobytes(), curr_buf.tobytes())
        self.assertEqual(result["verdict"], "INSUFFICIENT_QUALITY")
        self.assertEqual(result["status"], "CONCLUDED_WITH_LIMITATION")

    def test_03_scenario_d_nominal_no_defect(self):
        # Create identical images with structural patterns
        img = np.zeros((300, 400, 3), dtype=np.uint8)
        cv2.rectangle(img, (50, 50), (180, 150), (200, 200, 200), -1)
        cv2.circle(img, (280, 150), 40, (150, 150, 150), -1)

        _, buf = cv2.imencode(".jpg", img)
        img_bytes = buf.tobytes()

        result = self.agent.run_investigation(img_bytes, img_bytes)
        self.assertEqual(result["verdict"], "NOMINAL_NO_CHANGE")
        self.assertEqual(result["total_regions"], 0)

    def test_04_scenario_b_confirmed_defect_with_adaptive_action(self):
        # Reference image
        ref = np.zeros((300, 400, 3), dtype=np.uint8)
        cv2.rectangle(ref, (50, 50), (180, 150), (200, 200, 200), -1)
        cv2.rectangle(ref, (220, 140), (350, 240), (150, 150, 150), -1)

        # Current image with a prominent scratch / anomaly
        curr = ref.copy()
        cv2.circle(curr, (285, 190), 20, (0, 0, 255), -1)
        cv2.line(curr, (270, 180), (300, 200), (255, 255, 255), 4)

        _, ref_buf = cv2.imencode(".jpg", ref)
        _, curr_buf = cv2.imencode(".jpg", curr)

        result = self.agent.run_investigation(ref_buf.tobytes(), curr_buf.tobytes())
        self.assertEqual(result["verdict"], "CONFIRMED_ANOMALY")
        self.assertGreater(result["total_regions"], 0)
        self.assertIn("verification_evidence", result)
        self.assertTrue(result["verification_evidence"]["is_structural_change"])
        
        # Verify trace has multi-step actions recorded
        steps = [s["step"] for s in result["trace"]]
        self.assertIn("STEP_1_QUALITY_ASSESSMENT", steps)
        self.assertIn("STEP_2_ORB_HOMOGRAPHY_REGISTRATION", steps)
        self.assertIn("STEP_3_MORPHOLOGICAL_CHANGE_DETECTION", steps)
        self.assertIn("STEP_4_SPECTRAL_EDGE_CONFIRMATION", steps)
        self.assertIn("STEP_5_VERIFICATION_AND_GOVERNANCE", steps)

    def test_05_api_cv_runtime_and_inspect_e2e(self):
        # Test /api/cv/runtime
        res = self.client.get('/api/cv/runtime')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["opencv"]["is_opencv_5"])

        # Test /api/cv/inspect with base64 benchmark
        img = np.full((200, 200, 3), 100, dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 80), (220, 220, 220), -1)
        curr = img.copy()
        cv2.circle(curr, (50, 50), 12, (255, 0, 0), -1)

        _, buf_r = cv2.imencode(".jpg", img)
        _, buf_c = cv2.imencode(".jpg", curr)
        b64_r = "data:image/jpeg;base64," + base64.b64encode(buf_r).decode("utf-8")
        b64_c = "data:image/jpeg;base64," + base64.b64encode(buf_c).decode("utf-8")

        res_post = self.client.post('/api/cv/inspect', json={
            "reference_b64": b64_r,
            "current_b64": b64_c,
            "objective": "visual_change_investigation"
        })
        self.assertEqual(res_post.status_code, 200)
        post_data = json.loads(res_post.data)
        self.assertIn("investigation_id", post_data)
        self.assertIn("trace", post_data)
        self.assertIn("cloud_vault", post_data)

if __name__ == '__main__':
    unittest.main()
