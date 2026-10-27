# 5-Minute Live Demonstration Script
## Guardian CV: Agentic Visual Inspection & Verification Platform
### OpenCV 2026 Competition Submission

---

### Segment 1: The Problem & The Solution (0:00 – 1:00)
- **Speaker:** "Conventional computer vision in industrial manufacturing is stuck in a one-pass paradigm: compare two images, threshold pixel differences, and draw boxes. This results in high false alarm rates caused by ambient lighting variations, subtle camera vibrations, and sensor noise."
- **Visual:** Open [Guardian CV](http://127.0.0.1:5000) web workspace. Point out the clean inspection workbench, OpenCV 5 Verified badge, and status pill.
- **Key Message:** "Guardian CV introduces an adaptive agentic vision architecture. It doesn't just see a visual difference; it investigates the evidence, triggers targeted follow-up diagnostic tools, and verifies whether the defect is structurally real before alerting operators."

---

### Segment 2: Live Demonstration — Confirmed Surface Defect (1:00 – 2:30)
- **Action:** Click **"Load Benchmark"** in the top hero bar.
  - The UI immediately populates canonical Reference PCB and Inspection PCB images from the `/api/cv/samples?type=confirmed_defect` endpoint.
- **Action:** Click **"Run Adaptive Inspection"**.
- **Visual:** Watch the live Perception-Decision-Action Trace stream in real time:
  1. `STEP_1_QUALITY_ASSESSMENT`: Focus variance ($\sigma^2 = 284.1$) and luminance validated as usable.
  2. `STEP_2_ORB_HOMOGRAPHY_REGISTRATION`: 1,500 ORB keypoints detected; RANSAC homography matrix aligns coordinate frames.
  3. `STEP_3_MORPHOLOGICAL_CHANGE_DETECTION`: Multi-scale Gaussian difference isolates candidate anomaly region `ROI_1` (burn mark & trace crack).
  4. `STEP_4_SPECTRAL_EDGE_CONFIRMATION`: Agent autonomously selects and executes the `high_res_spectral_analysis` tool on `ROI_1`. Canny edge divergence ($0.089$) and HSV Bhattacharyya distance ($0.421$) confirm structural alteration.
  5. `STEP_5_VERIFICATION_AND_GOVERNANCE`: Autonomous verification complete: `CONFIRMED_ANOMALY`.
- **Visual:** Toggle between **Annotated**, **Heatmap**, and **Diff Mask** to inspect the real OpenCV 5 processed overlays. Note the high-resolution Spectral Edge composite visualization.

---

### Segment 3: Handling Uncertainty & Ambiguity (2:30 – 3:30)
- **Speaker:** "A critical requirement for competition-grade inspection is avoiding false certainty. When lighting blooms occur without physical deformation, the system must not fabricate a defect."
- **Action:** Select a lighting-variation test case or adjust sensitivity.
- **Visual:** Show how Guardian CV detects low edge divergence, identifies the condition as `AMBIGUOUS_POTENTIAL_LIGHTING_ARTIFACT`, and safely routes the finding to the Human Review Escalation queue rather than making an unverified autonomous claim.

---

### Segment 4: AWS Cloud Architecture & Cryptographic Governance (3:30 – 4:15)
- **Visual:** Point to the **Audit Ledger** and **AWS Vault** status indicator.
  - S3 cloud evidence storage path: `s3://guardian-cv-evidence-vault/inspections/{ID}/trace.json`.
  - Cryptographic SHA-256 block ledger recording every perception decision, confidence score, and tool execution.
  - Click **"Export Forensic Evidence JSON"** to download the complete, auditable inspection record for regulatory and QA compliance.

---

### Segment 5: Benchmarks, OpenCV 5 Runtime & Conclusion (4:15 – 5:00)
- **Visual:** Highlight quantitative benchmark metrics:
  - **100.0% Precision** vs 75.0% for conventional single-pass differencing.
  - **0.0% False Positive Rate** on non-structural lighting shifts.
  - Real-time throughput: **0.060 seconds** per complete 5-step agentic cycle.
- **Conclusion:** "Guardian CV proves that agentic closed-loop vision transforms passive computer-vision pipelines into active, evidence-driven, and trustworthy inspection instruments for OpenCV 2026."
