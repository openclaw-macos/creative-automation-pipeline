# Creative Automation Pipeline – Complete Campaign Automation System

## 🎯 Overview
A complete end‑to‑end creative automation pipeline for global consumer goods campaigns. Generates branded product images, creates multi‑aspect‑ratio creatives, applies legal guardrails, performs compliance checks, produces localized campaign videos with voiceover and background music, and uploads to cloud storage—all within a developer‑friendly, version‑controlled repository.

**Core Value Proposition:** Automate entire campaign production while enforcing brand compliance, legal safety, multi‑region localization, and full traceability.

---

## 🚀 Quick Start

### Clean Install (Recommended)
```bash
# 1. Clone repository
cd ~/A42_Folder
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
- **Python 3.8+** with virtual environment support
- **ComfyUI** server running on `http://127.0.0.1:8188`
- **FFmpeg** installed (for video processing)
- **Google Drive API** credentials (optional, for cloud storage)
- **HeyGen API key** (optional, for avatar videos)

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

### 📊 **Full Auditability & Reporting**
- **SQLite database** – Structured logs for analytics
- **JSON run reports** – Human‑readable execution logs
- **Generation metadata** – Product, dimensions, compliance status, timing
- **Query API** – Filter by date, product, region, compliance status

---

## 📁 Repository Structure

```
creative-automation-pipeline/
├── README.md                    # This documentation
├── requirements.txt             # Python dependencies
├── configs/
│   ├── brand_config.json       # Brand colors, logo path, music path
│   ├── brief.json              # Campaign template (products, region, audience)
│   ├── assets.json            # Asset path configuration
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
│   ├── brand_compliance.py    # Brand compliance checks
│   ├── legal_guardrail.py     # Legal word scanning
│   └── reporting.py           # Audit logging
├── scripts/ (or root)
│   ├── run_demo.sh            # Image + compliance + legal + reporting
│   ├── run_video_demo.sh      # Adds text/logo overlays + voiceover + MP4
│   ├── run_campaign_demo.sh   # Complete campaign workflow
│   ├── run_heygen_demo.sh     # HeyGen avatar generation
│   ├── run_heygen_from_brief.sh # HeyGen from brief.json
│   ├── run_localization_demo.sh # Localization testing
│   └── test_*.sh              # Verification scripts
└── docs/
    ├── demo_script.md         # 3‑minute video script
    └── BRAND_GUIDELINES.md    # Brand compliance guidelines
```

---

## 🛠️ Script Reference

### **run_demo.sh** – Basic Pipeline
```bash
# Image generation + compliance + legal + reporting
./run_demo.sh [--product "Coffee Maker"] [--width 512] [--height 512]
```
**What it does:**
1. Generates product image via ComfyUI
2. Runs brand compliance checks (logo, colors)
3. Scans campaign message for prohibited words
4. Logs generation to SQLite database

### **run_video_demo.sh** – Video Pipeline
```bash
# Adds text/logo overlays + voiceover + MP4 creation
./run_video_demo.sh [--campaign-message "Premium coffee experience"]
```
**What it adds:**
1. Text overlay with campaign message
2. Brand logo overlay (transparent, top‑right)
3. Voiceover generation via Voicebox TTS
4. MP4 video with background music mixing

### **run_campaign_demo.sh** – Complete Campaign
```bash
# Full campaign workflow (recommended)
./run_campaign_demo.sh --brief configs/brief.json [--upload-to-drive]
```
**Complete workflow:**
1. Reads `brief.json` (products, target_region, audience)
2. Generates base images for all products
3. Creates 3 aspect ratios for each product (resizing, not regenerating)
4. Adds brand logo overlay to all images
5. Generates voiceover from `campaign_video_message`
6. Creates slideshow video with all product images
7. Mixes voiceover with background music
8. (Optional) Uploads all assets to Google Drive

### **run_heygen_demo.sh** – Avatar Videos
```bash
# HeyGen avatar generation
./run_heygen_demo.sh --api-key YOUR_KEY --script "Campaign message"
```
**Features:**
- Uses local Ollama models for script planning
- Searches for Voicebox‑compatible voices
- Generates professional avatar video
- Addresses all campaign products in single video

### **run_localization_demo.sh** – Localization Testing
```bash
# Test all 6 region localizations
./run_localization_demo.sh
```

### **run_heygen_from_brief.sh** – HeyGen from Brief
```bash
# Generate HeyGen video from brief.json
./run_heygen_from_brief.sh --brief configs/brief.json
```

---

## 🔧 Configuration

### **brand_config.json**
```json
{
  "brand_name": "NexaGoods",
  "tagline": "Premium Essentials for Modern Living",
  "logo_path": "/Users/youee-mac/A42_Folder/creative-automation-pipeline/assets/nexagoods_logo.png",
  "video_settings": {
    "background_music": "/Users/youee-mac/A42_Folder/creative-automation-pipeline/assets/background_music.mp3"
  }
}
```

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
  "campaign_video_message": "Introducing our premium kitchen essentials..."
}
```

### **assets.json** – Asset Configuration
```json
{
  "nexagoods_logo": "/Users/youee-mac/A42_Folder/creative-automation-pipeline/assets/nexagoods_logo.png",
  "background_music": "/Users/youee-mac/A42_Folder/creative-automation-pipeline/assets/background_music.mp3",
  "asset_root": "/Users/youee-mac/A42_Folder/creative-automation-pipeline/assets"
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
│   └── with_logo/                # All 6 images with brand logo
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
├── pipeline_logs.db
└── run_report.json
```

---

## 🧪 Testing Suite

### **Complete Verification**
```bash
# Test all features
./test_campaign_fix.sh

# Test localization
./test_localization_complete.sh

# Test Google Drive integration
./test_google_drive.sh

# Test translation updates
./test_translation_update.sh
```

### **Expected Test Results**
- ✅ 2 base product images generated
- ✅ 6 aspect ratio images created (resizing, not regenerating)
- ✅ Brand logo overlay on all images (10% opacity, top‑right)
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
ls -la /Users/youee-mac/A42_Folder/google_serviceaccount/
```

#### **6. HeyGen API Key Invalid**
**Solution:** Update API key in script or environment variable:
```bash
export HEYGEN_API_KEY="sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### **Debug Mode**
```bash
# Enable verbose output
./run_campaign_demo.sh --brief configs/brief.json --verbose

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

**Last Updated:** March 2026  
**Version:** 2.0 – Complete Campaign Automation