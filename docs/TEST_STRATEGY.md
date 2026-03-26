# Creative Automation Pipeline - Test Strategy & Plan

**Version:** 1.0  
**Last Updated:** 2026-03-26  
**Author:** OpenClaw Testing Team  
**Document Status:** Active / Living Document

---

## 📋 Overview

This document provides a comprehensive test strategy for the **Creative Automation Pipeline** – an end‑to‑end automated content generation system. The pipeline includes image generation, video production, avatar synthesis, video combination, and YouTube publishing across multiple localized campaigns.

### **Objective**
- Validate all pipeline components function correctly in isolation and together
- Ensure localization support works across all target regions
- Verify error handling, simulation modes, and fallback mechanisms
- Generate test reports for audit and debugging
- Provide a step‑by‑step guide for evaluators to complete full testing

### **Test Approach**
- **Progressive testing**: Utility scripts → Individual steps → Full campaign workflow
- **Simulation support**: Use `--simulate` flag when external dependencies (ComfyUI, Voicebox, HeyGen, YouTube) are unavailable
- **Localization validation**: Test all 6 target regions (North America, Europe, APAC, LATAM, Middle East, South Asia)
- **Report‑driven**: Every test generates timestamped markdown and JSON reports in `test_reports/`

---

## 🛠 Test Environment Setup

### **1. Create Clean Test Folder**
```bash
# Create empty test folder (outside workspace)
mkdir -p /Users/youee-mac/IFN_Corp

# Copy pipeline from workspace to test folder
cp -r /Users/youee-mac/.openclaw/agents/main/workspace/creative-automation-pipeline /Users/youee-mac/IFN_Corp/

# Navigate to test directory
cd /Users/youee-mac/IFN_Corp/creative-automation-pipeline
```

### **2. Verify Basic Structure**
```bash
pwd  # Should show: /Users/youee-mac/IFN_Corp/creative-automation-pipeline
ls -la  # Should show: assets/, configs/, docs/, outputs/, scripts/, src/, etc.
```

### **3. Dependency Status Check**
```bash
# Check ComfyUI (optional – simulation available)
curl -s http://127.0.0.1:8188/prompt 2>/dev/null && echo "✅ ComfyUI running" || echo "⚠️ ComfyUI not accessible (will use simulation)"

# Check Voicebox (optional – simulation available)
# Note: Initial check may fail; retry if needed
curl -s http://127.0.0.1:17493/health 2>/dev/null && echo "✅ Voicebox running" || echo "⚠️ Voicebox not accessible (will use simulation)"

# Check Python dependencies
python3 --version
# Use pip3 if pip not found
command -v pip >/dev/null 2>&1 && pip_cmd=pip || pip_cmd=pip3
$pip_cmd list | grep -E "(pillow|opencv|numpy|requests)" || echo "⚠️ Required packages not found; run ./src/install_deps.sh"
```

---

## 🧪 Test Sequence & Expected Results

