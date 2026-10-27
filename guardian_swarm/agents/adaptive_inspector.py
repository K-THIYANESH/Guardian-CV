"""
Guardian CV - Adaptive Inspection Agent
========================================
Implements the closed-loop cycle:
Observe -> Evaluate -> Select Action -> Execute -> Reobserve -> Verify

Tracks full decision trace, bounding execution, uncertainty handling,
and human escalation triggers.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from guardian_swarm.core.vision_engine import GuardianVisionEngine

class AdaptiveInspectionAgent:
    """
    Autonomous inspection agent that makes evidence-grounded decisions
    based on substantive OpenCV 5 vision outputs.
    """
    def __init__(self, vision_engine: Optional[GuardianVisionEngine] = None, max_iterations: int = 5):
        self.vision = vision_engine or GuardianVisionEngine()
        self.max_iterations = max_iterations

    def run_investigation(
        self,
        ref_image_bytes: bytes,
        curr_image_bytes: bytes,
        objective: str = "visual_change_investigation",
        allow_human_escalation: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the bounded perception-decision-action-verification loop.
        """
        investigation_id = f"INSP-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()
        trace: List[Dict[str, Any]] = []

        # ==========================================================
        # STEP 1: Decode & Quality Assessment (OBSERVE)
        # ==========================================================
        step_1_id = "STEP_1_QUALITY_ASSESSMENT"
        try:
            ref_img = self.vision.decode_image_from_bytes(ref_image_bytes)
            curr_img = self.vision.decode_image_from_bytes(curr_image_bytes)
        except Exception as e:
            trace.append({
                "step": step_1_id,
                "timestamp": time.time(),
                "action": "image_decoding",
                "status": "FAILED",
                "rationale": f"Corrupted or invalid image input: {str(e)}",
                "decision": "TERMINATE_ERROR"
            })
            return {
                "investigation_id": investigation_id,
                "status": "ERROR",
                "verdict": "UNUSABLE_INPUT",
                "summary": f"Failed to decode image input: {str(e)}",
                "trace": trace,
                "duration_seconds": round(time.time() - start_time, 3)
            }

        ref_quality = self.vision.assess_quality(ref_img)
        curr_quality = self.vision.assess_quality(curr_img)

        trace.append({
            "step": step_1_id,
            "timestamp": time.time(),
            "action": "opencv_quality_assessment",
            "measured_output": {
                "ref_quality": ref_quality,
                "curr_quality": curr_quality
            },
            "status": "COMPLETED",
            "decision_rule": "Both reference and current images must satisfy minimum sharpness (var > 100) and exposure thresholds.",
            "selected_follow_up": "PROCEED" if (ref_quality["is_usable"] and curr_quality["is_usable"]) else "QUALITY_LIMITATION"
        })

        # Scenario A: Degraded quality handling
        if not ref_quality["is_usable"] or not curr_quality["is_usable"]:
            limitations = []
            if ref_quality.get("is_blurry") or curr_quality.get("is_blurry"):
                limitations.append("High blur detected (insufficient focus)")
            if ref_quality.get("is_underexposed") or curr_quality.get("is_underexposed"):
                limitations.append("Underexposed frame (poor illumination)")
            if ref_quality.get("is_overexposed") or curr_quality.get("is_overexposed"):
                limitations.append("Overexposed frame (saturation glare)")

            trace.append({
                "step": "STEP_1_BRANCH_QUALITY_REJECTION",
                "timestamp": time.time(),
                "action": "terminate_with_limitation",
                "status": "STOPPED",
                "rationale": f"Image quality limits reliable comparison: {', '.join(limitations)}",
                "decision": "REQUEST_OPERATOR_INPUT"
            })
            return {
                "investigation_id": investigation_id,
                "status": "CONCLUDED_WITH_LIMITATION",
                "verdict": "INSUFFICIENT_QUALITY",
                "summary": f"Inspection stopped due to quality limitation: {', '.join(limitations)}.",
                "quality_metrics": {"ref": ref_quality, "curr": curr_quality},
                "trace": trace,
                "duration_seconds": round(time.time() - start_time, 3)
            }

        # ==========================================================
        # STEP 2: Feature Alignment / Registration (ACTION -> RE-OBSERVE)
        # ==========================================================
        step_2_id = "STEP_2_ORB_HOMOGRAPHY_REGISTRATION"
        aligned_curr, align_meta = self.vision.register_images(ref_img, curr_img)

        trace.append({
            "step": step_2_id,
            "timestamp": time.time(),
            "action": "opencv_orb_homography",
            "measured_output": align_meta,
            "status": "COMPLETED" if align_meta["success"] else "FALLBACK_DIRECT_RESIZE",
            "decision_rule": "Warp perspective if RANSAC inliers >= 6, else fallback to direct scale normalization with alignment warning.",
            "selected_follow_up": "PROCEED_TO_STRUCTURAL_DIFF"
        })

        # ==========================================================
        # STEP 3: Multi-Scale Structural Difference (EVALUATE EVIDENCE)
        # ==========================================================
        step_3_id = "STEP_3_MORPHOLOGICAL_CHANGE_DETECTION"
        diff_results = self.vision.compute_visual_difference(ref_img, aligned_curr)

        candidate_count = diff_results["total_candidates"]
        trace.append({
            "step": step_3_id,
            "timestamp": time.time(),
            "action": "opencv_morphological_difference",
            "measured_output": {
                "candidate_regions_found": candidate_count,
                "top_region": diff_results["regions"][0]["region_id"] if candidate_count > 0 else None
            },
            "status": "COMPLETED",
            "decision_rule": "If candidate_count == 0 -> Conclude NO_DEFECT; If candidate_count > 0 -> Select top anomaly ROI for Spectral Edge Verification.",
            "selected_follow_up": "TERMINATE_NORMAL" if candidate_count == 0 else "EXECUTE_SPECTRAL_VERIFICATION"
        })

        # Scenario D: No significant visual change detected
        if candidate_count == 0:
            trace.append({
                "step": "STEP_3_BRANCH_NORMAL",
                "timestamp": time.time(),
                "action": "conclude_inspection",
                "status": "VERIFIED_NORMAL",
                "rationale": "No candidate regions exceeded the anomaly surface threshold. Surface matches reference baseline.",
                "decision": "CLOSE_INVESTIGATION"
            })
            return {
                "investigation_id": investigation_id,
                "status": "VERIFIED_NORMAL",
                "verdict": "NOMINAL_NO_CHANGE",
                "summary": "Full OpenCV 5 inspection completed. Zero candidate anomalies detected; component matches reference baseline.",
                "total_regions": 0,
                "regions": [],
                "visuals": {
                    "annotated": diff_results["annotated_b64"],
                    "heatmap": diff_results["heatmap_b64"],
                    "diff_map": diff_results["diff_map_b64"]
                },
                "alignment": align_meta,
                "trace": trace,
                "duration_seconds": round(time.time() - start_time, 3)
            }

        # ==========================================================
        # STEP 4: Targeted Spectral Edge & Histogram Follow-up (ACTION & RE-OBSERVE)
        # ==========================================================
        step_4_id = "STEP_4_SPECTRAL_EDGE_CONFIRMATION"
        primary_roi = diff_results["regions"][0]

        # Execute permitted tool: high_res_spectral_analysis
        spectral_evidence = self.vision.high_res_spectral_analysis(
            ref_crop_b64=primary_roi["ref_crop_b64"],
            curr_crop_b64=primary_roi["curr_crop_b64"]
        )

        trace.append({
            "step": step_4_id,
            "timestamp": time.time(),
            "action": "high_res_spectral_analysis",
            "target_roi": primary_roi["region_id"],
            "measured_output": spectral_evidence,
            "status": "COMPLETED",
            "decision_rule": "If structural change confirmed (Bhattacharyya > 0.35 or edge divergence > 0.05) -> CONFIRMED_DEFECT; Else -> AMBIGUOUS_SHADOW/LIGHTING.",
            "selected_follow_up": "FINALIZE_FINDING" if spectral_evidence["is_structural_change"] else "ESCALATE_OR_FLAG_UNCERTAIN"
        })

        # ==========================================================
        # STEP 5: Verification & Human Supervision Gate (VERIFY)
        # ==========================================================
        step_5_id = "STEP_5_VERIFICATION_AND_GOVERNANCE"
        if spectral_evidence["is_structural_change"]:
            verdict = "CONFIRMED_ANOMALY"
            summary = (
                f"Defect confirmed in {primary_roi['region_id']}: area {primary_roi['area_pixels']} px "
                f"({primary_roi['relative_area_pct']}% of surface). "
                f"Spectral edge divergence of {spectral_evidence['edge_divergence']} and color distance {spectral_evidence['color_bhattacharyya_distance']} "
                f"verify physical surface deviation."
            )
            escalation_required = False
        else:
            verdict = "AMBIGUOUS_POTENTIAL_LIGHTING_ARTIFACT"
            summary = (
                f"Initial difference observed in {primary_roi['region_id']}, but spectral edge analysis "
                f"indicates negligible structural deformation (edge div: {spectral_evidence['edge_divergence']}). "
                f"Flagged as ambiguous/lighting variation requiring human operator sign-off."
            )
            escalation_required = allow_human_escalation

        trace.append({
            "step": step_5_id,
            "timestamp": time.time(),
            "action": "governance_verification",
            "status": "FLAGGED_FOR_HUMAN_REVIEW" if escalation_required else "VERIFIED_AUTONOMOUSLY",
            "rationale": summary,
            "decision": "REQUIRE_HUMAN_SIGN_OFF" if escalation_required else "APPROVE_FINDINGS"
        })

        return {
            "investigation_id": investigation_id,
            "status": "PENDING_HUMAN_APPROVAL" if escalation_required else "COMPLETED",
            "verdict": verdict,
            "summary": summary,
            "escalation_required": escalation_required,
            "primary_roi": primary_roi["region_id"],
            "total_regions": candidate_count,
            "regions": diff_results["regions"],
            "verification_evidence": spectral_evidence,
            "alignment": align_meta,
            "visuals": {
                "annotated": diff_results["annotated_b64"],
                "heatmap": diff_results["heatmap_b64"],
                "diff_map": diff_results["diff_map_b64"],
                "spectral_composite": spectral_evidence.get("edge_composite_b64")
            },
            "trace": trace,
            "duration_seconds": round(time.time() - start_time, 3)
        }
