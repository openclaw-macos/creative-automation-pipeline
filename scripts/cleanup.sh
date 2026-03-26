#!/bin/bash
# Comprehensive cleanup script for Creative Automation Pipeline
# Organizes loose files and removes unnecessary clutter for clean reruns

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Safety check: ensure we're in the project directory
if [ ! -f "$PROJECT_ROOT/run_campaign_demo.sh" ] || [ ! -d "$PROJECT_ROOT/src" ]; then
    echo "❌ Error: This script must be run from the creative-automation-pipeline project root."
    echo "   Current directory doesn't appear to be the project root."
    echo "   Project root should contain: run_campaign_demo.sh, src/, configs/"
    exit 1
fi

echo "=== Creative Automation Pipeline - Comprehensive Cleanup ==="
echo "Project root: $PROJECT_ROOT"
echo ""
echo "This script will:"
echo "  1. 📁 Create organized directories for test outputs, backups, and temporary files"
echo "  2. 📄 Move loose files (test outputs, logs, backups) to organized locations"
echo "  3. 🗑️  Clean output directories (images, video, audio, logs) for fresh runs"
echo "  4. 🐍 Remove Python cache files and system temporary files"
echo "  5. 📊 Display summary of organized files"
echo ""
echo "Note: No campaign output folders (outputs/campaign_*) will be deleted."
echo "      Only loose files and temporary files will be cleaned/organized."
echo ""

# Create organized directories if they don't exist
mkdir -p "$PROJECT_ROOT/test_outputs"
mkdir -p "$PROJECT_ROOT/backups"
mkdir -p "$PROJECT_ROOT/tmp"
mkdir -p "$PROJECT_ROOT/logs/app"
mkdir -p "$PROJECT_ROOT/test_reports/archived"

echo "📁 Created organized directories:"
echo "  test_outputs/     - Test execution outputs"
echo "  backups/          - Script backup files"
echo "  tmp/              - Temporary files"
echo "  logs/app/         - Application logs"
echo "  test_reports/archived/ - Archived test reports"
echo ""

# ----------------------------------------------------------------------
# PHASE 1: Clean and organize loose files in project root
# ----------------------------------------------------------------------

echo "🔧 Phase 1: Cleaning and organizing loose files..."
echo "  Moving test output files to test_outputs/..."

# Move test output files
for file in "$PROJECT_ROOT"/test_output_*.txt "$PROJECT_ROOT"/campaign_test_*.txt; do
    if [ -f "$file" ]; then
        mv "$file" "$PROJECT_ROOT/test_outputs/"
        echo "    📄 Moved: $(basename "$file")"
    fi
done

