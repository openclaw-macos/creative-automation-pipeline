# Video Walkthrough Script - Creative Automation Pipeline
**Length:** 4-5 minutes
**Audience:** Developers, marketers, and technical users
**Goal:** Demonstrate the project architecture, thoughtful design choices, and how to set it up for local use.
**Visuals:** Screen-share GitHub repository, navigate files, explain key design decisions, run terminal commands.

---

## (0:00 - 0:45) INTRODUCTION & VALUE PROPOSITION

> **[Visual: Open browser to GitHub repo - https://github.com/openclaw-macos/creative-automation-pipeline]**

**Speaker:**
"Welcome to this walkthrough of the **Creative Automation Pipeline** - a production-ready system for global consumer-goods campaigns.

This system solves a critical business problem: manual creative production is slow, error-prone, and hard to scale across regions. The pipeline **automates the entire workflow** - from a simple campaign brief to branded images, localized videos, and even YouTube uploads - while enforcing **brand compliance, legal safety, and full auditability**.

Let me show you the repository structure and explain the thoughtful design choices that make this both robust and extensible."

---

## (0:45 - 1:30) REPOSITORY STRUCTURE & DESIGN PHILOSOPHY

> **[Visual: Expand the repo file tree in GitHub, highlight key directories]**

**Speaker:**
"The project follows a **clean, modular architecture** that separates concerns clearly:

- **`configs/`** - Configuration-driven design: brand managers update colors, logos, and campaign briefs **without touching code**.
- **`src/`** - The Python engine: each module has a single responsibility (image generation, compliance, localization, etc.).
- **`scripts/campaigns/`** - Ready-to-run workflows: **five sequenced scripts** that mirror a real campaign lifecycle.
- **`docs/`** - Comprehensive documentation, including brand guidelines and this walk-through.
- **`outputs/logs/`** - **Enhanced logging system**: all pipeline stages log to a unified SQLite database for complete auditability.

This separation allows **marketing teams to configure campaigns** while **developers extend the engine** - a key design choice for collaboration."

---

## (1:30 - 2:45) KEY FILES & THOUGHTFUL DESIGN CHOICES

> **[Visual: Open `configs/brand_config.json`]**

**Speaker:**
"**First, configuration-first design.** `brand_config.json` defines brand identity - colors, logo, prohibited words. By externalizing these rules, we enable **non-technical users to manage brand guidelines** while the code remains generic and reusable.

> **[Visual: Open `configs/brief.json`]**

"`brief.json` is the **campaign contract**. It lists products, target region, audience, and messaging. Notice the **automatic region-to-language mapping** - Japan → Japanese, Brazil → Portuguese - handled by `regions-language.json`. This **eliminates manual translation configuration**.

> **[Visual: Open `src/reporting.py`]**

"**Now, auditability.** `reporting.py` implements an **enhanced logging system** that tracks all **five pipeline stages**: image generation, video creation, HeyGen avatar, combined video, and YouTube upload. Each stage logs to `outputs/logs/pipeline_logs.db` with stage-specific metadata - a design choice that provides **complete campaign traceability**.

> **[Visual: Scroll through `src/` folder, highlight key modules]**

"**Modular architecture:** Each component has a single responsibility:
- `comfyui_generate.py` - AI image generation with **compliance checks integrated**
- `brand_compliance.py` - **Logo detection and color validation** using OpenCV
- `legal_guardrail.py` - **Prohibited-word scanning** with configurable rules
- `localization.py` - **Translation services with graceful fallbacks** (real API → mock)
- `video_pipeline.py` - **Video assembly with text/logo overlays and voiceover**
- `heygen_integration.py` - **Avatar video generation** with local-model script planning

**Key design choice:** Each module is **independently testable** and logs its own actions - enabling both unit testing and runtime monitoring."

---

## (2:45 - 3:30) CAMPAIGN WORKFLOW & SEQUENCED EXECUTION

> **[Visual: Navigate to `scripts/campaigns/`, show the five script files]**

**Speaker:**
"The pipeline executes as a **five-step sequenced workflow**, each step building on the previous:

1. **`run_images_demo.sh`** - Generates product images with compliance checks.
2. **`run_video_demo.sh`** - Creates product videos with voiceover and music.
3. **`run_heygen_demo.sh`** - Generates avatar sales pitch using HeyGen API.
4. **`run_heygen_products_demo.sh`** - Combines avatar + product videos.
5. **`run_youtube_heygen_products_demo.sh`** - Uploads final video to YouTube as draft.

**Design rationale:** This **modular sequencing** allows teams to run only needed steps, debug failures, and **re-use intermediate outputs**. Each script accepts the same `brief.json` - ensuring consistency across the campaign."

---

## (3:30 - 4:15) SETUP INSTRUCTIONS

> **[Visual: Switch to terminal, show clean setup]**

**Speaker:**
"Setting up the pipeline is straightforward. Here's the **three-step process**:

**Step 1: Clone and install dependencies**
```bash
git clone https://github.com/openclaw-macos/creative-automation-pipeline
cd creative-automation-pipeline
./src/install_deps.sh
```

**Step 2: Configure assets** - Update `configs/brand_config.json` with your logo and music paths.

**Step 3: Test with a complete campaign**
```bash
# Quick test with Coffee Maker example
./scripts/campaigns/run_images_demo.sh
```

**For a full campaign demonstration:**
```bash
# This runs all five stages with enhanced logging
./scripts/campaigns/run_images_demo.sh
./scripts/campaigns/run_video_demo.sh
./scripts/campaigns/run_heygen_demo.sh --api-key YOUR_KEY
./scripts/campaigns/run_heygen_products_demo.sh
./scripts/campaigns/run_youtube_heygen_products_demo.sh --simulate
```

The **`--simulate` flag** lets you test YouTube upload without API credentials."

---

## (4:15 - 4:45) EXAMPLE CAMPAIGNS & LOCALIZATION SYSTEM

> **[Visual: Navigate to `configs/examples/`, show six regional campaigns]**

**Speaker:**  
"To simplify testing, I've included **six ready‑to‑run campaign briefs** covering major global regions:

1. North America (English)
2. European Union (German)
3. Japan (Japanese)
4. UAE/Saudi Arabia (Arabic)
5. Brazil (Portuguese)
6. Scandinavia (Swedish)

**Localization design:** The system uses `regions-language.json` for **automatic mapping**, supports **multiple translation APIs**, and has **graceful fallbacks** - working offline with mock translations if APIs are unavailable.

**Test any region with one command:**
```bash
./scripts/campaigns/run_images_demo.sh --brief configs/examples/3_Premium_Personal_Care_Japan/brief.json
```

This **out-of-the-box readiness** demonstrates the pipeline's **production viability** for global teams."

---

## (4:45 - 5:15) CLOSING & EXTENSIBILITY

> **[Visual: Return to GitHub repo, highlight README and open issues]**

**Speaker:**
"In summary, this pipeline embodies **thoughtful software design**:

1. **Configuration-first** - Brand managers control rules without code changes.
2. **Modular & testable** - Each component has clear boundaries and responsibilities.
3. **Fully auditable** - Enhanced logging tracks all five pipeline stages.
4. **Graceful degradation** - Works offline, with mock APIs, and handles missing fields.
5. **Extensible** - Easy to add new regions, compliance checks, or cloud services.

The entire codebase is **documented, tested, and ready for production**. I'd be happy to walk through any module in detail or discuss how it could be extended for your specific needs.

Thank you for your time."

---

**Production Notes:**
- Speak clearly and at a moderate pace - this is a technical walk-through, not a sales pitch.
- Pause when switching visuals to let the viewer absorb the screen.
- **Emphasize design choices** - configuration-first, modularity, auditability, graceful fallbacks.
- **Demonstrate understanding** by explaining why you made specific architectural decisions.
- Keep the tone **confident and enthusiastic** about the engineering craftsmanship.
- If time permits, **run one quick command live** (e.g., `./scripts/campaigns/run_images_demo.sh`) to show the pipeline in action.