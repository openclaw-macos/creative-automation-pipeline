#!/bin/bash
# Demo script for Creative Automation Pipeline with Video Generation
# This script runs a test generation with full compliance, reporting, and video pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUTS_DIR="$SCRIPT_DIR/outputs"
WORKFLOW="$SCRIPT_DIR/configs/default_workflow.json"

# Default target region
TARGET_REGION="USA"
UPLOAD_TO_DRIVE=false
DRIVE_SERVICE_ACCOUNT="/Users/youee-mac/A42_Folder/google_serviceaccount/service_account.json"
DRIVE_FOLDER_ID="1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target-region)
            TARGET_REGION="$2"
            shift 2
            ;;
        --upload-to-drive)
            UPLOAD_TO_DRIVE=true
            shift
            ;;
        --drive-service-account)
            DRIVE_SERVICE_ACCOUNT="$2"
            shift 2
            ;;
        --drive-folder-id)
            DRIVE_FOLDER_ID="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--target-region REGION] [--upload-to-drive] [--drive-service-account PATH] [--drive-folder-id ID]"
            exit 1
            ;;
    esac
done

echo "=== Creative Automation Pipeline with Video Demo ==="
echo "Target Region: $TARGET_REGION"
if [ "$UPLOAD_TO_DRIVE" = true ]; then
    echo "Google Drive Upload: ENABLED"
    echo "  Service Account: $DRIVE_SERVICE_ACCOUNT"
    echo "  Folder ID: $DRIVE_FOLDER_ID"
else
    echo "Google Drive Upload: DISABLED (use --upload-to-drive to enable)"
fi
echo ""

# Create outputs directory
mkdir -p "$OUTPUTS_DIR/images"
mkdir -p "$OUTPUTS_DIR/video"
mkdir -p "$OUTPUTS_DIR/logs"

# Check if ComfyUI server is running
echo "Checking ComfyUI server connectivity..."
if ! curl -s http://127.0.0.1:8188/prompt > /dev/null; then
    echo "⚠️  ComfyUI server not running at http://127.0.0.1:8188"
    echo "Please start ComfyUI with: cd /path/to/ComfyUI && python main.py --port 8188"
    exit 1
fi
echo "✅ ComfyUI server is accessible"

# Check if Voicebox is running (optional)
echo "Checking Voicebox TTS server..."
if curl -s http://127.0.0.1:17493/health > /dev/null 2>&1; then
    echo "✅ Voicebox server is accessible"
    VOICEBOX_AVAILABLE=true
else
    echo "⚠️  Voicebox server not running at http://127.0.0.1:17493"
    echo "   Video will use silent audio fallback"
    VOICEBOX_AVAILABLE=false
fi

echo ""

# Run the pipeline with compliance checks and video generation
echo "Running pipeline with compliance checks and video generation..."
echo "=============================================================="

# Use virtual environment Python if available
if [ -f "./venv/bin/python" ]; then
    PYTHON_EXEC="./venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Build command arguments
CMD_ARGS=(
    "--prompt" "a sleek coffee maker on a modern kitchen counter"
    "--output" "$OUTPUTS_DIR/images/coffee_maker.png"
    "--workflow" "$WORKFLOW"
    "--product" "Coffee Maker"
    "--campaign-message" "Start your day smarter with our premium coffee maker"
    "--target-region" "$TARGET_REGION"
    "--compliance-check"
    "--legal-check"
    "--video"
    "--video-output-dir" "$OUTPUTS_DIR"
    "--seed" "42"
)

# Add Google Drive arguments if enabled
if [ "$UPLOAD_TO_DRIVE" = true ]; then
    CMD_ARGS+=("--upload-to-drive")
    CMD_ARGS+=("--drive-service-account" "$DRIVE_SERVICE_ACCOUNT")
    CMD_ARGS+=("--drive-folder-id" "$DRIVE_FOLDER_ID")
    CMD_ARGS+=("--keep-local")
fi

# Run the command
$PYTHON_EXEC "$SRC_DIR/comfyui_generate.py" "${CMD_ARGS[@]}"

echo ""
echo "========================================="
echo "Video Demo completed successfully!"
echo ""
echo "Outputs:"
echo "  - Image: $OUTPUTS_DIR/images/coffee_maker.png"
echo "  - Text Overlay: $OUTPUTS_DIR/video/Coffee_Maker_text_overlay.png"
echo "  - Final Image (with logo): $OUTPUTS_DIR/video/Coffee_Maker_final.png"
echo "  - Voiceover: $OUTPUTS_DIR/video/Coffee_Maker_voiceover.mp3"
echo "  - Video: $OUTPUTS_DIR/video/Coffee_Maker_video.mp4"
echo "  - Database: $SCRIPT_DIR/outputs/pipeline_logs.db"
echo "  - JSON Report: $SCRIPT_DIR/outputs/run_report.json"
echo ""
echo "To view the database, run:"
echo "  sqlite3 $SCRIPT_DIR/outputs/pipeline_logs.db \"SELECT * FROM generation_logs ORDER BY timestamp DESC LIMIT 5;\""
echo ""
echo "To play the video, run:"
echo "  open $OUTPUTS_DIR/video/Coffee_Maker_video.mp4"