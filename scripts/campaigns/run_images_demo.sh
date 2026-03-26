#!/bin/bash
# Image Generation Pipeline - Creates product images for campaign
# First step in campaign sequence: images → video → heygen → combined

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
SRC_DIR="$PROJECT_ROOT/src"
OUTPUTS_DIR="$PROJECT_ROOT/outputs"
WORKFLOW="$PROJECT_ROOT/configs/default_workflow.json"

echo "=== Creative Automation Pipeline Demo ==="
echo ""

# Create outputs directory
mkdir -p "$OUTPUTS_DIR/images"
mkdir -p "$OUTPUTS_DIR/logs"

# Check if ComfyUI server is running
echo "Checking ComfyUI server connectivity..."
if ! curl -s http://127.0.0.1:8188/prompt > /dev/null; then
    echo "⚠️  ComfyUI server not running at http://127.0.0.1:8188"
    echo "Please start ComfyUI with: cd /path/to/ComfyUI && python main.py --port 8188"
    exit 1
fi
echo "✅ ComfyUI server is accessible"
echo ""

# Run the pipeline with compliance checks
echo "Running pipeline with compliance checks..."
echo "========================================="

# Use virtual environment Python if available
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

$PYTHON_EXEC "$SRC_DIR/comfyui_generate.py" \
    --prompt "a sleek coffee maker on a modern kitchen counter" \
    --output "$OUTPUTS_DIR/images/coffee_maker.png" \
    --workflow "$WORKFLOW" \
    --product "Coffee Maker" \
    --campaign-message "Start your day smarter with our premium coffee maker" \
    --compliance-check \
    --legal-check \
    --seed 42

echo ""
echo "========================================="
echo "Demo completed successfully!"
echo ""
echo "Outputs:"
echo "  - Image: $OUTPUTS_DIR/images/coffee_maker.png"
echo "  - Database: $PROJECT_ROOT/outputs/logs/pipeline_logs.db"
echo "  - JSON Report: $PROJECT_ROOT/outputs/logs/run_report.json"
echo ""
echo "To view the database, run:"
echo "  sqlite3 $PROJECT_ROOT/outputs/logs/pipeline_logs.db \"SELECT * FROM generation_logs ORDER BY timestamp DESC LIMIT 5;\""
