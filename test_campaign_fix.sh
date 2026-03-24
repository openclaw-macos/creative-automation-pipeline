#!/bin/bash
# Test script to verify campaign fixes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Testing Campaign Fixes ==="
echo ""

# Make scripts executable
echo "1. Making scripts executable..."
chmod +x run_campaign_demo.sh 2>/dev/null || true
chmod +x run_demo.sh 2>/dev/null || true
chmod +x run_video_demo.sh 2>/dev/null || true
chmod +x src/install_deps.sh 2>/dev/null || true
chmod +x src/aspect_ratio.py 2>/dev/null || true

echo "✅ Scripts made executable"

# Test Python imports
echo ""
echo "2. Testing Python imports..."
python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/src')

try:
    from aspect_ratio import ASPECT_RATIOS, DIMENSIONS
    print('✅ aspect_ratio.py imports successfully')
    print(f'   Available aspect ratios: {list(ASPECT_RATIOS.keys())}')
except ImportError as e:
    print(f'❌ Failed to import aspect_ratio: {e}')

try:
    from video_pipeline import VideoPipeline
    print('✅ video_pipeline.py imports successfully')
except ImportError as e:
    print(f'❌ Failed to import video_pipeline: {e}')

try:
    from localization import Localization
    print('✅ localization.py imports successfully')
except ImportError as e:
    print(f'❌ Failed to import localization: {e}')
"

# Check asset paths
echo ""
echo "3. Checking asset paths..."
python3 -c "
import sys
import os
sys.path.append('$SCRIPT_DIR/src')

try:
    import json
    
    # Check brand_config.json
    with open('$SCRIPT_DIR/configs/brand_config.json', 'r') as f:
        config = json.load(f)
    
    logo_path = config.get('logo_path', '')
    bg_music = config.get('video_settings', {}).get('background_music', '')
    
    print('Brand config paths:')
    print(f'  Logo: {logo_path}')
    print(f'  Background music: {bg_music}')
    
    # Check if files exist
    if logo_path and os.path.exists(logo_path):
        print(f'  ✅ Logo exists: {os.path.getsize(logo_path)} bytes')
    elif logo_path:
        print(f'  ❌ Logo missing: {logo_path}')
    else:
        print(f'  ⚠️  Logo path not specified')
    
    if bg_music and os.path.exists(bg_music):
        print(f'  ✅ Background music exists: {os.path.getsize(bg_music)} bytes')
    elif bg_music:
        print(f'  ❌ Background music missing: {bg_music}')
    else:
        print(f'  ⚠️  Background music path not specified')
        
except Exception as e:
    print(f'❌ Error checking assets: {e}')
"

# Check brief.json
echo ""
echo "4. Checking brief.json structure..."
if [ -f "$SCRIPT_DIR/configs/brief.json" ]; then
    python3 -c "
import sys
import json
sys.path.append('$SCRIPT_DIR/src')

with open('$SCRIPT_DIR/configs/brief.json', 'r') as f:
    brief = json.load(f)

print('Brief structure:')
for key, value in brief.items():
    if isinstance(value, list):
        print(f'  {key}: {value}')
    elif isinstance(value, str):
        if len(value) > 50:
            print(f'  {key}: {value[:50]}...')
        else:
            print(f'  {key}: {value}')
    else:
        print(f'  {key}: {type(value).__name__}')

# Check if we have target_language field
if 'target_language' in brief:
    print(f'  ✅ target_language field present: {brief[\"target_language\"]}')
else:
    print(f'  ❌ target_language field missing')

# Check if we have campaign_video_message
if 'campaign_video_message' in brief:
    print(f'  ✅ campaign_video_message field present')
else:
    print(f'  ⚠️  campaign_video_message field missing (will be generated)')
"
else
    echo "❌ brief.json not found at $SCRIPT_DIR/configs/brief.json"
fi

echo ""
echo "=== Summary ==="
echo ""
echo "To run the complete campaign demo:"
echo "  ./run_campaign_demo.sh"
echo ""
echo "To test aspect ratio generation:"
echo "  python3 src/aspect_ratio.py --image /path/to/test.jpg --output-dir ./test_output"
echo ""
echo "To install dependencies:"
echo "  ./src/install_deps.sh"
echo ""
echo "Note: The campaign demo requires:"
echo "  - ComfyUI server running on http://127.0.0.1:8188"
echo "  - Voicebox TTS server (optional) on http://127.0.0.1:17493"
echo "  - FFmpeg installed for video processing"
echo ""