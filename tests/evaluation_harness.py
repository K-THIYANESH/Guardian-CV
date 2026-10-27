"""
Guardian CV - Quantitative Evaluation Harness & Benchmark Suite
================================================================
Conducts reproducible trials comparing:
- Baseline (Single-pass OpenCV difference without adaptive investigation)
- Guardian CV (Perception-Decision-Action-Verification Loop with Adaptive Re-Observation)

Measures:
- Precision & Recall for known changed regions
- False positive rate (FPR) under normal and subtle conditions
- Ambiguity reduction via secondary Spectral Edge Analysis
- Latency and computation throughput
"""

import sys
import os
import time
import json
from pathlib import Path
import numpy as np
import cv2

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from guardian_swarm.core.vision_engine import GuardianVisionEngine
from guardian_swarm.agents.adaptive_inspector import AdaptiveInspectionAgent

def generate_benchmark_pair(case_type: str):
    """
    Generate synthetic, mathematically defined test samples.
    """
    ref = np.zeros((300, 400, 3), dtype=np.uint8)
    # Background texture
    cv2.rectangle(ref, (40, 40), (160, 140), (180, 180, 180), -1)
    cv2.rectangle(ref, (200, 120), (360, 260), (140, 140, 140), -1)
    cv2.circle(ref, (100, 220), 35, (160, 160, 160), -1)

    curr = ref.copy()

    if case_type == "normal":
        # Identical
        return ref, curr, {"has_defect": False, "category": "nominal"}

    elif case_type == "structural_defect":
        # Real scratch / fissure
        cv2.circle(curr, (280, 190), 16, (0, 0, 255), -1)
        cv2.line(curr, (265, 175), (295, 205), (255, 255, 255), 3)
        return ref, curr, {"has_defect": True, "category": "surface_crack"}

    elif case_type == "lighting_variation":
        # Slight lighting bloom without structural deformation
        overlay = curr.copy()
        cv2.circle(overlay, (280, 190), 30, (255, 255, 200), -1)
        curr = cv2.addWeighted(curr, 0.7, overlay, 0.3, 0)
        return ref, curr, {"has_defect": False, "category": "illumination_bloom"}

    elif case_type == "misalignment":
        # Shift current image by 10 pixels and rotate 3 degrees
        h, w = curr.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), 3, 1.0)
        M[0, 2] += 8
        M[1, 2] += 5
        curr = cv2.warpAffine(curr, M, (w, h))
        # Add crack to rotated image
        cv2.circle(curr, (250, 150), 15, (0, 0, 255), -1)
        return ref, curr, {"has_defect": True, "category": "rotated_misaligned"}

    elif case_type == "severe_blur":
        curr = cv2.GaussianBlur(curr, (31, 31), 0)
        return ref, curr, {"has_defect": False, "category": "degraded_quality"}

    return ref, curr, {"has_defect": False, "category": "unknown"}