| # | Script | Purpose | Test Command | Expected Results | Verification |
|---|--------|---------|--------------|------------------|--------------|
| **1** | `timestamp_utils.sh` | Timestamp utilities | `source scripts/timestamp_utils.sh; get_timestamp_no_seconds` | Returns `YYYYMMDD_HHMM` format (e.g., `20260325_2251`) | No errors; timestamp matches current time within 1 minute |
| **2** | `fix_permissions.sh` | Fix script permissions | `./scripts/utils/fix_permissions.sh` | All `.sh` files become executable (`chmod +x`) | `ls -l scripts/*.sh` shows `-rwxr-xr-x` |
| **3** | `install_deps.sh` | Install dependencies | `./src/install_deps.sh` | Python packages installed; no permission errors | `pip list` shows required packages |
| **4** | `organize_outputs.sh` | Output organization | `./scripts/organize_outputs.sh` | Moves test files to `test_outputs/`, creates `backups/` | `ls test_outputs/` shows organized timestamped folders |
| **5** | `test_localization_demo.sh` | Test 6 region localizations | `./scripts/tests/test_localization_demo.sh` | All 6 regions processed without failures | Exit code 0; check `test_reports/*.md` for PASS status |
| **6** | `test_localization_complete.sh` | Complete localization test | `./scripts/tests/test_localization_complete.sh` | Verifies all campaign requirements for each region | Exit code 0; JSON report in `test_reports/` |
| **7** | `test_verify_localization.sh` | Verify localization output | `./scripts/tests/test_verify_localization.sh` | Compares expected vs actual localized content | Shows "All localization checks passed" |
| **8** | `test_complete_workflow.sh` | Full workflow test | `./scripts/tests/test_complete_workflow.sh` | Runs mini workflow successfully | Creates `outputs/test_workflow/` with sample assets |
| **9** | `run_tests_with_reports.sh` | Run all tests with reports | `./scripts/tests/run_tests_with_reports.sh` | Generates test reports for all test scripts | `test_reports/` contains `.md` and `.json` files |
| **10** | `test_campaign_template.sh` | Campaign testing template | `./scripts/test_campaign_template.sh 1_Smart_Kitchen_Essentials_North_America --simulate --quiet` | Creates timestamped test outputs/reports | `test_outputs/campaign_test_*/` created with logs |
| **11** | `run_images_demo.sh` | **Step 1**: Image generation | `./scripts/campaigns/run_images_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose` | Generates product images (or simulation placeholders) | `outputs/images/` contains product images (or `.placeholder` files) |
| **12** | `run_video_demo.sh` | **Step 2**: Video creation | `./scripts/campaigns/run_video_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose` | Creates product video (single or campaign slideshow) | `outputs/video/` or `outputs/campaign/` contains `.mp4` file |
| **13** | `run_heygen_demo.sh` | **Step 3**: Avatar generation | `./scripts/campaigns/run_heygen_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose` | Generates avatar video (mock if `--simulate`) | `outputs/avatar/` contains avatar video or simulation log |
| **14** | `run_heygen_products_demo.sh` | **Step 4**: Combine videos | `./scripts/campaigns/run_heygen_products_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose` | Creates combined product+avatar video | `outputs/combined/` contains final `.mp4` |
| **15** | `run_youtube_heygen_products_demo.sh` | **Step 5**: YouTube upload | `./scripts/campaigns/run_youtube_heygen_products_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --simulate --verbose` | Simulates YouTube upload (or real with OAuth) | Output shows "Upload simulation complete" or YouTube video ID |
| **16** | `run_campaign_demo.sh` | **Master orchestrator** | `./run_campaign_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --simulate --verbose` | Runs all 5 steps sequentially | Complete campaign folder in `outputs/campaign_*/` with all assets |

---

## 🔧 Dependency Checklist

| Dependency | Status Check | Actual Status | Simulation Alternative | Test Impact |
|------------|--------------|---------------|------------------------|-------------|
| **ComfyUI** | `curl -s http://127.0.0.1:8188/prompt` | ✅ Running (`{"exec_info": {"queue_remaining": 0}}`) | Image generation uses placeholder | Step 1 (images) – simulation creates `.placeholder` files |
| **Voicebox** | `curl -s http://127.0.0.1:17493/health` | ✅ Running (`{"status":"healthy",...}`) | Voice synthesis skipped | Step 2 (video) – uses silent video or mock audio |
| **HeyGen API** | API key in env/argument | Not tested (simulation available) | `--simulate` flag | Steps 3‑4 – mock avatar generation, video combination still works |
| **Google Drive** | Service account JSON | Not tested (simulation available) | Skip with `--simulate` | Optional upload – not required for core pipeline |
| **YouTube OAuth** | `client_secrets.json` | Not tested (simulation available) | `--simulate` flag | Step 5 – simulation outputs metadata without real upload |
| **Python Dependencies** | `pip list \| grep -E "(pillow\|opencv\|numpy\|requests\|pyyaml\|google)"` | ✅ Core packages installed (pillow, opencv-python, numpy, requests); missing pyyaml, Google APIs. Use `pip3` if `pip` not found | Install via `pip install -r requirements.txt` or `./src/install_deps.sh` | All steps – missing packages may cause import errors |

**Simulation Notes:**
- Add `--simulate` flag to any campaign script to bypass external dependencies
- Simulation still validates pipeline logic, file flows, and error handling
- Real dependencies only needed for final production validation
- **Actual status:** ComfyUI confirmed running (`{"exec_info": {"queue_remaining": 0}}`); Voicebox confirmed running (initial health check may fail, retry succeeds); Python 3.9.6 with pip 26.0.1; Core packages (pillow, opencv-python, numpy, requests) installed via pip3; Use `./src/install_deps.sh` for complete dependency setup including pyyaml and Google APIs

---

## 🚀 Execution Guide

### **Phase 1: Utility & Test Scripts (Tests 1‑10)**
Run in order to validate core infrastructure:
```bash
cd /Users/youee-mac/IFN_Corp/creative-automation-pipeline

# 1‑4: Core utilities
source scripts/timestamp_utils.sh; get_timestamp_no_seconds
./scripts/utils/fix_permissions.sh
./src/install_deps.sh
./scripts/organize_outputs.sh

# Ensure Python can find localization module
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# 5‑10: Localization and test suites
./scripts/tests/test_localization_demo.sh
./scripts/tests/test_localization_complete.sh
./scripts/tests/test_verify_localization.sh
./scripts/tests/test_complete_workflow.sh
./scripts/tests/run_tests_with_reports.sh
./scripts/test_campaign_template.sh 1_Smart_Kitchen_Essentials_North_America --simulate --quiet
```

