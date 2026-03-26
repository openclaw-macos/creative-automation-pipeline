#!/bin/bash
# Consolidated HeyGen Avatar Integration Script
# Reads from campaign brief.json, uses regions-language.json mapping, and generates avatar video
# Supports avatar_script field in brief (or generates from products using AI)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
SRC_DIR="$PROJECT_ROOT/src"
CONFIGS_DIR="$PROJECT_ROOT/configs"
OUTPUTS_DIR="$PROJECT_ROOT/outputs/heygen"

# Default values
BRIEF_FILE="$CONFIGS_DIR/brief.json"
USE_REAL_TRANSLATION=false
LOCAL_MODEL="mistral-nemo"
VERBOSE=false

# HeyGen API key (provided by user)
HEYGEN_API_KEY="sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --brief)
            BRIEF_FILE="$2"
            shift 2
            ;;
        --use-real-translation)
            USE_REAL_TRANSLATION=true
            shift
            ;;
        --local-model)
            LOCAL_MODEL="$2"
            shift 2
            ;;
        --api-key)
            HEYGEN_API_KEY="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Generate HeyGen avatar video from campaign brief"
            echo ""
            echo "Options:"
            echo "  --brief FILE              Path to brief.json (default: configs/brief.json)"
            echo "  --use-real-translation    Use real translation API (default: mock/offline)"
            echo "  --local-model MODEL       Local model for script planning (default: mistral-nemo)"
            echo "  --api-key KEY             HeyGen API key (overrides default)"
            echo "  --verbose                 Enable verbose output"
            echo "  --help                    Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --brief configs/brief.json"
            echo "  $0 --api-key \"sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=== HeyGen Avatar Integration (Consolidated) ==="
echo "Brief file: $BRIEF_FILE"
echo "Translation: $([ "$USE_REAL_TRANSLATION" = true ] && echo "Real API" || echo "Mock (offline)")"
echo "Local model: $LOCAL_MODEL"
echo ""

# Create outputs directory
mkdir -p "$OUTPUTS_DIR"

# Check if brief file exists
if [ ! -f "$BRIEF_FILE" ]; then
    echo "❌ Brief file not found: $BRIEF_FILE"
    echo "   Create a brief.json file or specify with --brief"
    exit 1
fi

# Check if API key is set
if [ -z "$HEYGEN_API_KEY" ] || [ "$HEYGEN_API_KEY" = "YOUR_HEYGEN_API_KEY_HERE" ] || [ "$HEYGEN_API_KEY" = "sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "❌ HeyGen API key not set."
    echo "   Please update the HEYGEN_API_KEY variable in this script or use --api-key"
    exit 1
fi

echo "API key configured (starts with: ${HEYGEN_API_KEY:0:16}...)"
echo "Using HeyGen v2 API with lowercase 'x-api-key' header"
echo "Using digital twin: Agent 42 from isFutureNOW"
echo "Using voice: RaviK Pullet"
echo ""

# Use virtual environment Python if available
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Generate output filename based on brief
BRIEF_NAME=$(basename "$BRIEF_FILE" .json)
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
OUTPUT_VIDEO="$OUTPUTS_DIR/${BRIEF_NAME}_avatar_${TIMESTAMP}.mp4"

echo "Generating avatar video from brief..."
echo "  Output: $OUTPUT_VIDEO"
echo ""

# Build command arguments
CMD_ARGS=(
    "--brief" "$BRIEF_FILE"
    "--api-key" "$HEYGEN_API_KEY"
    "--output" "$OUTPUT_VIDEO"
    "--local-model" "$LOCAL_MODEL"
)

if [ "$USE_REAL_TRANSLATION" = true ]; then
    CMD_ARGS+=("--use-real-translation")
fi

if [ "$VERBOSE" = true ]; then
    CMD_ARGS+=("--verbose")
fi

# Run HeyGen generation
echo "  Running: $PYTHON_EXEC $SRC_DIR/generate_heygen_from_brief.py ${CMD_ARGS[*]}"
echo ""

$PYTHON_EXEC "$SRC_DIR/generate_heygen_from_brief.py" "${CMD_ARGS[@]}"

echo ""
echo "========================================="
echo "HeyGen Avatar Generation Completed!"
echo ""
echo "Output video: $OUTPUT_VIDEO"
echo ""
echo "To play the video:"
echo "  open \"$OUTPUT_VIDEO\""
echo ""
echo "To concatenate with products video (optional):"
echo "  ./scripts/campaigns/run_heygen_products_demo.sh --avatar-video \"$OUTPUT_VIDEO\""
echo ""
echo "Note: This uses the actual HeyGen API which may incur costs."
echo "Script planning uses local model processing to avoid DeepSeek API charges."