# Guardian CV — Demo Input Dataset

This directory contains standardized, high-contrast visual inspection pairs created for presenting and demonstrating **Guardian CV** (OpenCV 2026 Competition).

Each scenario contains a **Baseline (Reference)** image and an **Inspection (Current)** image.

---

## Included Demo Scenarios

### 1. Electronics / PCB Inspection (`01_pcb_...`)
- **Baseline**: `01_pcb_reference_baseline.png` (nominal green PCB substrate with microchips, traces, and solder pins)
- **Defective**: `01_pcb_inspection_defective.png`
  - **Defect A**: Broken trace / scratch across signal line
  - **Defect B**: Solder bridge / electrical burn short-circuit
  - **Defect C**: Missing solder joint pad
- **Recommended Mode**: *PCB / Structural Defect*

### 2. Industrial Surface & Metal Finish (`02_metal_surface_...`)
- **Baseline**: `02_metal_surface_baseline.png` (brushed metal plate with rivet holes)
- **Defective**: `02_metal_surface_defective.png`
  - **Defect A**: Structural stress crack / scratch line
  - **Defect B**: Chemical corrosion / oxidation discoloration
- **Recommended Mode**: *Surface / Coating Verification*

### 3. Packaging & Tamper Seal Integrity (`03_package_seal_...`)
- **Baseline**: `03_package_seal_baseline.png` (sealed carton with intact tamper band & barcode)
- **Defective**: `03_package_seal_tampered.png`
  - **Defect A**: Torn / broken security seal
  - **Defect B**: Physical corner dent & breach
- **Recommended Mode**: *Packaging / Seal Verification*

### 4. Nominal / Clean Verification (`04_nominal_clean_...`)
- **Baseline**: `04_nominal_clean_baseline.png`
- **Inspection**: `04_nominal_clean_inspection.png` (identical component with minor ambient illumination gain)
- **Expected Outcome**: `NOMINAL_NO_CHANGE` (demonstrating false-positive rejection)

---

## How to Test in the Web UI

1. Open **Guardian CV** at `http://127.0.0.1:5000`.
2. Under **1 · Inspection Inputs**:
   - Drag & drop or click the **Reference** box to upload the `*_baseline.png` file.
   - Drag & drop or click the **Current** box to upload the `*_defective.png` (or `*_inspection.png`) file.
3. Choose the appropriate Inspection Mode and make sure **Adaptive Follow-up (Agentic)** is enabled.
4. Click **Run Inspection** to watch the real-time agentic trace, difference heatmap, and bounding box extractions.
