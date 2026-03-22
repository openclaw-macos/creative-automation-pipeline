# Creative Automation Pipeline – Proof of Concept

## Overview
This proof‑of‑concept (POC) demonstrates an end‑to‑end creative automation pipeline for a global consumer goods company. The pipeline generates branded product images, applies legal guardrails, performs compliance checks, and logs every asset for auditability. It is built on top of existing local tools (ComfyUI for image generation, Voicebox for TTS) and is designed to be extended to a production‑grade system.

**Core Value Proposition:** Automate social ad creatives while enforcing brand compliance, legal safety, and full traceability—all within a developer‑friendly, version‑controlled repository.

---

## Architecture Decisions (Architect‑Level)

### 1. **Modular, Extensible Design**
   - **Separation of Concerns:** Image generation, compliance, legal checks, and reporting are isolated into independent Python modules (`brand_compliance.py`, `legal_guardrail.py`, `reporting.py`). This allows teams to update or replace individual components without breaking the entire pipeline.
   - **Plugin‑Ready:** Each module exposes a simple API (class‑based) that can be called from any orchestrator (OpenClaw, Airflow, Prefect, or a simple script).

### 2. **Brand Compliance via Computer Vision (Not Just Manual Review)**
   - **Why OpenCV?** Chosen over a full Vision‑LLM for speed, cost, and determinism. Template matching for logo detection and RGB distance for brand‑color verification are sufficient for a POC and can be swapped for a more sophisticated model (e.g., CLIP, GroundingDINO) in production.
   - **Config‑Driven:** Brand colors, logo path, tolerance thresholds are stored in `configs/brand_config.json`. This allows non‑developers (brand managers) to adjust parameters without touching code.
   - **Graceful Degradation:** If OpenCV is not installed, compliance checks return a clear warning but do not halt the pipeline—allowing the POC to run in “audit‑only” mode.

### 3. **Legal Guardrails as a Pre‑Flight Check**
   - **Prohibited‑Word List:** A configurable list of banned terms (e.g., “cheap”, “free”, “winner”) is scanned in campaign messages before they are sent to image‑overlay or TTS.
   - **Structural Awareness:** The guardrail recursively traverses JSON/YAML campaign structures, checking every string field. This prevents legal pitfalls from nested creative briefs.
   - **Flag‑and‑Continue:** When a prohibited word is found, the pipeline logs the violation and can either halt or continue with a flagged version (configurable). This aligns with a “fail‑safe but not fail‑stop” philosophy.

### 4. **Reporting Built for Auditability & Analytics**
   - **Dual Logging:** Every generation is recorded both in a SQLite database (for structured queries) and a JSON log file (for human readability and backup).
   - **Rich Metadata:** Each log entry includes product name, dimensions, compliance status, generation time, checks passed/failed, and the raw campaign message. This enables:
     - **Compliance Dashboards:** “What percentage of last week’s assets passed brand‑color checks?”
     - **Performance Analytics:** “Which product lines have the longest generation times?”
     - **Legal Audits:** “Show me all creatives that contained the word ‘guarantee’.”
   - **SQLite Choice:** Lightweight, serverless, and compatible with DB Browser for SQLite—allowing marketing teams to explore logs without SQL knowledge.

### 5. **Repository Structure Optimized for Collaboration**
   ```
   skills/comfyui/
   ├── configs/           # Brand configs, workflow JSONs, prohibited‑word lists
   ├── src/               # Python source code (generation, compliance, legal, reporting)
   ├── outputs/           # Generated images, logs, and run reports (git‑ignored)
   ├── docs/              # This README, architecture diagrams, setup guides
   └── requirements.txt   # Explicit dependency list for reproducible environments
   ```
   - **Clear Separation:** Configs are separate from code, outputs are isolated, documentation lives alongside the implementation.
   - **Git‑Ready:** `outputs/` is added to `.gitignore` to avoid committing generated assets. Only code, configs, and docs are version‑controlled.

