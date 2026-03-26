#!/bin/bash
# Image Generation Pipeline - Creates product images for campaign from brief.json
# First step in campaign sequence: images → video → heygen → combined
# Reads configs/brief.json by default, accepts --brief for alternative brief files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
SRC_DIR="$PROJECT_ROOT/src"
OUTPUTS_DIR="$PROJECT_ROOT/outputs"
WORKFLOW="$PROJECT_ROOT/configs/default_workflow.json"

# Default brief file
BRIEF_FILE="$PROJECT_ROOT/configs/brief.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --brief)
            BRIEF_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Image Generation Pipeline - Creates product images for campaign from brief.json"
            echo ""
            echo "Options:"
            echo "  --brief FILE    Path to brief.json (default: configs/brief.json)"
            echo "  --help          Show this help"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --brief configs/examples/3_Premium_Personal_Care_Japan/brief.json"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=== Creative Automation Pipeline - Image Generation ==="
echo "Brief file: $BRIEF_FILE"
echo ""

# Check if brief file exists
if [ ! -f "$BRIEF_FILE" ]; then
    echo "❌ Brief file not found: $BRIEF_FILE"
    echo "   Create a brief.json file or specify with --brief"
    exit 1
fi

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

# Extract products from brief.json
echo "Reading products from brief.json..."
PRODUCTS=$(python3 -c "
import json
with open('$BRIEF_FILE', 'r', encoding='utf-8') as f:
    brief = json.load(f)
products = brief.get('products', ['Coffee Maker'])
print(' '.join(products))
")

CAMPAIGN_MESSAGE=$(python3 -c "
import json
with open('$BRIEF_FILE', 'r', encoding='utf-8') as f:
    brief = json.load(f)
print(brief.get('campaign_message', 'Start your day smarter with our kitchen essentials').replace('\n', ' ').replace('\"', '\\\\\"'))
")

echo "Products to generate: $PRODUCTS"
echo "Campaign message: $CAMPAIGN_MESSAGE"
echo ""

# Use virtual environment Python if available
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Generate images for each product
INDEX=1
for PRODUCT in $PRODUCTS; do
    echo "=== Generating image for: $PRODUCT ==="
    
    # Clean product name for filename
    CLEAN_NAME=$(echo "$PRODUCT" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
    OUTPUT_PATH="$OUTPUTS_DIR/images/${CLEAN_NAME}.png"
    
    # Generate prompt based on product
    PROMPT="a sleek $PRODUCT on a modern kitchen counter, professional photography, studio lighting"
    
    echo "Prompt: $PROMPT"
    echo "Output: $OUTPUT_PATH"
    echo ""
    
    $PYTHON_EXEC "$SRC_DIR/comfyui_generate.py" \
        --prompt "$PROMPT" \
        --output "$OUTPUT_PATH" \
        --workflow "$WORKFLOW" \
        --product "$PRODUCT" \
        --campaign-message "$CAMPAIGN_MESSAGE" \
        --compliance-check \
        --legal-check \
        --seed "$INDEX"
    
    if [ -f "$OUTPUT_PATH" ]; then
        echo "✅ Successfully generated: $OUTPUT_PATH"
    else
        echo "❌ Failed to generate image for $PRODUCT"
    fi
    
    echo ""
    INDEX=$((INDEX + 1))
done

echo "========================================="
echo "Image Generation completed successfully!"
echo ""
echo "Outputs:"
for PRODUCT in $PRODUCTS; do
    CLEAN_NAME=$(echo "$PRODUCT" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
    echo "  - $PRODUCT: $OUTPUTS_DIR/images/${CLEAN_NAME}.png"
done
echo "  - Database: $PROJECT_ROOT/outputs/logs/pipeline_logs.db"
echo "  - JSON Report: $PROJECT_ROOT/outputs/logs/run_report.json"
echo ""
echo "To view the database, run:"
echo "  sqlite3 $PROJECT_ROOT/outputs/logs/pipeline_logs.db \"SELECT * FROM generation_logs ORDER BY timestamp DESC LIMIT 5;\""
echo ""
echo "Next step: Run ./scripts/campaigns/run_video_demo.sh to create video from these images"