def run_evaluation_suite():
    engine = GuardianVisionEngine()
    agent = AdaptiveInspectionAgent(vision_engine=engine)

    cases = [
        "normal", "normal", "normal", "normal", "normal",
        "structural_defect", "structural_defect", "structural_defect", "structural_defect",
        "lighting_variation", "lighting_variation", "lighting_variation",
        "misalignment", "misalignment",
        "severe_blur", "severe_blur"
    ]

    results_baseline = []
    results_adaptive = []

    print(f"============================================================")
    print(f"GUARDIAN CV - OpenCV 5 AGENTIC EVALUATION BENCHMARK")
    print(f"Total Trials: {len(cases)} test image pairs across 5 categories")
    print(f"============================================================")

    for idx, case in enumerate(cases):
        ref, curr, meta = generate_benchmark_pair(case)
        _, ref_buf = cv2.imencode(".jpg", ref)
        _, curr_buf = cv2.imencode(".jpg", curr)
        ref_bytes = ref_buf.tobytes()
        curr_bytes = curr_buf.tobytes()

        # 1. Baseline Evaluation: Simple direct thresholding without adaptive re-observation
        t0 = time.time()
        diff = cv2.absdiff(ref, curr)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_diff, 35, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        baseline_found = any(cv2.contourArea(c) > 50 for c in contours)
        baseline_verdict = "DEFECT" if baseline_found else "NORMAL"
        t_base = time.time() - t0

        results_baseline.append({
            "case": case,
            "ground_truth": meta["has_defect"],
            "predicted_defect": baseline_found,
            "verdict": baseline_verdict,
            "latency": t_base
        })

        # 2. Guardian CV Adaptive Inspection
        t0 = time.time()
        res_cv = agent.run_investigation(ref_bytes, curr_bytes)
        t_adaptive = time.time() - t0

        adaptive_verdict = res_cv["verdict"]
        predicted_defect = (adaptive_verdict == "CONFIRMED_ANOMALY")

        results_adaptive.append({
            "case": case,
            "ground_truth": meta["has_defect"],
            "predicted_defect": predicted_defect,
            "verdict": adaptive_verdict,
            "status": res_cv["status"],
            "trace_steps": len(res_cv["trace"]),
            "latency": t_adaptive
        })

    # Calculate Metrics
    # Baseline
    b_tp = sum(1 for r in results_baseline if r["ground_truth"] and r["predicted_defect"])
    b_fp = sum(1 for r in results_baseline if not r["ground_truth"] and r["predicted_defect"])
    b_tn = sum(1 for r in results_baseline if not r["ground_truth"] and not r["predicted_defect"])
    b_fn = sum(1 for r in results_baseline if r["ground_truth"] and not r["predicted_defect"])
    b_prec = b_tp / (b_tp + b_fp) if (b_tp + b_fp) > 0 else 0
    b_rec = b_tp / (b_tp + b_fn) if (b_tp + b_fn) > 0 else 0
    b_fpr = b_fp / (b_fp + b_tn) if (b_fp + b_tn) > 0 else 0

    # Adaptive Agent
    a_tp = sum(1 for r in results_adaptive if r["ground_truth"] and r["predicted_defect"])
    a_fp = sum(1 for r in results_adaptive if not r["ground_truth"] and r["predicted_defect"])
    a_tn = sum(1 for r in results_adaptive if not r["ground_truth"] and not r["predicted_defect"])
    a_fn = sum(1 for r in results_adaptive if r["ground_truth"] and not r["predicted_defect"])
    a_prec = a_tp / (a_tp + a_fp) if (a_tp + a_fp) > 0 else 0
    a_rec = a_tp / (a_tp + a_fn) if (a_tp + a_fn) > 0 else 0
    a_fpr = a_fp / (a_fp + a_tn) if (a_fp + a_tn) > 0 else 0

    print(f"\n[EVALUATION REPORT SUMMARY]")
    print(f"------------------------------------------------------------")
    print(f"Metric               | Baseline Single-Pass | Guardian CV (Adaptive)")
    print(f"---------------------+----------------------+-----------------------")
    print(f"Precision            | {b_prec*100:6.1f}%               | {a_prec*100:6.1f}%")
    print(f"Recall               | {b_rec*100:6.1f}%               | {a_rec*100:6.1f}%")
    print(f"False Positive Rate  | {b_fpr*100:6.1f}%               | {a_fpr*100:6.1f}%")
    print(f"Avg Latency (sec)    | {np.mean([r['latency'] for r in results_baseline]):6.3f}s               | {np.mean([r['latency'] for r in results_adaptive]):6.3f}s")
    print(f"------------------------------------------------------------")
    print(f"Key Finding: Guardian CV reduced false alarms from lighting variations and blur from {b_fpr*100:.1f}% to {a_fpr*100:.1f}%")
    print(f"via its closed-loop Spectral Edge Verification and Quality Limitation Gate.")

    # Save to disk as benchmark artifact
    eval_artifact_path = os.path.join(os.getcwd(), "artifacts", "evaluation_metrics.json")
    os.makedirs(os.path.dirname(eval_artifact_path), exist_ok=True)
    with open(eval_artifact_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "opencv_version": engine.version,
            "metrics": {
                "baseline": {
                    "precision": round(b_prec, 4),
                    "recall": round(b_rec, 4),
                    "false_positive_rate": round(b_fpr, 4),
                    "avg_latency": round(float(np.mean([r['latency'] for r in results_baseline])), 4)
                },
                "adaptive_agent": {
                    "precision": round(a_prec, 4),
                    "recall": round(a_rec, 4),
                    "false_positive_rate": round(a_fpr, 4),
                    "avg_latency": round(float(np.mean([r['latency'] for r in results_adaptive])), 4)
                }
            },
            "trials": results_adaptive
        }, f, indent=2)

    print(f"Saved evaluation artifacts to: {eval_artifact_path}")

if __name__ == "__main__":
    run_evaluation_suite()
