# Creative Automation Pipeline – Complete Campaign Automation System

## 🎯 Overview
A complete end‑to‑end creative automation pipeline for global consumer goods campaigns. Generates branded product images, creates multi‑aspect‑ratio creatives, applies legal guardrails, performs compliance checks, produces localized campaign videos with voiceover and background music, and uploads to cloud storage—all within a developer‑friendly, version‑controlled repository.

**Core Value Proposition:** Automate entire campaign production while enforcing brand compliance, legal safety, multi‑region localization, and full traceability.

---

## 🚀 Quick Start

### Clean Install (Recommended)
```bash
# 1. Clone repository
cd ~/projects
git clone https://github.com/openclaw-macos/creative-automation-pipeline
cd creative-automation-pipeline

# 2. Install dependencies
./src/install_deps.sh

# 3. Configure assets (update paths in configs/brand_config.json)
# Edit logo_path and background_music paths to point to your assets

# 4. Test complete campaign workflow
./run_campaign_demo.sh --brief configs/brief.json
```

### Requirements

**Core Dependencies:**
- **Python 3.8+** with virtual environment support – install via [python.org](https://www.python.org/downloads/) or your system package manager.
- **ComfyUI** server running on `http://127.0.0.1:8188` – follow the [ComfyUI installation guide](https://github.com/comfyanonymous/ComfyUI) to set up locally. You'll need at least one Stable Diffusion checkpoint (e.g., SD1.5, SDXL) placed in `ComfyUI/models/checkpoints/`.
- **FFmpeg** installed (for video processing) – on macOS: `brew install ffmpeg`; on Ubuntu/Debian: `sudo apt install ffmpeg`.
- **Voicebox TTS** (optional) – a local TTS server for voiceover generation. The pipeline expects a Voicebox server at `http://127.0.0.1:17493`. **For reliable operation on macOS, disable App Nap:**  
  ```bash
  # Verify bundle identifier
  mdls -name kMDItemCFBundleIdentifier /Applications/Voicebox.app
  
  # Disable App Nap
  defaults write sh.voicebox.app NSAppSleepDisabled -bool YES
  
  # Restart Voicebox.app
  ```
  Check Activity Monitor → Energy tab → ensure "App Nap" column says "No" for Voicebox.

- **Edge TTS** (optional fallback) – a Python package that uses Microsoft Edge's neural TTS voices. If Voicebox is unavailable, the pipeline will automatically try Edge TTS. **Installation:**
  ```bash
  pip install edge-tts
  ```
  The pipeline includes built‑in support for Edge TTS with language‑specific neural voices:
  - English (en): `en-US-AriaNeural`
  - German (de): `de-DE-KatjaNeural`
  - Japanese (ja): `ja-JP-NanamiNeural`
  - Arabic (ar): `ar-SA-HamedNeural`
  - Portuguese (pt): `pt-BR-FranciscaNeural`
  - Swedish (sv): `sv-SE-SofieNeural`
  
  Edge TTS requires an internet connection and uses Microsoft's cloud TTS service via the Edge browser API. Voice quality is high but latency depends on network speed.

**Optional Cloud Services:**
- **Google Drive API** credentials (optional, for cloud storage) – create a service account and download the JSON key. Place it at `~/google_serviceaccount/service_account.json` or update the path in `src/comfyui_generate.py`.
- **HeyGen API key** (optional, for avatar videos) – sign up at [HeyGen](https://www.heygen.com/) and obtain an API key.

**Storage Requirements**
- **Python virtual environment & packages:** ~500 MB.
- **ComfyUI installation (without models):** ~2 GB.
- **Stable Diffusion checkpoints:** 4–10 GB depending on model selection (SD1.5 ~4 GB, SDXL ~6 GB, additional LoRAs/VAEs extra).
- **FFmpeg:** ~100 MB.
- **Voicebox TTS models (if used):** Small/Fast Models: ~1.5 GB to 3 GB (Good for quick testing); High-Fidelity/Pro Models (XTTSv2/Voicebox-style): 6 GB to 15 GB. This is what you need for realistic brand voiceovers.
- **Total estimated disk space:** 6–30 GB (depending on models and optional components).

**Installation Time (assuming standard US internet speeds)**
- **Python packages:** 5–10 minutes.
- **ComfyUI setup (clone, install, download models):** 30–60 minutes (most time spent downloading models).
- **FFmpeg:** 1–2 minutes.
- **Voicebox TTS setup:** optional, additional 10–60 minutes (depending on model size).
- **Total setup time:** 45–150 minutes for a fully functional pipeline (including optional components).

**Hardware Requirements**
- **Minimum:** 8 GB system RAM, 4 GB VRAM (GPU), 25 GB free disk space
- **Recommended:** 16 GB system RAM, 8 GB VRAM (NVIDIA GPU with CUDA support), 40 GB free disk space
- **GPU:** NVIDIA GPU recommended for ComfyUI acceleration (AMD/Intel iGPUs may work but slower)
- **Operating System:** macOS 10.15+, Ubuntu 20.04+, Windows 10/11 (WSL2 recommended for Windows)

**Network & Port Requirements**
- **Open ports:** 8188 (ComfyUI), 17493 (Voicebox TTS – optional)
- **Internet access required** for initial setup (Python packages, model downloads, translation APIs)
- **Firewall configuration:** Ensure localhost traffic is allowed on the above ports
- **Proxy/ VPN considerations:** If behind corporate firewall, configure proxy settings for Python/curl

**Verification Checklist (Run Before First Use)**
Before running any campaign, verify each component works:

1. **Python environment:**
   ```bash
   python3 --version  # Should show 3.8+
   pip3 list | grep -E "(requests|opencv|Pillow)"  # Core packages installed
   ```

2. **ComfyUI server:**
   ```bash
   curl -s http://127.0.0.1:8188  # Should return HTML
   # Or visit http://127.0.0.1:8188 in browser
   ```

3. **FFmpeg installation:**
   ```bash
   ffmpeg -version  # Should show version info
   ```

4. **Asset files exist:**
   ```bash
   ls -la configs/brand_config.json  # Should exist
   # Check logo and background music paths in the config file
   ```

5. **Voicebox TTS reliability (macOS):**
   ```bash
   # Check if Voicebox is running
   curl -s http://127.0.0.1:17493/health  # Should return {"status":"ok"} or similar
   
   # Verify App Nap is disabled
   defaults read sh.voicebox.app NSAppSleepDisabled  # Should return "1" or "YES"
   
   # Check Activity Monitor → Energy tab → "App Nap" column for Voicebox should say "No"
   ```
   
   **Note:** If Voicebox is unavailable, the pipeline will automatically try Edge TTS (requires `pip install edge-tts`). Edge TTS uses Microsoft's cloud neural voices and requires an internet connection.

6. **Test minimal generation (without compliance):**
   ```bash
   python3 src/comfyui_generate.py --prompt "test" --output test.png --no-compliance-check --no-legal-check --no-report
   ```

**Performance Expectations**
- **Image generation:** 10–30 seconds per image (depends on GPU, model size, steps)
- **Video processing:** 5–20 seconds per minute of video (depends on resolution, effects)
- **Localization translation:** 1–5 seconds per phrase (depends on API latency)
- **Google Drive upload:** Varies with file size and network speed

**File Permissions Guide**
- **macOS/Linux:** Ensure you have read/write permissions to the project directory:
  ```bash
  chmod -R 755 creative-automation-pipeline
  ```
- **Avoid sudo** for Python package installation (use virtual environment)
- **Asset files** (logo.png, background_music.mp3) should be readable by the Python process

**Update Instructions**
To update the pipeline to the latest version:
```bash
cd creative-automation-pipeline
git pull origin main
./src/install_deps.sh  # Updates Python packages
# Check config migration notes if any breaking changes
```

**Important Notes:**
- The pipeline requires an active internet connection for initial dependency downloads and model fetching.
- Ensure your system has sufficient GPU memory for ComfyUI (at least 4 GB VRAM recommended for SD1.5, 8 GB for SDXL).
- All file paths in configuration files must be absolute paths (not relative) to avoid permission errors.
- For a smooth, glitch‑free experience, run the installation steps in order and verify each component works before proceeding.

---

## ✨ Key Features

### 🖼️ **Smart Aspect Ratio Generation**
- **2 products × 3 aspect ratios = 6 creatives** from 2 base AI-generated images
- **Intelligent resizing** (center‑crop, letterbox, stretch) – no duplicate AI generation
- **Standard dimensions:**
  - **1:1** (1080×1080) – Square (Instagram, Facebook)
  - **16:9** (1920×1080) – Widescreen (YouTube, video)
  - **9:16** (1080×1920) – Portrait (Instagram Reels, TikTok)

### 🎬 **Campaign Slideshow Videos**
- **Multi‑product slideshows** – All campaign products in single video
- **Crossfade transitions** – Professional 1‑second transitions between images
- **Background music + voiceover** – Mixed audio (voice: 1.0, music: 0.3 volume)
- **Brand logo overlay** – Transparent logo on all product images (10% opacity)

### 🌍 **Multi‑Region Localization**
- **6 target regions** with automatic language mapping:
  - North America (USA/Canada) → English
  - European Union (Germany/France) → German
  - Japan → Japanese
  - UAE / Saudi Arabia → Arabic
  - Brazil → Portuguese
  - Scandinavia (Sweden/Denmark) → Swedish
- **Free translation APIs** – LibreTranslate, Google Translate, MyMemory Translation
- **Mock translation fallback** – Works offline with pre‑translated phrases

### ☁️ **Google Drive Cloud Storage**
- **Automatic upload** of all generated assets (images, videos, audio, reports)
- **Service account authentication** – Secure API access without user login
- **Organized folder structure** – Maintains local folder hierarchy in cloud
- **Public shareable links** – Automatically generates read‑only links
- **Local copy preserved** – Never deletes original files

### 🤖 **HeyGen Avatar Integration**
- **Campaign‑focused avatar videos** – Single video addressing all products
- **Local‑model script planning** – Uses Ollama models to avoid API costs
- **Voicebox‑compatible voice search** – Prioritizes matching voices
- **Background customization** – Professional studio backgrounds

### 🛡️ **Brand Compliance & Legal Safety**
- **Logo detection** – OpenCV template matching verifies brand presence
- **Color compliance** – Ensures brand colors cover minimum percentage
- **Prohibited‑word scanning** – Case‑insensitive whole‑word matching
- **Region‑specific legal checks** – Configurable by target market

### 📊 **Enhanced Full Auditability & Reporting**
- **Unified SQLite database** – Structured logs for all 5 pipeline stages in `outputs/logs/pipeline_logs.db`
- **Enhanced schema** – Supports `stage` column with values: `image_generation`, `video_generation`, `heygen_generation`, `combination_generation`, `youtube_upload`
- **Complete campaign tracking** – Logs every step from image generation to YouTube upload
- **JSON run reports** – Human‑readable execution logs in `outputs/logs/run_report.json`
- **Generation metadata** – Product, dimensions, compliance status, timing, stage-specific data
- **Query API** – Filter by date, product, region, compliance status, or pipeline stage
- **Performance metrics** – Generation time, file sizes, compliance scores across all stages

### 🔊 **Console Output & Logging**
- **Structured logging** – Unified logger with timestamps, levels, and emoji support
- **Progress indicators** – Step‑by‑step progress tracking with [step/total] format
- **Error handling** – Clear error messages with actionable context
- **Verbose mode** – `--verbose` flag for detailed debugging output
- **Color support** – Terminal colors for better readability (auto‑detected)
- **Log levels** – DEBUG, INFO, WARNING, ERROR, CRITICAL with appropriate emojis

---

## 🧪 Example Campaigns (Ready to Test)

Six ready‑to‑run campaign briefs are included in `configs/examples/` covering major global regions. Each brief works out‑of‑the‑box with automatic region‑to‑language mapping and graceful fallbacks.

| Folder | Target Region | Language (auto‑mapped) | Products |
|--------|---------------|------------------------|----------|
| `1_Smart_Kitchen_Essentials_North_America` | USA | `en` (English) | Smart Coffee Maker, Air Fryer |
| `2_Sustainable_Home_Care_Europe` | European Union (Germany/France) | `de` (German) | Biodegradable All‑Purpose Cleaner, Refillable Glass Spray Bottle |
| `3_Premium_Personal_Care_Japan` | Japan | `ja` (Japanese) | Hydrating Serum, Sonic Facial Cleanser |
| `4_Smart_Fitness_Tech_Middle_East` | UAE / Saudi Arabia | `ar` (Arabic) | Smart Fitness Watch, Noise‑Cancelling Earbuds |
| `5_Nutritious_Baby_Care_Brazil` | Brazil | `pt` (Portuguese) | Organic Fruit Purees, Vitamin‑D Fortified Snacks |
| `6_Urban_Commuter_Gear_Nordics` | Scandinavia (Sweden/Denmark) | `sv` (Swedish) | Weatherproof Commuter Backpack, Insulated Travel Mug |

**Usage:**
```bash
# Test any example campaign
./run_campaign_demo.sh --brief configs/examples/3_Premium_Personal_Care_Japan/brief.json

# Or test localization with all regions
./scripts/tests/test_localization_demo.sh
```

**Note:** Region‑to‑language mapping is hardcoded in `src/localization.py`; `target_language` in brief.json is optional. Missing fields (e.g., `campaign_video_message`) fall back gracefully.

**Campaign Folder Naming Standard:** New campaigns use timestamped folder names: `campaign_{number}_{product_type}_{region}_{timestamp}` using standardized format `YYYYMMDD_HHMM` (no seconds). Example: `campaign_2_Sustainable_Home_Care_Europe_20260324_1439`. Example campaigns above use legacy numbering for compatibility.

---

## 📁 Repository Structure

```
creative-automation-pipeline/
├── README.md                    # This documentation
├── requirements.txt             # Python dependencies
├── run_campaign_demo.sh         # Master orchestrator (runs all 5 steps sequentially)
├── configs/
│   ├── brand_config.json       # Brand colors, logo path, music path
│   ├── brief.json              # Campaign template (products, region, audience)
│   ├── assets.json            # Asset path configuration
│   ├── examples/               # 6 ready‑to‑run campaign briefs (see above)
│   ├── default_workflow.json   # ComfyUI workflow template
│   └── sdxl_workflow.json     # SDXL workflow for high‑quality images
├── src/
│   ├── comfyui_generate.py    # Main generation script
│   ├── video_pipeline.py      # Video/slideshow creation
│   ├── aspect_ratio.py        # Aspect ratio resizing
│   ├── localization.py        # Translation services
│   ├── google_drive_integration.py
│   ├── heygen_integration.py
│   ├── campaign_manager.py    # Campaign folder organization
│   ├── timestamp_utils.py     # Timestamp utilities for campaigns and reports
│   ├── test_report_generator.py # Test report generation
│   ├── brand_compliance.py    # Brand compliance checks
│   ├── legal_guardrail.py     # Legal word scanning
│   └── reporting.py           # Audit logging
├── scripts/
│   ├── campaigns/
│   │   ├── run_images_demo.sh         # Image generation + compliance + legal + reporting
│   │   ├── run_video_demo.sh          # Creates video from images (calls images demo if needed)
│   │   ├── run_heygen_demo.sh         # Consolidated HeyGen avatar generation from brief
│   │   ├── run_heygen_products_demo.sh # Combined avatar + products video
│   │   └── run_youtube_heygen_products_demo.sh # YouTube upload (calls step 4 if video missing)
│   ├── tests/
│   │   ├── test_*.sh                   # Individual test scripts
│   │   └── run_tests_with_reports.sh   # Test runner with timestamped reports
│   ├── timestamp_utils.sh          # Bash timestamp utilities (YYYYMMDD_HHMM format)
│   ├── test_campaign_template.sh   # Campaign testing template with timestamped reports
│   ├── organize_outputs.sh         # Output organization utility (mandatory)
│   └── utils/
│       └── fix_permissions.sh      # Utility script
└── docs/
    ├── demo_script.md         # 3‑minute video script (proof‑of‑concept demo)
    ├── video_walkthrough_script.md # 4‑5 minute technical walk‑through
    └── BRAND_GUIDELINES.md    # Brand compliance guidelines
```

---

## 🛠️ Script Reference

**Note:** For single‑command execution of the complete 5‑step pipeline, use the master orchestrator:  
`./run_campaign_demo.sh --brief configs/brief.json`  
The individual scripts below are useful for debugging or specific workflow steps.

### **(Step 1) run_images_demo.sh** – Image Generation Pipeline
```bash
# Image generation + compliance + legal + reporting
./scripts/campaigns/run_images_demo.sh [--brief FILE]
```
**What it does:**
1. Generates product image via ComfyUI
2. Runs brand compliance checks (logo, colors)
3. Scans campaign message for prohibited words
4. Logs generation to SQLite database

### **(Step 2) run_video_demo.sh** – Video Pipeline
```bash
# Creates video from images (calls run_images_demo.sh if images not present)
./scripts/campaigns/run_video_demo.sh [--brief FILE] [--upload-to-drive] [--drive-service-account PATH] [--drive-folder-id ID]
```
**What it does (automatically detects single vs multi-product from brief.json):**

**Single Product Mode** (when brief.json has 1 product):
1. Checks for existing product image (calls `run_images_demo.sh` if not present)
2. Adds text overlay with campaign message from brief.json
3. Adds brand logo overlay (transparent, top‑right)
4. Generates voiceover via Voicebox TTS
5. Creates MP4 video with background music mixing
6. Output: `outputs/video/Product_Name_video.mp4`

**Multi-Product Campaign Mode** (when brief.json has 2+ products):
1. Reads `brief.json` (products, target_region, audience, campaign_video_message)
2. Generates base images for all products
3. Creates 3 aspect ratios for each product (1:1, 16:9, 9:16)
4. Adds brand logo overlay to all images
5. Adds text overlay with campaign message
6. Generates voiceover from `campaign_video_message`
7. Creates slideshow video with all product images
8. Mixes voiceover with background music
9. (Optional) Uploads all assets to Google Drive (`--upload-to-drive`)
10. Output: Organized campaign folder at `outputs/campaign/` with slideshow video
11. Uses standardized timestamp format: `YYYYMMDD_HHMM` (no seconds)

### **(Step 3) run_heygen_demo.sh** – Consolidated Avatar Videos
```bash
# Generate HeyGen avatar video from campaign brief (reads from brief.json)
./scripts/campaigns/run_heygen_demo.sh [--brief FILE] [--api-key KEY] [--use-real-translation] [--local-model MODEL] [--verbose]
```
**Features:**
- Reads `brief.json` with optional `avatar_script` field
- Uses `regions-language.json` for language mapping
- Uses digital twin: Agent 42 from isFutureNOW
- Uses voice: RaviK Pullet (or auto-detected)
- Generates avatar script from products using AI if not provided
- Supports real or mock translation for localization

### **(Step 4) run_heygen_products_demo.sh** – Combined Avatar + Products Video
```bash
# Generate combined video: avatar sales pitch + products showcase
./scripts/campaigns/run_heygen_products_demo.sh [--brief FILE] [--avatar-video FILE] [--products-video FILE] [--output-dir DIR] [--regenerate-avatar] [--regenerate-products] [--keep-intermediates] [--verbose]
```
**Workflow:**
1. Generates HeyGen avatar video (or uses existing)
2. Generates products video via `run_video_demo.sh` (or uses existing)
3. Concatenates both videos using `ffmpeg`
4. Outputs final combined video for campaign

### **(Step 5) run_youtube_heygen_products_demo.sh** – YouTube Upload
```bash
# Upload HeyGen avatar products video to YouTube as draft
./scripts/campaigns/run_youtube_heygen_products_demo.sh [--brief FILE] [--secrets FILE] [--regenerate-video] [--simulate] [--verbose] [--keep-thumbnail]
```
**Workflow:**
1. Checks for combined video (calls `run_heygen_products_demo.sh` if not present)
2. Generates catchy YouTube title using AI (or uses `youtube_title` from brief)
3. Creates YouTube thumbnail using AI (or uses `youtube_thumbnail` from brief)
4. Uploads video to YouTube as private (draft) using OAuth 2.0
5. Saves upload result with video ID and status

**Required:**
- OAuth `client_secrets.json` from Google Cloud Console
- YouTube Data API v3 enabled in Google Cloud project
- User authorization via browser (first time only)

**Optional flags:**
- `--simulate` - Test without actual YouTube upload
- `--regenerate-video` - Force regenerate video before upload
- `--verbose` - Detailed output

### **Campaign Workflow Sequence**
The five campaign scripts work in sequence, each using output from the previous step:

**Sequence:**
1. **(Step 1) `run_images_demo.sh`** → Generates product images from `brief.json` (logs to `image_generation` stage)
2. **(Step 2) `run_video_demo.sh`** → Creates products video from images (automatically handles single or multi-product; calls step 1 if images missing; logs to `video_generation` stage)
3. **(Step 3) `run_heygen_demo.sh`** → Generates avatar sales pitch video from `brief.json` (logs to `heygen_generation` stage)
4. **(Step 4) `run_heygen_products_demo.sh`** → Concatenates avatar + products videos into final campaign video (logs to `combination_generation` stage)
5. **(Step 5) `run_youtube_heygen_products_demo.sh`** → Uploads video to YouTube as draft (calls step 4 if video missing; logs to `youtube_upload` stage)

**Logging:** Each stage automatically logs to the unified SQLite database (`outputs/logs/pipeline_logs.db`) with stage-specific metadata for complete campaign auditability.

### **Master Orchestrator: `run_campaign_demo.sh`**
For single-command execution of the entire 5-step sequence, use the master orchestrator:
```bash
# Run complete campaign with unified error handling and progress tracking
./run_campaign_demo.sh --brief configs/brief.json [OPTIONS]
```
**Features:**
- Runs all 5 steps sequentially with automatic error handling (stops on failure)
- Unified progress tracking with color-coded output (adapts to terminal capabilities)
- Supports simulation mode (no real API calls, faster testing)
- Configurable via comprehensive command-line flags
- Maintains full logging to `pipeline_logs.db` for each stage
- Safe command construction (handles paths with spaces/special characters)

**Complete Flag Reference:**
| Flag | Description | Default |
|------|-------------|---------|
| `--brief FILE` | **Required.** Path to campaign brief.json | *(none)* |
| `--verbose` | Enable verbose output (shows all subcommand output) | `false` |
| `--simulate` | Simulation mode (no real API calls, skip compliance checks) | `false` |
| `--upload-to-drive` | Upload outputs to Google Drive (ignored in simulation) | `false` |
| `--drive-service-account PATH` | Google service account JSON path | `""` |
| `--drive-folder-id ID` | Google Drive folder ID | `""` |
| `--heygen-api-key KEY` | HeyGen API key (required for real avatar generation) | `""` |
| `--client-secrets PATH` | OAuth client_secrets.json for YouTube upload | `""` |
| `--keep-intermediates` | Keep intermediate video files (don't clean up) | `false` |
| `--help` | Show usage information | N/A |

**Simulation Mode Behavior:**
- **Step 1 (Images):** Runs normally (ComfyUI is local, no external APIs)
- **Step 2 (Video):** Skips Google Drive upload (even if `--upload-to-drive` specified)
- **Step 3 (Avatar):** Uses mock/offline translation (default, no API key needed)
- **Step 5 (YouTube):** Uses `--simulate` flag (no real upload)

**Example full campaign execution:**

**Option A: Master Orchestrator (Recommended)**
```bash
# Single command runs all 5 steps with unified error handling and progress tracking
./run_campaign_demo.sh --brief configs/brief.json --verbose
```
*With Google Drive upload:* `./run_campaign_demo.sh --brief configs/brief.json --upload-to-drive`
*Simulation mode (no real APIs):* `./run_campaign_demo.sh --brief configs/brief.json --simulate --verbose`

**Option B: Individual Steps (For Debugging)**
```bash
# Step 1: Generate product images
./scripts/campaigns/run_images_demo.sh --brief configs/brief.json

# Step 2: Create products video (will use existing images, auto-detects single/multi-product)
./scripts/campaigns/run_video_demo.sh --brief configs/brief.json

# Step 3: Generate avatar video
./scripts/campaigns/run_heygen_demo.sh --brief configs/brief.json

# Step 4: Combine both videos
./scripts/campaigns/run_heygen_products_demo.sh --brief configs/brief.json

# Step 5: Upload to YouTube as draft
./scripts/campaigns/run_youtube_heygen_products_demo.sh --brief configs/brief.json --secrets /path/to/client_secrets.json
```

### **test_localization_demo.sh** – Localization Testing
```bash
# Test all 6 region localizations (now in tests folder)
./scripts/tests/test_localization_demo.sh
```

### **Utility Scripts**

**`scripts/timestamp_utils.sh`** – Standardized timestamp functions
```bash
# Source in scripts for standardized YYYYMMDD_HHMM timestamp format
source scripts/timestamp_utils.sh
TIMESTAMP=$(get_timestamp_no_seconds)  # Returns: 20260325_1437
```
Provides: `get_timestamp_no_seconds`, `get_timestamp_with_seconds`, `get_readable_date`, `get_campaign_folder_name`, `get_test_report_filename`

**`scripts/test_campaign_template.sh`** – Campaign testing template
```bash
# Run a complete campaign test with timestamped outputs and reports
./scripts/test_campaign_template.sh 1_Smart_Kitchen_Essentials_North_America [OPTIONS]
```
**Options:**
- `--quiet` – Quiet mode (minimal output, no verbose)
- `--simulate` – Simulation mode (no real API calls)
- `--upload-to-drive` – Upload outputs to Google Drive
- `--heygen-api-key KEY` – HeyGen API key for avatar generation
- `--client-secrets PATH` – OAuth client_secrets.json for YouTube

**Creates:** Timestamped test outputs in `test_outputs/`, Markdown reports in `test_reports/`, organized campaign folders with standardized naming (`campaign_{name}_{timestamp}`)

**`scripts/organize_outputs.sh`** – Output organization utility (mandatory)
```bash
# Organize outputs, move test files to test_outputs/, backups to backups/
./scripts/organize_outputs.sh
```
Creates: `test_outputs/`, `backups/`, `test_reports/` directories; moves temporary files; optional old campaign cleanup

**`scripts/utils/fix_permissions.sh`** – Permission fixing utility
```bash
# Fix permissions for all scripts in the repository
./scripts/utils/fix_permissions.sh
```

## 📁 Outputs Folder Structure

```
outputs/
├── logs/                    # Pipeline tracking database & reports
│   ├── pipeline_logs.db    # SQLite database with 5-stage pipeline tracking
│   └── run_report.json     # JSON report of latest run
├── images/                  # Generated product images (single product mode)
│   └── product_name.png    # Base product image
├── video/                  # Single product video outputs
│   ├── Product_Name_video.mp4          # Final video
│   ├── Product_Name_text_overlay.png   # Image with text overlay
│   ├── Product_Name_final.png          # Image with logo+text overlay
│   └── Product_Name_voiceover.mp3      # Generated voiceover
└── campaign/               # Multi-product campaign outputs (Step 2 multi-product mode)
    ├── images/
    │   ├── base/          # Original generated images for all products
    │   ├── aspect_ratios/ # 3 aspect ratios per product (1:1, 16:9, 9:16)
    │   ├── with_logo/     # Images with brand logo overlay
    │   └── with_logo_and_textoverlay/ # Final images for video
    ├── audio/
    │   └── campaign_voiceover.mp3  # Campaign narration
    └── video/
        └── campaign_slideshow.mp4  # Slideshow video with all products
```

**Notes:**
- **Single product mode** (brief.json has 1 product): Outputs go to `outputs/video/`
- **Multi-product campaign mode** (brief.json has 2+ products): Outputs go to organized `outputs/campaign/` folder
- All pipeline stages log to `outputs/logs/pipeline_logs.db` for complete auditability
- Example brief.json files in `configs/examples/` demonstrate both single and multi-product configurations

---

## 🔧 Configuration

### **brand_config.json**
```json
{
  "brand_name": "NexaGoods",
  "tagline": "Premium Essentials for Modern Living",
  "logo_path": "/absolute/path/to/your/logo.png",
  "video_settings": {
    "background_music": "/absolute/path/to/your/background_music.mp3"
  }
}
```

### **regions-language.json** – Region Mapping
```json
{
  "region_language_mapping": {
    "USA": "en",
    "European Union (Germany/France)": "de",
    "Japan": "ja",
    "UAE / Saudi Arabia": "ar",
    "Brazil": "pt",
    "Scandinavia (Sweden/Denmark)": "sv"
  },
  "language_voice_mapping": {
    "en": "en-US",
    "de": "de-DE",
    "ja": "ja-JP",
    "ar": "ar-SA",
    "pt": "pt-BR",
    "sv": "sv-SE"
  }
}
```
*Used by `run_video_demo.sh` and `run_heygen_demo.sh` for language localization.*

### **brief.json** – Campaign Template
```json
{
  "product_type": "Smart Kitchen Essentials",
  "products": [
    {"name": "Coffee Maker", "description": "Smart pour‑over coffee maker"},
    {"name": "Blender", "description": "High‑speed professional blender"}
  ],
  "target_region": "North America (USA/Canada)",
  "audience": "Urban professionals aged 25‑45",
  "campaign_message": "Start your day smarter with our kitchen essentials",
  "campaign_video_message": "Introducing our premium kitchen essentials...",
  "avatar_script": "Welcome to NexaGoods, your source for premium kitchen essentials...", // Optional: Custom script for HeyGen avatar
  "target_language": "en", // Optional: Override region-based language mapping
  "youtube_title": "Amazing Smart Kitchen Essentials - Must See Review!", // Optional: YouTube video title
  "youtube_thumbnail": "/path/to/custom/thumbnail.jpg" // Optional: Custom YouTube thumbnail (deprecated: youtube_thumbnail_image also supported)
}
```

### **assets.json** – Asset Configuration
```json
{
  "nexagoods_logo": "/absolute/path/to/your/logo.png",
  "background_music": "/absolute/path/to/your/background_music.mp3",
  "asset_root": "/absolute/path/to/your/assets/folder"
}
```

---

## 📈 Output Structure

### **Campaign Outputs**
```
outputs/campaign/
├── images/
│   ├── base/                     # 2 base AI-generated images
│   ├── aspect_ratios/            # 6 resized images (2 × 3)
│   ├── with_logo/                # All 6 images with brand logo
│   └── with_logo_and_textoverlay/ # All 6 images with logo + campaign text
├── video/
│   └── campaign_slideshow.mp4    # Slideshow with both products
├── audio/
│   └── campaign_voiceover.mp3    # Voiceover mixed with background music
└── campaign_metadata.json        # Generation logs and compliance reports
```

### **Individual Product Outputs**
```
outputs/
├── Coffee_Maker_512x512.png
├── Coffee_Maker_text_overlay.png
├── Coffee_Maker_final.png
├── Coffee_Maker_voiceover.mp3
├── Coffee_Maker_video.mp4
└── logs/
    ├── pipeline_logs.db
    └── run_report.json
```

---

## 🧪 Testing Suite

### **Complete Verification (With Reports)**
```bash
# Run all tests with timestamped .md reports
./scripts/tests/run_tests_with_reports.sh --all

# Run specific test with report
./scripts/tests/run_tests_with_reports.sh --test test_campaign_fix

# List available tests
./scripts/tests/run_tests_with_reports.sh --list
```

### **Individual Test Scripts**
```bash
# Test all features
./scripts/tests/test_campaign_fix.sh

# Test localization
./scripts/tests/test_localization_complete.sh

# Test Google Drive integration
./scripts/tests/test_google_drive.sh

# Test translation updates
./scripts/tests/test_translation_update.sh
```

### **Expected Test Results**
- ✅ 2 base product images generated
- ✅ 6 aspect ratio images created (resizing, not regenerating)
- ✅ Brand logo overlay on all images (10% opacity, top‑right)
- ✅ Campaign text overlay on all images (with campaign message)
- ✅ Campaign slideshow video with crossfade transitions
- ✅ Voiceover mixed with background music
- ✅ Localization for 6 target regions
- ✅ Google Drive upload (if configured)
- ✅ HeyGen avatar video addressing all products

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Missing Assets (logo.png, background_music.mp3)**
**Solution:** Update paths in `configs/brand_config.json`:
```json
"logo_path": "/absolute/path/to/your/logo.png",
"background_music": "/absolute/path/to/your/background_music.mp3"
```

#### **2. ComfyUI Connection Failed**
**Solution:** Ensure ComfyUI server is running:
```bash
cd /path/to/ComfyUI
python main.py --port 8188
```

#### **3. FFmpeg Not Found**
**Solution:** Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

#### **4. Python Module Errors**
**Solution:** Reinstall dependencies:
```bash
./src/install_deps.sh
```

#### **5. Google Drive Authentication Failed**
**Solution:** Verify service account JSON file exists and has Drive API permissions:
```bash
ls -la ~/path/to/google_serviceaccount/
# Update the path in src/comfyui_generate.py if different
```

#### **6. HeyGen API Key Invalid**
**Solution:** Update API key in script or environment variable:
```bash
export HEYGEN_API_KEY="sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### **Debug Mode**
```bash
# Enable verbose output (using test script)
./scripts/tests/test_campaign_demo.sh --brief configs/brief.json --verbose

# Test individual components
python3 src/aspect_ratio.py --help
python3 src/video_pipeline.py --help
```

---

## 🔄 Development & Extension

### **Adding New Features**
1. **New aspect ratio:** Update `src/aspect_ratio.py` → `ASPECT_RATIOS` dictionary
2. **New region:** Update `src/localization.py` → `REGION_LANGUAGE_MAP`
3. **New compliance check:** Add method to `src/brand_compliance.py`
4. **New video effect:** Extend `src/video_pipeline.py` → `_get_video_filter()`

### **Production Considerations**
- **Replace OpenCV with Vision‑LLM** for better logo detection
- **Add CDN integration** for asset delivery
- **Implement queue system** for high‑volume generation
- **Add monitoring dashboard** with real‑time metrics
- **Integrate with marketing platforms** (Facebook Ads, Google Ads API)

### **Performance Optimization**
- **Parallel generation** for multiple products
- **Cache translated phrases** to reduce API calls
- **Batch uploads** to Google Drive
- **Preview generation** with lower resolution

---

## 📄 License & Attribution

- **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **OpenCV:** [https://opencv.org/](https://opencv.org/)
- **Voicebox:** [https://github.com/facebookresearch/voicebox](https://github.com/facebookresearch/voicebox)
- **FFmpeg:** [https://ffmpeg.org/](https://ffmpeg.org/)

Built for internal demonstration and production‑ready campaign automation.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### **Code Standards**
- Follow PEP 8 for Python code
- Add docstrings to all public methods
- Include unit tests for new features
- Update documentation (README.md) accordingly

---

**Last Updated:** March 26, 2026 (Enhanced logging system with 5-stage tracking)  
**Version:** 2.3 – Enhanced logging system with 5-stage campaign tracking