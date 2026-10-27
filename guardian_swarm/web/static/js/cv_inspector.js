/**
 * Guardian CV — Agentic Vision Inspector
 * ========================================
 * Full frontend controller for the OpenCV 5 inspection pipeline.
 * Features: drag-and-drop uploads, live trace rendering, region overlays,
 * benchmark generation, forensic export, adaptive re-observation display.
 *
 * Competition: OpenCV 2026 — Agentic Vision Special Award
 */

document.addEventListener("DOMContentLoaded", () => {

    // ─── Element References ───────────────────────────────────────────────
    const dropzoneRef       = document.getElementById("dropzone-ref");
    const dropzoneCurr      = document.getElementById("dropzone-curr");
    const inputRefFile      = document.getElementById("input-ref-file");
    const inputCurrFile     = document.getElementById("input-curr-file");
    const btnStartInspection = document.getElementById("btn-start-cv-inspection");
    const btnLoadSamples    = document.getElementById("btn-load-cv-samples");
    const btnExportReport   = document.getElementById("btn-export-cv-report");

    let refImageBase64 = null;
    let currImageBase64 = null;
    let currentInspectionResult = null;

    // ─── Fetch runtime status ─────────────────────────────────────────────
    async function fetchRuntimeStatus() {
        try {
            const res = await fetch("/api/cv/runtime");
            const data = await res.json();
            const awsBadge = document.getElementById("cv-aws-badge");
            if (awsBadge && data.aws) {
                if (data.aws.is_connected) {
                    awsBadge.innerHTML = '<span class="cv-badge-dot"></span>AWS: S3 Live Vault';
                    awsBadge.className = "cv-badge cv-badge-green";
                } else {
                    awsBadge.innerHTML = '<span class="cv-badge-dot"></span>AWS: Sandboxed (Local)';
                    awsBadge.className = "cv-badge cv-badge-orange";
                }
            }
        } catch (e) {
            console.debug("CV runtime status unavailable:", e.message);
        }
    }
    fetchRuntimeStatus();

    // ─── Drag-and-drop helpers ─────────────────────────────────────────────
    function setupDropzone(zone, inputEl, type) {
        if (!zone || !inputEl) return;

        zone.addEventListener("click", () => inputEl.click());

        zone.addEventListener("dragover", (e) => {
            e.preventDefault();
            zone.classList.add("dragover");
        });
        zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
        zone.addEventListener("drop", (e) => {
            e.preventDefault();
            zone.classList.remove("dragover");
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith("image/")) {
                handleFileSelect(file, type);
            }
        });

        inputEl.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) handleFileSelect(file, type);
        });
    }

    setupDropzone(dropzoneRef,  inputRefFile,  "ref");
    setupDropzone(dropzoneCurr, inputCurrFile, "curr");

    // ─── File select handler ───────────────────────────────────────────────
    function handleFileSelect(file, type) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const b64 = e.target.result;
            if (type === "ref") {
                refImageBase64 = b64;
                document.getElementById("ref-placeholder").style.display = "none";
                document.getElementById("ref-preview-box").style.display = "block";
                document.getElementById("ref-preview-img").src = b64;
                document.getElementById("ref-filename").textContent = file.name;
            } else {
                currImageBase64 = b64;
                document.getElementById("curr-placeholder").style.display = "none";
                document.getElementById("curr-preview-box").style.display = "block";
                document.getElementById("curr-preview-img").src = b64;
                document.getElementById("curr-filename").textContent = file.name;
            }
        };
        reader.readAsDataURL(file);
    }

    // ─── Load Benchmark Sample ─────────────────────────────────────────────
    if (btnLoadSamples) {
        btnLoadSamples.addEventListener("click", async () => {
            try {
                btnLoadSamples.textContent = "Loading Benchmark...";
                btnLoadSamples.disabled = true;

                // Attempt to fetch deterministic server-side OpenCV benchmark first
                try {
                    const res = await fetch("/api/cv/samples?type=confirmed_defect");
                    if (res.ok) {
                        const data = await res.json();
                        refImageBase64 = data.reference_b64;
                        currImageBase64 = data.current_b64;

                        document.getElementById("ref-placeholder").style.display = "none";
                        document.getElementById("ref-preview-box").style.display = "block";
                        document.getElementById("ref-preview-img").src = refImageBase64;
                        document.getElementById("ref-filename").textContent = "benchmark_pcb_reference.jpg";

                        document.getElementById("curr-placeholder").style.display = "none";
                        document.getElementById("curr-preview-box").style.display = "block";
                        document.getElementById("curr-preview-img").src = currImageBase64;
                        document.getElementById("curr-filename").textContent = "benchmark_pcb_defective.jpg";

                        btnLoadSamples.textContent = "✓ Benchmark Loaded";
                        setTimeout(() => {
                            btnLoadSamples.textContent = "Load Benchmark";
                            btnLoadSamples.disabled = false;
                        }, 2000);
                        return;
                    }
                } catch (netErr) {
                    console.debug("Remote benchmark sample fetch fallback to local canvas generator:", netErr.message);
                }

                // Generate realistic industrial reference image
                const refCanvas = document.createElement("canvas");
                refCanvas.width = 512;
                refCanvas.height = 384;
                const ctxRef = refCanvas.getContext("2d");

                // Background — industrial dark grey panel
                ctxRef.fillStyle = "#1a1f2e";
                ctxRef.fillRect(0, 0, 512, 384);

                // Component grid pattern
                ctxRef.strokeStyle = "#2d3748";
                ctxRef.lineWidth = 1;
                for (let x = 0; x < 512; x += 32) {
                    ctxRef.beginPath(); ctxRef.moveTo(x, 0); ctxRef.lineTo(x, 384); ctxRef.stroke();
                }
                for (let y = 0; y < 384; y += 32) {
                    ctxRef.beginPath(); ctxRef.moveTo(0, y); ctxRef.lineTo(512, y); ctxRef.stroke();
                }

                // PCB components
                ctxRef.fillStyle = "#4a5568";
                ctxRef.fillRect(60, 80, 120, 80);    // Chip A
                ctxRef.fillRect(240, 140, 130, 90);  // Chip B
                ctxRef.fillRect(400, 60, 80, 60);    // Cap bank

                // Solder pads
                ctxRef.fillStyle = "#c6a64a";
                [[60,80],[80,80],[100,80],[120,80],[140,80],[160,80],[180,80]].forEach(([x,y]) => {
                    ctxRef.beginPath(); ctxRef.arc(x, y, 4, 0, 2*Math.PI); ctxRef.fill();
                });

                // Labels
                ctxRef.fillStyle = "#a0aec0";
                ctxRef.font = "bold 11px monospace";
                ctxRef.fillText("U4 — GUARDIAN INDUSTRIAL CTRL", 55, 72);
                ctxRef.fillText("IC-PROC-A", 70, 125);
                ctxRef.fillText("IC-PROC-B", 255, 190);
                ctxRef.fillText("C-BANK-1", 405, 55);
                ctxRef.fillStyle = "#718096";
                ctxRef.font = "9px monospace";
                ctxRef.fillText("REF: PCB-UNIT-04 // BASELINE", 50, 360);

                refImageBase64 = refCanvas.toDataURL("image/jpeg", 0.92);

                // Generate current image with DEFECT
                const currCanvas = document.createElement("canvas");
                currCanvas.width = 512;
                currCanvas.height = 384;
                const ctxCurr = currCanvas.getContext("2d");
                ctxCurr.drawImage(refCanvas, 0, 0);

                // DEFECT 1: Burn/discoloration on Chip B
                const grad = ctxCurr.createRadialGradient(305, 185, 0, 305, 185, 30);
                grad.addColorStop(0, "rgba(220, 38, 38, 0.9)");
                grad.addColorStop(0.5, "rgba(180, 60, 0, 0.6)");
                grad.addColorStop(1, "rgba(0,0,0,0)");
                ctxCurr.fillStyle = grad;
                ctxCurr.beginPath();
                ctxCurr.arc(305, 185, 30, 0, 2 * Math.PI);
                ctxCurr.fill();

                // DEFECT 2: Crack / lifted component
                ctxCurr.strokeStyle = "#fbbf24";
                ctxCurr.lineWidth = 2.5;
                ctxCurr.beginPath();
                ctxCurr.moveTo(285, 175); ctxCurr.lineTo(295, 185);
                ctxCurr.lineTo(288, 193); ctxCurr.lineTo(300, 200);
                ctxCurr.stroke();

                // DEFECT 3: Missing pad (dark spot on solder)
                ctxCurr.fillStyle = "#0a0a0a";
                ctxCurr.beginPath();
                ctxCurr.arc(80, 80, 5, 0, 2 * Math.PI);
                ctxCurr.fill();

                // Annotation overlay
                ctxCurr.strokeStyle = "#ef4444";
                ctxCurr.lineWidth = 2;
                ctxCurr.setLineDash([4, 3]);
                ctxCurr.strokeRect(275, 155, 65, 65);
                ctxCurr.setLineDash([]);

                ctxCurr.fillStyle = "#ef4444";
                ctxCurr.font = "bold 10px monospace";
                ctxCurr.fillText("⚠ DEFECT ZONE", 275, 148);

                currImageBase64 = currCanvas.toDataURL("image/jpeg", 0.92);

                // Update UI
                document.getElementById("ref-placeholder").style.display = "none";
                document.getElementById("ref-preview-box").style.display = "block";
                document.getElementById("ref-preview-img").src = refImageBase64;
                document.getElementById("ref-filename").textContent = "benchmark_pcb_reference.jpg";

                document.getElementById("curr-placeholder").style.display = "none";
                document.getElementById("curr-preview-box").style.display = "block";
                document.getElementById("curr-preview-img").src = currImageBase64;
                document.getElementById("curr-filename").textContent = "benchmark_pcb_defective.jpg";

                btnLoadSamples.textContent = "✓ Benchmark Loaded";
                setTimeout(() => {
                    btnLoadSamples.textContent = "Load Benchmark";
                    btnLoadSamples.disabled = false;
                }, 2000);

            } catch (err) {
                console.error("Benchmark generation failed:", err);
                btnLoadSamples.textContent = "Load Benchmark";
                btnLoadSamples.disabled = false;
            }
        });
    }

    // ─── View Toggle (Annotated / Heatmap / Diff Mask) ───────────────────
    document.querySelectorAll(".cv-toggle-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".cv-toggle-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const imgType = btn.getAttribute("data-img");
            const evidenceImg = document.getElementById("cv-evidence-img");

            if (!currentInspectionResult || !currentInspectionResult.visuals) return;

            const imgKey = imgType === "annotated" ? "annotated" :
                           imgType === "heatmap"   ? "heatmap"   : "diff_map";
            const src = currentInspectionResult.visuals[imgKey];
            if (src && evidenceImg) {
                evidenceImg.src = src;
            }
        });
    });

    // ─── Run Adaptive Inspection ───────────────────────────────────────────
    if (btnStartInspection) {
        btnStartInspection.addEventListener("click", async () => {
            if (!refImageBase64 || !currImageBase64) {
                showCvAlert("Please select both a reference image and a current inspection image first.", "warning");
                return;
            }

            const objective = document.getElementById("cv-objective-select").value;
            const sensitivitySelect = document.getElementById("cv-sensitivity-select");
            const sensitivity = sensitivitySelect ? sensitivitySelect.value : "standard";

            const timeline    = document.getElementById("cv-trace-timeline");
            const verdictTitle = document.getElementById("cv-verdict-title");
            const verdictSummary = document.getElementById("cv-verdict-summary");
            const evidenceDisplay = document.getElementById("cv-evidence-display");

            // Disable & loading state
            btnStartInspection.disabled = true;
            btnStartInspection.innerHTML = `<span class="pulsing-dot"></span> Running Adaptive Inspection...`;

            // Show loading bar
            const loadingBar = document.getElementById("cv-loading-bar");
            if (loadingBar) loadingBar.style.display = "block";

            // Reset display
            document.getElementById("cv-evidence-placeholder").style.display = "none";
            document.getElementById("cv-evidence-img").style.display = "none";
            document.getElementById("cv-spectral-row").style.display = "none";
            document.getElementById("cv-metrics-row").style.display = "none";

            timeline.innerHTML = renderTraceStep("INIT", "Initializing OpenCV 5 Vision Engine & Quality Diagnostics...", "🔵", "#60a5fa");

            try {
                // Stream simulated agent trace steps while waiting for backend
                const traceIntervals = [
                    [700,  "QUALITY_GATE",   "Assessing image sharpness (Laplacian variance), luminance & contrast...", "🔍", "#f59e0b"],
                    [1400, "REGISTRATION",   "Extracting ORB keypoints & performing BFMatcher with Lowe ratio test...", "🔗", "#a78bfa"],
                    [2100, "HOMOGRAPHY",     "Computing RANSAC homography — aligning perspective coordinates...", "📐", "#a78bfa"],
                    [2800, "DIFF_ANALYSIS",  "Computing multi-scale structural difference map with morphological ops...", "⚡", "#f97316"],
                    [3500, "CONTOUR_DETECT", "Extracting candidate anomaly contours & bounding ROI regions...", "🎯", "#f97316"],
                    [4200, "VERDICT_EVAL",   "Evaluating thresholds & preparing Adaptive Re-Observation tools...", "🤖", "#22c55e"],
                ];

                const timers = traceIntervals.map(([delay, step, detail, icon, color]) =>
                    setTimeout(() => {
                        timeline.innerHTML += renderTraceStep(step, detail, icon, color);
                        timeline.scrollTop = timeline.scrollHeight;
                    }, delay)
                );

                const response = await fetch("/api/cv/inspect", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        reference_b64: refImageBase64,
                        current_b64: currImageBase64,
                        objective: objective
                    })
                });

                timers.forEach(t => clearTimeout(t));

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || "Inspection encountered a server error.");
                }

                currentInspectionResult = data;

                // ── Render Verdict ──────────────────────────────────────────
                verdictTitle.textContent = data.verdict;
                const verdictColor = data.verdict === "CONFIRMED_ANOMALY" ? "#ef4444" :
                                     data.verdict === "NOMINAL_NO_CHANGE" ? "#22c55e" : "#f59e0b";
                verdictTitle.style.color = verdictColor;
                verdictSummary.textContent = data.summary;

                // Add verdict glow to card
                const verdictCard = document.getElementById("cv-verdict-card");
                if (verdictCard) {
                    verdictCard.style.borderColor = verdictColor;
                    verdictCard.style.boxShadow = `0 0 12px ${verdictColor}22`;
                }

                // ── Show Evidence Image ─────────────────────────────────────
                const evidenceImg = document.getElementById("cv-evidence-img");
                evidenceImg.style.display = "block";
                evidenceImg.src = data.visuals ? data.visuals.annotated : "";

                // ── Reset toggle buttons to Annotated ──────────────────────
                document.querySelectorAll(".cv-toggle-btn").forEach(b => b.classList.remove("active"));
                const annotatedBtn = document.querySelector(".cv-toggle-btn[data-img='annotated']");
                if (annotatedBtn) annotatedBtn.classList.add("active");

                // ── Render Metrics Pills ────────────────────────────────────
                document.getElementById("cv-metrics-row").style.display = "flex";
                document.getElementById("metric-regions").textContent   = data.total_regions || 0;
                const regionsArr = data.regions || data.candidate_regions || [];
                const topRegion = regionsArr.length > 0 ? regionsArr[0] : null;
                document.getElementById("metric-intensity").textContent = topRegion ? (topRegion.max_diff_intensity || 0).toFixed(1) : "—";
                document.getElementById("metric-coverage").textContent  = topRegion ? (topRegion.relative_area_pct || 0).toFixed(2) + "%" : "—";
                const regInfo = data.alignment || data.registration_info || {};
                document.getElementById("metric-alignment").textContent = regInfo.alignment_type || "ORB/RANSAC";


                // ── Render Trace Timeline ───────────────────────────────────
                timeline.innerHTML = "";
                if (data.trace && data.trace.length > 0) {
                    data.trace.forEach((step, i) => {
                        const status = (step.status || "").toUpperCase();
                        const stepIcon = status === "COMPLETED" ? "✅" :
                                         status === "REOBSERVING" ? "🔄" :
                                         status === "SKIPPED" ? "⏭" :
                                         status === "EXECUTING" ? "⚡" : "▶";
                        const stepColor = status === "COMPLETED" ? "#22c55e" :
                                          status === "REOBSERVING" ? "#a78bfa" :
                                          status === "SKIPPED" ? "#6b7280" : "#f97316";
                        const detail = step.decision_rule || step.rationale || step.action || step.status || "";
                        timeline.innerHTML += renderTraceStep(
                            step.step || `Step ${i + 1}`,
                            detail,
                            stepIcon,
                            stepColor
                        );
                    });
                    timeline.scrollTop = timeline.scrollHeight;
                }

                // ── Render Spectral Re-Observation Evidence ─────────────────
                const spectralRow = document.getElementById("cv-spectral-row");
                const ve = data.verification_evidence || {};
                const spectralSrc = (data.visuals && data.visuals.spectral_composite)
                    ? data.visuals.spectral_composite
                    : ve.edge_composite_b64 || null;

                if (ve && Object.keys(ve).length > 0 && spectralSrc) {
                    spectralRow.style.display = "block";
                    document.getElementById("cv-spectral-composite-img").src = spectralSrc;
                    document.getElementById("cv-spectral-metrics").innerHTML = `
                        <div>Edge Divergence: <strong style="color:#fff;">${(ve.edge_divergence || 0).toFixed(4)}</strong></div>
                        <div>Ref Edge Density: <strong style="color:#9ca3af;">${(ve.ref_edge_density || 0).toFixed(4)}</strong></div>
                        <div>Curr Edge Density: <strong style="color:#9ca3af;">${(ve.curr_edge_density || 0).toFixed(4)}</strong></div>
                        <div>HSV Bhattacharyya: <strong style="color:#fff;">${(ve.color_bhattacharyya_distance || 0).toFixed(4)}</strong></div>
                        <div>Structural Change: <strong style="color:${ve.is_structural_change ? '#ef4444' : '#22c55e'}">${ve.is_structural_change ? '✓ CONFIRMED' : '✗ NOT DETECTED'}</strong></div>
                    `;
                } else {
                    spectralRow.style.display = "none";
                }

                // ── Render Regions Panel ────────────────────────────────────
                const regionsList = document.getElementById("cv-regions-list");
                if (regionsList && regionsArr.length > 0) {
                    regionsList.innerHTML = regionsArr.map((r, i) => `
                        <div style="background:var(--bg-card); border:1px solid ${i === 0 ? '#ef4444' : 'var(--border-color)'}; border-radius:6px; padding:8px 10px;">
                            <div style="font-weight:700; color:${i === 0 ? '#ef4444' : '#f97316'}; font-size:11px;">${r.region_id}</div>
                            <div style="color:var(--text-secondary); margin-top:3px; line-height:1.6;">
                                <div>BBox: [${(r.bbox || []).join(', ')}]</div>
                                <div>Area: ${(r.area_pixels || 0).toLocaleString()} px (${r.relative_area_pct || 0}%)</div>
                                <div>Intensity: Mean ${r.mean_diff_intensity || 0} / Max ${r.max_diff_intensity || 0}</div>
                            </div>
                            <div style="display:flex; gap:6px; margin-top:6px;">
                                ${r.ref_crop_b64 ? `<img src="${r.ref_crop_b64}" style="height:40px; border:1px solid #333; border-radius:3px;" title="Reference ROI">` : ''}
                                ${r.curr_crop_b64 ? `<img src="${r.curr_crop_b64}" style="height:40px; border:1px solid #ef4444; border-radius:3px;" title="Current ROI (anomaly)">` : ''}
                            </div>
                        </div>
                    `).join("");
                } else if (regionsList) {
                    regionsList.innerHTML = '<div style="color:var(--text-muted); font-family:var(--font-mono); font-size:11px;">No anomaly regions detected — images appear nominal.</div>';
                }

                // ── Cloud / Vault Status ─────────────────────────────────────
                const cloudStatus = document.getElementById("cv-cloud-status");
                if (cloudStatus && data.cloud_vault) {
                    cloudStatus.textContent = `✔ Vault: ${data.cloud_vault.storage || 'local'} (${data.cloud_vault.uri || 'local'})`;
                    cloudStatus.style.color = "#22c55e";
                }

                // ── Update history badge ─────────────────────────────────────
                fetch('/api/cv/history').then(r => r.json()).then(hist => {
                    if (hist.inspections && hist.inspections.length > 0) {
                        const badge = document.getElementById('nav-history-count');
                        if (badge) { badge.style.display = 'inline-block'; badge.textContent = hist.inspections.length; }
                    }
                }).catch(() => {});



            } catch (err) {
                console.error("Inspection error:", err);
                verdictTitle.textContent = "Inspection Failed";
                verdictTitle.style.color = "#ef4444";
                verdictSummary.textContent = err.message || "An unexpected error occurred during inspection.";
                timeline.innerHTML += renderTraceStep("ERROR", err.message, "❌", "#ef4444");
                document.getElementById("cv-evidence-placeholder").style.display = "flex";
                document.getElementById("cv-evidence-img").style.display = "none";
            } finally {
                btnStartInspection.disabled = false;
                btnStartInspection.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:15px;height:15px;"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Adaptive Inspection`;
                if (loadingBar) loadingBar.style.display = "none";
            }
        });
    }

    // ─── Render trace step HTML ────────────────────────────────────────────
    function renderTraceStep(stepName, detail, icon, color) {
        return `<div class="cv-trace-item">
            <div class="cv-trace-step-header" style="color:${color};">
                <span class="cv-trace-step-icon">${icon}</span>
                <span>▶ ${stepName}</span>
            </div>
            <div class="cv-trace-step-detail">${detail}</div>
        </div>`;
    }

    // ─── Export Forensic Report JSON ───────────────────────────────────────
    if (btnExportReport) {
        btnExportReport.addEventListener("click", () => {
            if (!currentInspectionResult) {
                showCvAlert("No inspection data available. Run an inspection first.", "warning");
                return;
            }
            const exportData = {
                ...currentInspectionResult,
                export_timestamp: new Date().toISOString(),
                product: "Guardian CV",
                competition: "OpenCV 2026 — Agentic Vision Special Award"
            };
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `guardian_cv_forensic_${currentInspectionResult.investigation_id || Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    // ─── Utility: Show CV-specific alert ──────────────────────────────────
    function showCvAlert(message, type = "info") {
        const existingAlert = document.getElementById("cv-inline-alert");
        if (existingAlert) existingAlert.remove();

        const alert = document.createElement("div");
        alert.id = "cv-inline-alert";
        const color = type === "warning" ? "#f59e0b" : type === "error" ? "#ef4444" : "#60a5fa";
        alert.style.cssText = `
            position:fixed; top:60px; left:50%; transform:translateX(-50%);
            background:#1a1a1a; border:1px solid ${color}; color:${color};
            padding:10px 20px; border-radius:8px; font-size:13px; z-index:9999;
            box-shadow:0 4px 16px rgba(0,0,0,0.4); animation:fadeSlideIn 0.3s ease;
        `;
        alert.textContent = message;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 4000);
    }

});
