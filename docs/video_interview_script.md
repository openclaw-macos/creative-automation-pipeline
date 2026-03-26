# Video Interview Script – Creative Automation Pipeline
**Length:** 3 minutes  
**Audience:** Technical interviewer / hiring manager  
**Goal:** Demonstrate deep understanding of the project, its architecture, and how to set it up.  
**Visuals:** Screen‑share GitHub repository, navigate files, run terminal commands.

---

## (0:00 – 0:30) INTRODUCTION

> **[Visual: Open browser to GitHub repo – https://github.com/openclaw-macos/creative-automation-pipeline]**

**Speaker:**  
“Hi, I’m [Your Name]. Today I’d like to walk you through a production‑ready creative automation pipeline I built for global consumer‑goods campaigns. This system takes a simple campaign brief and automatically generates branded product images, creates multi‑aspect‑ratio creatives, applies legal guardrails, localizes content for six target regions, produces a full video slideshow with voiceover and background music, and uploads everything to Google Drive—all with full auditability.

“Let me show you the repository structure and explain how it works.”

---

## (0:30 – 1:00) REPOSITORY OVERVIEW

> **[Visual: Expand the repo file tree in GitHub]**

**Speaker:**  
“The project follows a clean, modular layout. At the top level we have:

- **`configs/`** – where brand managers set colors, logos, music, and campaign briefs.
- **`src/`** – the Python engine that drives the automation.
- **`scripts/`** – ready‑to‑run demo scripts for different workflows.
- **`docs/`** – detailed documentation, including this video script.
- **`outputs/`** – where all generated assets are saved.

“Everything is version‑controlled and designed for easy collaboration between marketing and engineering teams.”

---

## (1:00 – 1:45) KEY FILES & THEIR FUNCTIONS

> **[Visual: Open `configs/brand_config.json`]**

**Speaker:**  
“First, `brand_config.json` defines the brand identity—logo path, brand colors, background music. This file lets non‑technical users update branding without touching code.

> **[Visual: Open `configs/brief.json`]**

“`brief.json` is the campaign template. It lists products, target region, audience, and the campaign message. The pipeline reads this and automatically maps the region to a language—for example, Japan maps to Japanese, Brazil to Portuguese.

> **[Visual: Open `src/campaign_manager.py`]**

“The core orchestration is in `src/campaign_manager.py`. It calls all the other modules: image generation, aspect‑ratio resizing, compliance checks, video creation, and cloud upload.

> **[Visual: Scroll through `src/` folder]**

“Other key modules include `comfyui_generate.py` for AI image generation, `localization.py` for translation, `brand_compliance.py` for logo and color checks, `legal_guardrail.py` for prohibited‑word scanning, and `google_drive_integration.py` for cloud storage.

“Each module is independent, tested, and logs its actions to a SQLite database for full traceability.”

---

## (1:45 – 2:30) SETUP INSTRUCTIONS

> **[Visual: Switch to terminal, clone the repo]**

**Speaker:**  
“Setting up the pipeline is straightforward. Let me show you the three‑step process:

1. **Clone the repository** and install dependencies.

```bash
git clone https://github.com/openclaw-macos/creative-automation-pipeline
cd creative-automation-pipeline
./src/install_deps.sh
```

2. **Configure assets** by updating the logo and music paths in `configs/brand_config.json`.

3. **Run a complete campaign** with the built‑in demo script.

```bash
./scripts/campaigns/run_video_demo.sh
```

“That single command triggers the entire workflow: image generation, aspect‑ratio creation, logo overlay, voiceover synthesis, video assembly, and optional Google Drive upload.”

---

## (2:30 – 3:00) EXAMPLE CAMPAIGNS & LOCALIZATION

> **[Visual: Navigate to `configs/examples/`]**

**Speaker:**  
“To make evaluation easy, I’ve included six ready‑to‑run campaign briefs covering all target regions specified in the FDE assignment.

“Each folder contains a `brief.json` with region‑specific products and messaging. The pipeline automatically maps the region to the correct language—no manual translation needed.

“For instance, to test the Japanese campaign, you’d run:

```bash
cp configs/examples/3_Premium_Personal_Care_Japan/brief.json configs/brief.json
./scripts/campaigns/run_video_demo.sh
```

“The system gracefully handles missing fields, uses free translation APIs, and falls back to mock translations if offline.

“This ensures the pipeline works out‑of‑the‑box for any global team.”

---

## (3:00 – 3:15) CLOSING

> **[Visual: Return to GitHub repo, highlight the README]**

**Speaker:**  
“In summary, this pipeline turns a manual, error‑prone creative process into a fully automated, auditable, and brand‑safe workflow. It’s modular, extensible, and ready for production.

“The entire codebase is documented, tested, and available on GitHub. I’d be happy to walk through any part in more detail or discuss how it could be extended for your specific needs.

“Thank you for your time.”

--- 

**Production Notes:**
- Speak clearly and at a moderate pace.
- Pause briefly when switching visuals to let the viewer absorb the screen.
- Emphasize the **automatic region‑to‑language mapping** and **graceful fallbacks** – these are key differentiators.
- Keep the tone confident and enthusiastic, but not rushed.
- If time permits, quickly run one of the example campaigns live to show the pipeline in action (optional).