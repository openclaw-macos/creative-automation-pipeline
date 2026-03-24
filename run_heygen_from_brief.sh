#!/bin/bash
# Generate HeyGen avatar video from campaign brief

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUTS_DIR="$SCRIPT_DIR/outputs/heygen_from_brief"

# HeyGen API key (provided by user)
HEYGEN_API_KEY="sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

echo "=== HeyGen Avatar Generation from Campaign Brief ==="
echo ""

# Create outputs directory
mkdir -p "$OUTPUTS_DIR"

# Check if API key is set
if [ -z "$HEYGEN_API_KEY" ] || [ "$HEYGEN_API_KEY" = "YOUR_HEYGEN_API_KEY_HERE" ]; then
    echo "❌ HeyGen API key not set."
    echo "   Please update the HEYGEN_API_KEY variable in this script."
    exit 1
fi

echo "API key configured (starts with: ${HEYGEN_API_KEY:0:16}...)"

# Use virtual environment Python if available
if [ -f "./venv/bin/python" ]; then
    PYTHON_EXEC="./venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Test with configs/brief.json
BRIEF_FILE="$SCRIPT_DIR/configs/brief.json"
OUTPUT_FILE="$OUTPUTS_DIR/nexagoods_from_brief.mp4"

echo ""
echo "Generating avatar video from brief..."
echo "  Brief: $BRIEF_FILE"
echo "  Output: $OUTPUT_FILE"
echo "  Translation: Mock (offline) - set --use-real-translation for real API"
echo ""

$PYTHON_EXEC "$SRC_DIR/generate_heygen_from_brief.py" \
    --brief "$BRIEF_FILE" \
    --api-key "$HEYGEN_API_KEY" \
    --output "$OUTPUT_FILE"

echo ""
echo "========================================="
echo "HeyGen from Brief completed!"
echo ""
echo "To play the video, run:"
echo "  open $OUTPUT_FILE"
echo ""
echo "To use real translation API (requires internet):"
echo "  $PYTHON_EXEC \"$SRC_DIR/generate_heygen_from_brief.py\" \\"
echo "    --brief \"$BRIEF_FILE\" \\"
echo "    --api-key \"$HEYGEN_API_KEY\" \\"
echo "    --output \"$OUTPUTS_DIR/nexagoods_real_translation.mp4\" \\"
echo "    --use-real-translation"
echo ""
echo "To generate video for different briefs:"
echo "  1. Create brief.json files in configs/"
echo "  2. Run: python3 src/generate_heygen_from_brief.py --brief configs/brief_japan.json"
echo ""