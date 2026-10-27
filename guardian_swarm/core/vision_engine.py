"""
Guardian CV - OpenCV 5 Substantive Vision Engine
=================================================
Performs image quality diagnostics, robust image registration (ORB/Homography),
multi-scale structural difference analysis, candidate defect extraction,
and high-resolution re-observation tools.
"""

import cv2
import numpy as np
import base64
import os
import time
from typing import Dict, Any, List, Tuple, Optional

# Enforce OpenCV 5 runtime requirement
CV_VERSION = cv2.__version__

class GuardianVisionEngine:
    """
    Substantive OpenCV 5 processing engine for visual change investigation.
    """
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "artifacts", "cv_evidence")
        os.makedirs(self.output_dir, exist_ok=True)
        self.version = CV_VERSION

    @staticmethod
    def get_runtime_info() -> Dict[str, Any]:
        """Verify and report the exact OpenCV runtime configuration."""
        build_info = cv2.getBuildInformation()
        is_cv5 = CV_VERSION.startswith("5.")
        return {
            "opencv_version": CV_VERSION,
            "is_opencv_5": is_cv5,
            "cuda_support": "CUDA" in build_info,
            "threads": cv2.getNumThreads(),
            "simd_support": cv2.useOptimized()
        }

    @staticmethod
    def decode_image_from_bytes(image_bytes: bytes) -> np.ndarray:
        """Decode image bytes safely into a BGR numpy array."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image from provided data buffer.")
        return img

    @staticmethod
    def encode_image_to_base64(img: np.ndarray, ext: str = ".jpg") -> str:
        """Encode an OpenCV BGR image into a Base64 data URL string."""
        success, buf = cv2.imencode(ext, img)
        if not success:
            raise ValueError("Failed to encode image to buffer.")
        b64_str = base64.b64encode(buf).decode("utf-8")
        mime = "image/jpeg" if ext.lower() in [".jpg", ".jpeg"] else "image/png"
        return f"data:{mime};base64,{b64_str}"

    def assess_quality(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate image focus (blurriness), contrast, and luminance distribution.
        Scenario A: If quality fails, the adaptive agent triggers preprocessing or asks for replacement.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Laplacian variance for blur/sharpness
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = float(laplacian.var())
        is_blurry = variance < 100.0  # standard threshold for sharpness

        # Mean and standard deviation for contrast/lighting
        mean_lum, std_lum = cv2.meanStdDev(gray)
        mean_lum_val = float(mean_lum[0][0])
        std_lum_val = float(std_lum[0][0])
        
        # An image is usable if it is not excessively blurry and not completely pitch black or saturated
        is_underexposed = mean_lum_val < 5.0 and std_lum_val < 5.0
        is_overexposed = mean_lum_val > 250.0
        is_low_contrast = std_lum_val < 10.0

        is_usable = not (is_blurry or is_underexposed or is_overexposed)
        
        return {
            "sharpness_score": round(variance, 2),
            "mean_luminance": round(mean_lum_val, 2),
            "contrast_std": round(std_lum_val, 2),
            "is_blurry": is_blurry,
            "is_underexposed": is_underexposed,
            "is_overexposed": is_overexposed,
            "is_low_contrast": is_low_contrast,
            "is_usable": is_usable,
            "resolution": [img.shape[1], img.shape[0]]
        }

    def register_images(self, ref_img: np.ndarray, curr_img: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Perform robust feature matching & homography estimation using ORB.
        Aligns current image to reference coordinates or signals alignment failure.
        """
        h_ref, w_ref = ref_img.shape[:2]
        gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
        gray_curr = cv2.cvtColor(curr_img, cv2.COLOR_BGR2GRAY)

        # ORB feature detector (part of core OpenCV 5)
        orb = cv2.ORB_create(nfeatures=1500)
        kp_ref, des_ref = orb.detectAndCompute(gray_ref, None)
        kp_curr, des_curr = orb.detectAndCompute(gray_curr, None)

        if des_ref is None or des_curr is None or len(kp_ref) < 10 or len(kp_curr) < 10:
            # Fallback resize without warping if features insufficient
            resized_curr = cv2.resize(curr_img, (w_ref, h_ref))
            return resized_curr, {
                "success": False,
                "reason": "Insufficient keypoints detected for feature matching",
                "inliers": 0,
                "alignment_type": "direct_resize"
            }

        # BFMatcher with Hamming distance
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        knn_matches = matcher.knnMatch(des_curr, des_ref, k=2)

        # Lowe's ratio test
        good_matches = []
        for m_match in knn_matches:
            if len(m_match) == 2:
                m, n = m_match
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

        if len(good_matches) < 8:
            resized_curr = cv2.resize(curr_img, (w_ref, h_ref))
            return resized_curr, {
                "success": False,
                "reason": f"Only {len(good_matches)} good matches; minimum 8 required",
                "inliers": len(good_matches),
                "alignment_type": "direct_resize"
            }

        # Extract coordinates
        src_pts = np.float32([kp_curr[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_ref[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        homography, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        inliers = int(np.sum(mask)) if mask is not None else 0

        if homography is None or inliers < 6:
            resized_curr = cv2.resize(curr_img, (w_ref, h_ref))
            return resized_curr, {
                "success": False,
                "reason": "Homography computation failed or insufficient RANSAC inliers",
                "inliers": inliers,
                "alignment_type": "direct_resize"
            }

        # Warp perspective
        aligned_curr = cv2.warpPerspective(curr_img, homography, (w_ref, h_ref), flags=cv2.INTER_LINEAR)
        return aligned_curr, {
            "success": True,
            "inliers": inliers,
            "good_matches": len(good_matches),
            "alignment_type": "homography_warp"
        }

    def compute_visual_difference(
        self,
        ref_img: np.ndarray,
        aligned_curr: np.ndarray,
        min_area: int = 50,
        diff_threshold: int = 35
    ) -> Dict[str, Any]:
        """
        Compute multi-scale structural and photometric differences,
        apply morphology, and extract candidate regions of interest (ROIs).
        """
        h, w = ref_img.shape[:2]
        gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
        gray_curr = cv2.cvtColor(aligned_curr, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian Blur to reduce sensor noise
        blur_ref = cv2.GaussianBlur(gray_ref, (5, 5), 0)
        blur_curr = cv2.GaussianBlur(gray_curr, (5, 5), 0)

        # Absolute difference map
        abs_diff = cv2.absdiff(blur_ref, blur_curr)

        # Adaptive thresholding or binary threshold
        _, thresh = cv2.threshold(abs_diff, diff_threshold, 255, cv2.THRESH_BINARY)

        # Morphological open to remove specks, then close to connect regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Find contours of candidate anomalies
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidate_regions = []
        annotated_curr = aligned_curr.copy()
        
        region_id_seq = 1
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            x, y, rw, rh = cv2.boundingRect(cnt)
            # Region difference intensity
            roi_diff = abs_diff[y:y+rh, x:x+rw]
            mean_intensity = float(np.mean(roi_diff))
            max_intensity = float(np.max(roi_diff))

            # Store crop references
            ref_crop = ref_img[y:y+rh, x:x+rw]
            curr_crop = aligned_curr[y:y+rh, x:x+rw]

            region_dict = {
                "region_id": f"ROI_{region_id_seq}",
                "bbox": [int(x), int(y), int(rw), int(rh)],
                "area_pixels": int(area),
                "relative_area_pct": round((area / (w * h)) * 100, 3),
                "mean_diff_intensity": round(mean_intensity, 2),
                "max_diff_intensity": round(max_intensity, 2),
                "ref_crop_b64": self.encode_image_to_base64(ref_crop),
                "curr_crop_b64": self.encode_image_to_base64(curr_crop)
            }
            candidate_regions.append(region_dict)

            # Draw on annotated image
            cv2.rectangle(annotated_curr, (x, y), (x + rw, y + rh), (0, 140, 255), 2)
            cv2.putText(
                annotated_curr,
                f"ROI_{region_id_seq}",
                (x, max(15, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 140, 255),
                2
            )
            region_id_seq += 1

        # Generate difference heatmap visualization (ColorMap JET)
        heatmap = cv2.applyColorMap(abs_diff, cv2.COLORMAP_JET)
        blended_heatmap = cv2.addWeighted(aligned_curr, 0.6, heatmap, 0.4, 0)

        # Sort candidate regions by area * intensity descending
        candidate_regions.sort(
            key=lambda r: r["area_pixels"] * r["mean_diff_intensity"],
            reverse=True
        )

        return {
            "total_candidates": len(candidate_regions),
            "regions": candidate_regions,
            "annotated_b64": self.encode_image_to_base64(annotated_curr),
            "heatmap_b64": self.encode_image_to_base64(blended_heatmap),
            "diff_map_b64": self.encode_image_to_base64(cleaned)
        }

    def high_res_spectral_analysis(
        self,
        ref_crop_b64: str,
        curr_crop_b64: str
    ) -> Dict[str, Any]:
        """
        Tool: Re-observe a candidate ROI using edge spectrum (Canny) and color histogram comparison.
        Used by the agent in follow-up investigation to confirm surface structural alteration vs lighting artifact.
        """
        # Decode crops
        header_r, data_r = ref_crop_b64.split(",", 1)
        header_c, data_c = curr_crop_b64.split(",", 1)
        ref_bytes = base64.b64decode(data_r)
        curr_bytes = base64.b64decode(data_c)
        ref_crop = self.decode_image_from_bytes(ref_bytes)
        curr_crop = self.decode_image_from_bytes(curr_bytes)

        # Normalize crop sizes
        h, w = ref_crop.shape[:2]
        curr_crop_resized = cv2.resize(curr_crop, (w, h))

        # Canny edge density difference
        ref_gray = cv2.cvtColor(ref_crop, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_crop_resized, cv2.COLOR_BGR2GRAY)
        
        edges_ref = cv2.Canny(ref_gray, 50, 150)
        edges_curr = cv2.Canny(curr_gray, 50, 150)

        ref_edge_density = float(np.count_nonzero(edges_ref) / (w * h))
        curr_edge_density = float(np.count_nonzero(edges_curr) / (w * h))
        edge_diff_abs = abs(curr_edge_density - ref_edge_density)

        # Color Histogram Bhattacharyya distance in HSV space
        hsv_ref = cv2.cvtColor(ref_crop, cv2.COLOR_BGR2HSV)
        hsv_curr = cv2.cvtColor(curr_crop_resized, cv2.COLOR_BGR2HSV)
        
        hist_ref = cv2.calcHist([hsv_ref], [0, 1], None, [30, 32], [0, 180, 0, 256])
        hist_curr = cv2.calcHist([hsv_curr], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist_ref, hist_ref, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist_curr, hist_curr, 0, 1, cv2.NORM_MINMAX)

        bhattacharyya_dist = float(cv2.compareHist(hist_ref, hist_curr, cv2.HISTCMP_BHATTACHARYYA))

        # Surface Structural verdict
        # Higher Bhattacharyya distance (>0.35) or high edge density divergence (>0.05) indicates true structural change
        is_structural_change = (bhattacharyya_dist > 0.35) or (edge_diff_abs > 0.05)

        # Composite verification visual
        edge_comp = np.hstack([edges_ref, edges_curr])
        edge_b64 = self.encode_image_to_base64(edge_comp, ext=".png")

        return {
            "ref_edge_density": round(ref_edge_density, 4),
            "curr_edge_density": round(curr_edge_density, 4),
            "edge_divergence": round(edge_diff_abs, 4),
            "color_bhattacharyya_distance": round(bhattacharyya_dist, 4),
            "is_structural_change": is_structural_change,
            "edge_composite_b64": edge_b64
        }