**Checkpoint:** Verify `test_reports/` contains reports for all completed tests.

### **Phase 2: Campaign Steps (Tests 11‑16)**
Run sequentially using the **Smart Kitchen Essentials** campaign:
```bash
# Step 1: Images
./scripts/campaigns/run_images_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose

# Step 2: Video
./scripts/campaigns/run_video_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose

# Step 3: Avatar (simulate)
./scripts/campaigns/run_heygen_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose --simulate

# Step 4: Combine
./scripts/campaigns/run_heygen_products_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose

# Step 5: YouTube (simulate)
./scripts/campaigns/run_youtube_heygen_products_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --simulate --verbose

# Full campaign (orchestrator)
./run_campaign_demo.sh --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --simulate --verbose
```

**Checkpoint:** Verify `outputs/` contains organized campaign folder with all 5 step outputs.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Permission denied"** on scripts | Run `./scripts/utils/fix_permissions.sh` (recommended) or run `chmod +x` on the specific script |
| **Python import errors** | Run `./src/install_deps.sh` |
| **"ModuleNotFoundError: No module named 'localization'"** | Add src directory to Python path: `export PYTHONPATH=$PYTHONPATH:$(pwd)/src` then run the test again |
| **"pip: command not found"** or **"pip list shows no packages"** | Use `pip3` instead of `pip`; add alias `alias pip='pip3'` to `~/.zshrc` and `source ~/.zshrc` |
| **PATH warnings** during package installation | Add Python bin to PATH: `echo 'export PATH="/Users/youee-mac/Library/Python/3.9/bin:\$PATH"' >> ~/.zshrc && source ~/.zshrc` |
| **ComfyUI/Voicebox connection failed** | Add `--simulate` flag to campaign scripts |
| **Missing brief.json files** | Copy from `configs/examples/` to `configs/brief.json` |
| **Test reports not generated** | Check `test_reports/` directory exists; script creates it automatically |
| **YouTube upload requires OAuth** | Use `--simulate` or provide `client_secrets.json` via `--client-secrets` |
| **HeyGen API errors** | Use `--simulate` or set `HEYGEN_API_KEY` environment variable |

### **Resume Testing After Session Expiry**
If testing is interrupted (session expiry, compaction, restart):
1. Navigate back to test folder: `cd /Users/youee-mac/IFN_Corp/creative-automation-pipeline`
2. Check progress: `ls test_reports/*.md` – see which tests already completed
3. Consult table above – run next script in sequence
4. Verify expected results match before proceeding

---

## 📊 Test Report Analysis

All tests generate two report files:
- **Markdown report** (`test_report_*.md`): Human‑readable summary with tables and logs
- **JSON report** (`test_report_*.json`): Machine‑readable results for automation

**Key report metrics to verify:**
- ✅ **Exit code**: Should be `0` for success
- ✅ **Check results**: All checks should show `✅ PASS` (warnings acceptable)
- ✅ **Duration**: Each test should complete within expected time (varies by step)
- ✅ **Output files**: Verify expected files created in correct directories

**Example verification command:**
```bash
# Check latest test report
latest_report=$(ls -t test_reports/test_report_*.md | head -1)
echo "Latest report: $latest_report"
head -20 "$latest_report"

# Check JSON results
json_report="${latest_report%.md}.json"
jq '.results.passed, .results.failed, .duration_seconds' "$json_report"
```

---

## 📁 Appendix: Script Reference

| Script Category | Location | Purpose |
|----------------|----------|---------|
| **Utilities** | `scripts/utils/` | Timestamps, permissions, dependencies, cleanup |
| **Tests** | `scripts/tests/` | Localization, workflow, verification, reporting |
| **Campaigns** | `scripts/campaigns/` | 5‑step pipeline: images → video → avatar → combine → YouTube |
| **Source** | `src/` | Python modules: timestamp utilities, report generation, etc. |
| **Configs** | `configs/examples/` | Example briefs for 6 regions and multiple products |
| **Outputs** | `outputs/` | Generated assets organized by campaign and step |
| **Test Outputs** | `test_outputs/` | Test‑specific outputs (not production) |
| **Test Reports** | `test_reports/` | Generated test reports (markdown + JSON) |

---

## 🔄 Maintenance & Updates

This is a **living document**. Update when:
- New scripts are added to the pipeline
- Test sequence changes
- Expected results need adjustment
- Troubleshooting steps are discovered

**Document versioning:**
- Update **Last Updated** date
- Note changes in **Git commit message**
- Keep backward compatibility for existing test instructions

---

*"A well‑tested pipeline is a reliable pipeline."*  
Use this document to systematically validate all components, resume testing after interruptions, and ensure the Creative Automation Pipeline meets production standards.