#!/bin/bash
# Demo script for HeyGen Avatar Integration
# Uses local models (qwen3‑vl, mistral‑nemo) for script planning to avoid DeepSeek API charges

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUTS_DIR="$SCRIPT_DIR/outputs/heygen"

# Default target region
TARGET_REGION="USA"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target-region)
            TARGET_REGION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--target-region REGION]"
            exit 1
            ;;
    esac
done

echo "=== HeyGen Avatar Integration Demo ==="
echo "Target Region: $TARGET_REGION"
echo ""

# Create outputs directory
mkdir -p "$OUTPUTS_DIR"

# HeyGen API key (provided by user)
HEYGEN_API_KEY="sk_V2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

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

# Test script for avatar
SCRIPT="Welcome to NexaGoods, your source for premium kitchen essentials. Today we're showcasing our state-of-the-art coffee maker, designed for modern professionals who value both style and function. Start your day smarter with appliances that work as hard as you do."

echo ""
echo "Generating avatar video with HeyGen..."
echo "  Using local model: mistral-nemo (to avoid DeepSeek API charges)"
echo "  Script length: ${#SCRIPT} characters"
echo "  Output: $OUTPUTS_DIR/nexagoods_avatar.mp4"
echo ""

$PYTHON_EXEC "$SRC_DIR/heygen_integration.py" \
    --api-key "$HEYGEN_API_KEY" \
    --script "$SCRIPT" \
    --output "$OUTPUTS_DIR/nexagoods_avatar.mp4" \
    --local-model "mistral-nemo" \
    --target-region "$TARGET_REGION"

echo ""
echo "========================================="
echo "HeyGen Demo completed!"
echo ""
echo "Note: This demo uses the actual HeyGen API which may incur costs."
echo "The script planning uses simulated local model processing to avoid"
echo "DeepSeek API charges (as requested)."
echo ""
echo "To play the video, run:"
echo "  open $OUTPUTS_DIR/nexagoods_avatar.mp4"
echo ""
echo "Next steps for production:"
echo "  1. Replace simulated local model calls with actual Ollama/LLM calls"
echo "  2. Add brand compliance checks for avatar videos"
echo "  3. Integrate with the main creative automation pipeline"