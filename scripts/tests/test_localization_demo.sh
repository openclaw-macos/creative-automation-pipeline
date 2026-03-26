#!/bin/bash
# Demo script for Localization in Creative Automation Pipeline
# Tests localization for all 6 target regions specified in requirements

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
SRC_DIR="$PROJECT_ROOT/src"
OUTPUTS_DIR="$PROJECT_ROOT/outputs/localization_demo"

echo "=== Localization Demo for Creative Automation Pipeline ==="
echo ""

# Create outputs directory
mkdir -p "$OUTPUTS_DIR"

# Use virtual environment Python if available
if [ -f "./venv/bin/python" ]; then
    PYTHON_EXEC="./venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Test all 6 regions from requirements
REGIONS=(
    "USA"
    "European Union (Germany/France)"
    "Japan"
    "UAE / Saudi Arabia"
    "Brazil"
    "Scandinavia (Sweden/Denmark)"
)

# Campaign message to translate
CAMPAIGN_MESSAGE="Start your day smarter with our kitchen essentials"

echo "Testing localization for 6 regions:"
echo "==================================="

for region in "${REGIONS[@]}"; do
    echo ""
    echo "Region: $region"
    echo "-----------------------------------"
    
    # Create region-specific output directory
    REGION_CLEAN="${region//[ \/()]/_}"  # Replace spaces/slashes/parentheses with underscores
    REGION_CLEAN="${REGION_CLEAN//__/_}"    # Replace double underscores with single
    REGION_CLEAN="${REGION_CLEAN/#_/}"      # Remove leading underscore  
    REGION_CLEAN="${REGION_CLEAN/%_/}"      # Remove trailing underscore
    REGION_DIR="$OUTPUTS_DIR/$REGION_CLEAN"
    mkdir -p "$REGION_DIR"
    
    # Test localization module
    $PYTHON_EXEC -c "
import sys
import os

# Add both src and project root to Python path
sys.path.insert(0, '$SRC_DIR')
sys.path.insert(0, '$PROJECT_ROOT')

try:
    from localization import Localization
except ImportError as e:
    print(f'  ERROR: Failed to import localization: {e}')
    print(f'  sys.path: {sys.path}')
    sys.exit(1)

loc = Localization(use_mock=True)
lang = loc.get_language_code('$region')
voice = loc.get_voice_code(lang)
translated = loc.translate_text('$CAMPAIGN_MESSAGE', 'en', lang)

print(f'  Language code: {lang}')
print(f'  Voice code: {voice}')
print(f'  Original: $CAMPAIGN_MESSAGE')
print(f'  Translated: {translated}')
" > "$REGION_DIR/localization_result.txt"
    
    cat "$REGION_DIR/localization_result.txt"
    
    # Create a simple brief.json for this region
    BRIEF_JSON="$REGION_DIR/brief.json"
    cat > "$BRIEF_JSON" << EOF
{
  "products": ["Coffee Maker"],
  "target_region": "$region",
  "audience": "Young professionals 25-35",
  "campaign_message": "$CAMPAIGN_MESSAGE"
}
EOF
    
    echo "  Created brief.json in: $REGION_DIR/"
done

echo ""
echo "========================================="
echo "Localization demo completed!"
echo ""
echo "Summary:"
echo "- Tested 6 regions as specified in requirements"
echo "- Used mock translation (no internet required)"
echo "- Generated brief.json files for each region"
echo "- Outputs saved to: $OUTPUTS_DIR/"
echo ""
echo "Next steps:"
echo "1. Test with actual translation API (set use_mock=False in localization.py)"
echo "2. Run video pipeline with each brief.json"
echo "3. Verify audio generation in correct language"
echo ""
echo "To test video pipeline with a specific region:"
echo "  cd $PROJECT_ROOT"
echo "  ./run_video_demo.sh --target-region \"Japan\""
echo ""