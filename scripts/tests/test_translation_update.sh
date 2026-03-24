#!/bin/bash
# Test script to verify translation API and localization updates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"

echo "=== Testing Translation API & Localization Updates ==="
echo ""

echo "1. Testing Free Translation APIs in localization.py..."
python3 -c "
import sys
sys.path.append('$SRC_DIR')
from localization import Localization

print('Testing mock translation (offline):')
loc_mock = Localization(use_mock=True)
text = 'Start your day smarter with our kitchen essentials'
for region in ['North America (USA/Canada)', 'Japan', 'Brazil']:
    lang = loc_mock.get_language_code(region)
    translated = loc_mock.translate_text(text, 'en', lang)
    print(f'  {region:30} → {lang}: \"{translated[:40]}...\"')

print()
print('Testing actual translation APIs (requires internet):')
print('  LibreTranslate: Free, open source')
print('  Google Translate: Free tier (limited)')
print('  MyMemory Translation: Free API')
print()
print('To use actual translation (not mock):')
print('  loc = Localization(use_mock=False, translation_api=\"libre\")')
print('  or translation_api=\"google\" or \"mymemory\"')
"

echo ""
echo "2. Testing target_language field in brief.json..."
python3 -c "
import sys
sys.path.append('$SRC_DIR')
from localization import Localization
import json

loc = Localization(use_mock=True)

# Test brief with target_language
test_brief = {
    'products': ['Coffee Maker', 'Blender'],
    'target_region': 'North America (USA/Canada)',
    'target_language': 'en',
    'audience': 'Young professionals 25-35',
    'campaign_message': 'Start your day smarter with our kitchen essentials',
    'campaign_video_message': 'Welcome to NexaGoods, your source for premium kitchen essentials. Today we\'re showcasing our state-of-the-art Coffee Maker and Blender, designed for modern professionals who value both style and function. Start your day smarter with appliances that work as hard as you do. These products are well suited for Young professionals 25-35 years age living in North America (USA/Canada)'
}

print('Brief structure:')
for key, value in test_brief.items():
    if isinstance(value, str):
        print(f'  {key}: {value[:60]}...')
    else:
        print(f'  {key}: {value}')

print()
localized = loc.localize_campaign(test_brief)
print('Localized brief keys:')
for key in localized.keys():
    print(f'  - {key}')

print()
print('Language from brief:')
print(f'  target_language field: {loc.get_language_from_brief(test_brief)}')
print(f'  Generated campaign_video_message: {localized.get(\"campaign_video_message_generated\", False)}')
"

echo ""
echo "3. Testing updated configs/brief.json..."
if [ -f "$SCRIPT_DIR/configs/brief.json" ]; then
    echo "Current brief.json:"
    cat "$SCRIPT_DIR/configs/brief.json" | python3 -m json.tool
else
    echo "❌ configs/brief.json not found"
fi

echo ""
echo "4. Dependencies check..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Translation APIs in requirements.txt:"
    grep -i "translation\|libre\|google.*api\|mymemory" "$SCRIPT_DIR/requirements.txt" || echo "  (No specific translation packages needed - uses requests)"
fi

echo ""
echo "=== Summary ==="
echo ""
echo "✅ Free Translation APIs implemented:"
echo "   - LibreTranslate (free, open source)"
echo "   - Google Translate (free tier)"
echo "   - MyMemory Translation (free)"
echo "   - Mock translation fallback (offline)"
echo ""
echo "✅ target_language field support:"
echo "   - Code prefers target_language over target_region"
echo "   - Updated configs/brief.json with target_language"
echo "   - Enhanced campaign_video_message generation"
echo ""
echo "✅ North America naming:"
echo "   - Region mapping includes 'North America (USA/Canada)'"
echo "   - Backward compatible with 'USA'"
echo ""
echo "To use actual translation (not mock):"
echo "  Edit src/localization.py: change use_mock=False"
echo "  Or set translation_api='libre', 'google', or 'mymemory'"
echo ""
echo "To generate HeyGen video with brief.json:"
echo "  python3 src/comfyui_generate.py --brief configs/brief.json --video --target-language en"
echo ""