### 6. **Demo‑Ready Video Script Included**
   - A 3‑minute video script (`docs/demo_script.md`) is provided, optimized for the user’s Voicebox Digital Twin. It walks through local setup, pipeline execution, and review of the output folder—making it easy to record a polished stakeholder demo without extra prep.

### 7. **512×512 Default – Avoiding Common Pitfalls**
   - The pipeline defaults to **512×512** images (square) to avoid the 1024×1024 and 2048×2048 sizes that the user explicitly prohibited. This is enforced in both the workflow JSON and the Python script’s default arguments.

### 8. **Video Pipeline with Config‑Driven Overlays**
   - **Text & Logo Overlays:** Campaign messages are automatically overlaid as white 48‑pt text (bottom‑center) with fade‑in/out effects, while the brand logo appears at top‑right with 10% opacity—all configurable in `brand_config.json`.
   - **Voicebox TTS Integration:** Narration is generated via a local Voicebox server (`http://127.0.0.1:17493`) with silent‑audio fallback, ensuring video always has an audio track.
   - **FFmpeg Center‑Crop:** Images are intelligently cropped to 16:9 using correct center‑crop mathematics, preserving the most important visual content.
   - **One‑Click Demo:** `run_video_demo.sh` executes the full video pipeline end‑to‑end, from image generation to final MP4.

### 9. **HeyGen Avatar Integration with Local‑Model Planning**
   - **API‑First Avatar Generation:** Uses the HeyGen API to produce professional avatar videos from scripts, with support for avatar/voice selection and background customization.
   - **Local‑Model Cost Avoidance:** All script planning and refinement uses local Ollama models (`mistral‑nemo`, `qwen3‑vl`, `qwen3.5`) to avoid DeepSeek API charges while still leveraging HeyGen’s high‑quality avatar rendering.
   - **Voicebox Voice Preference:** The integration automatically searches for Voicebox‑compatible voices in HeyGen’s voice library, falling back to the best available English voice.
   - **Standalone Demo:** `run_heygen_demo.sh` showcases avatar generation with the provided API key, using local models for script processing as requested.
   - Aspect‑ratio flexibility is retained via command‑line arguments (`--width`, `--height`), but the safe default ensures compliance with the user’s directive.

---

## Module Details

### Brand Compliance (`src/brand_compliance.py`)
- **Logo Detection:** Uses OpenCV template matching to verify the brand logo appears in the generated image.
- **Brand‑Color Verification:** Checks that at least one of the defined brand‑color hex values covers >5% of the image pixels (within a configurable tolerance).
- **Output:** JSON with pass/fail per check, match scores, and color percentages.

### Legal Guardrail (`src/legal_guardrail.py`)
- **Prohibited‑Word Scanning:** Case‑insensitive whole‑word matching against a configurable list.
- **Structure‑Aware:** Handles plain text, JSON, and YAML campaign messages.
- **Flagging:** Returns a version of the text with prohibited words wrapped in `[PROHIBITED: …]` markers.

### Reporting (`src/reporting.py`)
- **SQLite Database:** Table `generation_logs` with columns for all relevant metadata.
- **JSON Log:** Human‑readable `run_report.json` appended with each generation.
- **Query API:** Methods to filter logs by product, date, compliance status.
- **Statistics:** Summary of total generations, pass rates, average generation time.

### Extended Generation Script (`src/comfyui_generate.py`)
- **Backward Compatible:** All original command‑line arguments still work.
- **New Flags:**
  - `--compliance-check` – run brand compliance after generation.
  - `--legal-check` – scan the prompt/campaign message for prohibited words.
  - `--brand-config` – path to brand configuration JSON.
  - `--no-report` – skip database/JSON logging.
  - `--product` – product name for reporting.
  - `--campaign-message` – separate campaign text for legal checks.
  - `--video` – generate video with text/logo overlays and voiceover.
  - `--video-output-dir` – directory for video outputs.
  - `--voicebox-url` – Voicebox TTS server URL.