# Move demo run logs from outputs/ to test_outputs/
for file in "$PROJECT_ROOT"/outputs/*_run_*.txt; do
    if [ -f "$file" ]; then
        mv "$file" "$PROJECT_ROOT/test_outputs/"
        echo "    📄 Moved: outputs/$(basename "$file")"
    fi
done

# Move backup files to backups/
echo "  Moving backup files to backups/..."
for file in "$PROJECT_ROOT"/*.backup* "$PROJECT_ROOT"/*.bak "$PROJECT_ROOT"/run_*.sh.backup*; do
    if [ -f "$file" ]; then
        mv "$file" "$PROJECT_ROOT/backups/"
        echo "    💾 Moved: $(basename "$file")"
    fi
done

# Move temporary test scripts to tmp/
echo "  Moving temporary test scripts to tmp/..."
for file in "$PROJECT_ROOT"/test_*.py; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "test_compound_analysis.py" ]; then
        mv "$file" "$PROJECT_ROOT/tmp/"
        echo "    🐍 Moved: $(basename "$file")"
    fi
done

# Move test compound analysis to test_outputs/ (keep for reference)
if [ -f "$PROJECT_ROOT/test_compound_analysis.py" ]; then
    mv "$PROJECT_ROOT/test_compound_analysis.py" "$PROJECT_ROOT/test_outputs/"
    echo "    📊 Moved: test_compound_analysis.py"
fi

# Move loose JSON files (except config files) to test_outputs/
echo "  Moving loose JSON files to test_outputs/..."
for file in "$PROJECT_ROOT"/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip config files
        if [[ "$filename" != "brand_config.json" && "$filename" != "brief.json" && "$filename" != "assets.json" && "$filename" != "default_workflow.json" && "$filename" != "sdxl_workflow.json" ]]; then
            mv "$file" "$PROJECT_ROOT/test_outputs/"
            echo "    📄 Moved: $filename"
        fi
    fi
done

# Move any other loose text/log files to test_outputs/
echo "  Moving other loose text/log files to test_outputs/..."
for file in "$PROJECT_ROOT"/*.txt "$PROJECT_ROOT"/*.log; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip README and LICENSE
        if [[ "$filename" != "README.md" && "$filename" != "LICENSE" && "$filename" != "requirements.txt" ]]; then
            mv "$file" "$PROJECT_ROOT/test_outputs/"
            echo "    📄 Moved: $filename"
        fi
    fi
done

# ----------------------------------------------------------------------
# PHASE 2: Clean outputs directory (preserve campaign folders)
# ----------------------------------------------------------------------

echo ""
echo "🔧 Phase 2: Cleaning outputs directory..."
echo "  Removing loose files from outputs/..."

# Remove loose files in outputs/ (keep campaign_* directories)
find "$PROJECT_ROOT/outputs" -maxdepth 1 -type f -name "*.txt" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT/outputs" -maxdepth 1 -type f -name "*.log" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT/outputs" -maxdepth 1 -type f -name "*.json" ! -name "assets.json" -exec rm -f {} \; 2>/dev/null || true

# Clean campaign-specific output directories (if they exist)
if [ -d "$PROJECT_ROOT/outputs/campaign" ]; then
    echo "  Cleaning campaign output directory..."
    find "$PROJECT_ROOT/outputs/campaign/images/base" -name "*.png" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/outputs/campaign/images/aspect_ratios" -name "*.png" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/outputs/campaign/images/with_logo" -name "*.png" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/outputs/campaign/video" -name "*.mp4" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/outputs/campaign/audio" -name "*.mp3" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/outputs/campaign/logs" -name "*.log" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$PROJECT_ROOT/outputs/campaign/logs" -name "*.txt" -type f -exec rm -f {} \; 2>/dev/null || true
fi

# ----------------------------------------------------------------------
# PHASE 3: Organize test reports
# ----------------------------------------------------------------------

echo ""
echo "🔧 Phase 3: Organizing test reports..."
echo "  Archiving old test report logs..."

# Move phase log files to archived
for file in "$PROJECT_ROOT"/test_reports/phase*.log; do
    if [ -f "$file" ]; then
        mv "$file" "$PROJECT_ROOT/test_reports/archived/"
        echo "    📋 Archived: test_reports/$(basename "$file")"
    fi
done

# Keep summary and fix reports in main test_reports/
echo "  Keeping summary reports in test_reports/..."

# ----------------------------------------------------------------------
# PHASE 4: Clean Python cache and temporary files
# ----------------------------------------------------------------------

echo ""
echo "🔧 Phase 4: Cleaning Python cache and temporary files..."

# Remove __pycache__ directories
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true

# Remove .pyc files
find "$PROJECT_ROOT" -type f -name "*.pyc" -exec rm -f {} \; 2>/dev/null || true

# Remove .pyo files
find "$PROJECT_ROOT" -type f -name "*.pyo" -exec rm -f {} \; 2>/dev/null || true

# Remove .pytest_cache if exists
if [ -d "$PROJECT_ROOT/.pytest_cache" ]; then
    rm -rf "$PROJECT_ROOT/.pytest_cache"
fi

# Remove system temporary files and editor backups
echo "  Removing system temporary files and editor backups..."
find "$PROJECT_ROOT" -type f -name ".DS_Store" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "Thumbs.db" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.swp" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.swo" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.swn" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.swl" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*~" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.tmp" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.temp" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name ".~lock.*" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.orig" -exec rm -f {} \; 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.rej" -exec rm -f {} \; 2>/dev/null || true

# Remove empty directories (except important ones)
echo "  Removing empty directories..."
find "$PROJECT_ROOT" -type d -empty ! -path "$PROJECT_ROOT/.git/*" ! -path "$PROJECT_ROOT/.venv/*" ! -path "$PROJECT_ROOT/venv/*" ! -path "$PROJECT_ROOT/outputs/*" ! -path "$PROJECT_ROOT/test_outputs/*" ! -path "$PROJECT_ROOT/backups/*" ! -path "$PROJECT_ROOT/tmp/*" ! -path "$PROJECT_ROOT/logs/*" ! -path "$PROJECT_ROOT/test_reports/*" -exec rmdir {} \; 2>/dev/null || true

# ----------------------------------------------------------------------
# PHASE 5: Verify cleanup
# ----------------------------------------------------------------------

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📊 Summary of organized files:"
echo "  Test outputs:     $(ls -1 "$PROJECT_ROOT/test_outputs/" 2>/dev/null | wc -l) files"
echo "  Backups:          $(ls -1 "$PROJECT_ROOT/backups/" 2>/dev/null | wc -l) files"
echo "  Temporary files:  $(ls -1 "$PROJECT_ROOT/tmp/" 2>/dev/null | wc -l) files"
echo "  Archived logs:    $(ls -1 "$PROJECT_ROOT/test_reports/archived/" 2>/dev/null | wc -l) files"
echo ""
echo "🏗️  Project structure is now clean and organized."
echo "   Run './run_campaign_demo.sh' for fresh campaign execution."
echo "   Run './scripts/cleanup.sh' anytime to reorganize files."
echo ""

# Optional: Show remaining loose files (for debugging)
echo "🔍 Remaining loose files in project root:"
find "$PROJECT_ROOT" -maxdepth 1 -type f \( -name "*.txt" -o -name "*.log" -o -name "*.bak" -o -name "*backup*" -o -name "test_*.py" \) 2>/dev/null | grep -v ".git" | while read -r file; do
    if [ -f "$file" ]; then
        echo "   ⚠️  Found: $(basename "$file")"
    fi
done

# ----------------------------------------------------------------------
# OPTIONAL: Clean old campaign directories (keep only last 5)
# Uncomment the following lines if you want to automatically clean
# old campaign output directories to save disk space.
# 
# Note: Works with both timestamp formats:
#   - Old format (with seconds): campaign_*_YYYYMMDD_HHMMSS
#   - New format (no seconds):   campaign_*_YYYYMMDD_HHMM
# ----------------------------------------------------------------------
# echo ""
# echo "🔧 Optional: Cleaning old campaign directories (keeping last 5)..."
# # List campaign directories sorted by modification time, keep last 5
# cd "$PROJECT_ROOT/outputs" 2>/dev/null && {
#     ls -dt campaign_* 2>/dev/null | tail -n +6 | while read -r dir; do
#         if [ -d "$dir" ]; then
#             echo "   🗑️  Removing old campaign directory: $dir"
#             rm -rf "$dir"
#         fi
#     done
#     cd - >/dev/null
# } || true

echo ""
echo "🎯 Tip: Add './scripts/cleanup.sh' to your .gitignore if you want to keep"
echo "      temporary files out of version control."
echo ""
echo "💡 To clean old campaign directories automatically, uncomment the"
echo "   optional section in scripts/cleanup.sh (lines 170-185)."