- **Integrated Logging:** Automatically logs every generation when reporting is enabled.

### Video Pipeline (`src/video_pipeline.py`)
- **Text Overlays:** Adds campaign message as white 48‑pt text with semi‑transparent background at bottom‑center position, with configurable fade‑in/out effects.
- **Logo Overlays:** Places brand logo at top‑right corner with 10% opacity (configurable), automatically resized to 15% of image width.
- **Voicebox TTS Integration:** Generates voiceover using local Voicebox server with silent‑audio fallback.
- **FFmpeg Video Assembly:** Creates 16:9 MP4 videos with proper center‑cropping and fade transitions.
- **Config‑Driven:** All settings (font size, color, position, opacity) read from `brand_config.json`.

### HeyGen Integration (`src/heygen_integration.py`)
- **Avatar Video Generation:** Uses HeyGen API to create professional avatar videos from scripts.
- **Local‑Model Planning:** Script refinement and planning uses local Ollama models (`mistral‑nemo`, `qwen3‑vl`, `qwen3.5`) to avoid cloud API charges.
- **Voicebox Voice Preference:** Automatically searches for Voicebox‑compatible voices in HeyGen’s voice library.
- **API Key Configuration:** Requires HeyGen API key (provided in demo script).
- **Polling & Download:** Monitors video generation status and downloads completed videos automatically.

---

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   cd skills/comfyui
   ./src/install_deps.sh
   ```

2. **Configure Brand Settings:**
   - Edit `configs/brand_config.json` with your logo path, brand colors, and prohibited words.
   - Place your logo image in `assets/logo.png` (or update the `logo_path`).

3. **Start ComfyUI Server:**
   ```bash
   cd /path/to/ComfyUI
   python main.py --port 8188
   ```

4. **Run Demo Scripts:**
   - **Basic pipeline (image + compliance + legal + reporting):**
     ```bash
     ./run_demo.sh
     ```
   - **Video pipeline (adds text/logo overlays + voiceover + MP4):**
     ```bash
     ./run_video_demo.sh
     ```
   - **HeyGen avatar pipeline (requires API key, uses local models):**
     ```bash
     ./run_heygen_demo.sh
     ```

5. **Inspect Logs:**
   - Open `outputs/pipeline_logs.db` with DB Browser for SQLite.
   - View `outputs/run_report.json` for a human‑readable log.

---

## Demo Video Script (3‑Minute Voiceover)

A complete script is available in `docs/demo_script.md`. It guides the viewer through:
- **Introduction** (30s): The problem of manual creative production and the need for automation.
- **Local Setup** (60s): Starting ComfyUI, installing dependencies, configuring brand settings.
- **Pipeline Execution** (60s): Running the extended generation script with compliance checks.
- **Reviewing Outputs** (30s): Showing the generated image, compliance report, and SQLite logs.

The script is written in a conversational, presenter‑friendly tone optimized for the user’s Voicebox Digital Twin.

---

## Next Steps for Production

1. **Replace OpenCV with Vision‑LLM:** Swap template matching for a fine‑tuned CLIP or GroundingDINO model to detect logo variations and brand elements more robustly.
2. **Add Localization Guardrails:** Extend the legal module to check for region‑specific regulations (e.g., FDA disclaimers for the US, GDPR wording for the EU).
3. **Integrate with CI/CD:** Automate the pipeline on every Git push—generate previews, run compliance checks, and block merges if any asset fails.
4. **Cloud Storage:** Replace local `outputs/` with S3/GCS buckets, and log metadata to a cloud‑based data warehouse (BigQuery, Snowflake).
5. **Dashboard:** Build a Streamlit or Retool dashboard that visualizes compliance rates, generation times, and asset libraries.

---

## License & Attribution
- **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **OpenCV:** [https://opencv.org/](https://opencv.org/)
- **Voicebox:** [https://github.com/facebookresearch/voicebox](https://github.com/facebookresearch/voicebox)

This POC is built for internal demonstration purposes. Extend and customize as needed for your organization.