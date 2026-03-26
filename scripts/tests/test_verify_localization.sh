#!/bin/bash
# Verification script for Creative Automation Pipeline Localization
# Tests all 6 regions, HeyGen integration, and script executability

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
SRC_DIR="$PROJECT_ROOT/src"

echo "============================================================"
echo "LOCALIZATION VERIFICATION SCRIPT"
echo "============================================================"
echo ""

# Test 1: Check script executability (new organization)
echo "1. Checking script executability..."
SCRIPTS=(
    "$PROJECT_ROOT/scripts/campaigns/run_images_demo.sh"
    "$PROJECT_ROOT/scripts/campaigns/run_video_demo.sh"
    "$PROJECT_ROOT/scripts/campaigns/run_heygen_demo.sh"
    "$PROJECT_ROOT/scripts/tests/test_localization_demo.sh"
    "$PROJECT_ROOT/scripts/tests/test_localization_complete.sh"
    "$PROJECT_ROOT/scripts/tests/test_complete_workflow.sh"
)

for script_path in "${SCRIPTS[@]}"; do
    script_name=$(basename "$script_path")
    if [ -f "$script_path" ]; then
        if [ -x "$script_path" ]; then
            echo "  ✅ $script_name (exists and executable)"
        else
            echo "  ⚠️  $script_name (exists but not executable, fixing...)"
            chmod +x "$script_path"
        fi
    else
        echo "  ❌ $script_name (missing at: $script_path)"
    fi
done

echo ""
echo "2. Testing Python localization module..."
python3 -c "
import sys
sys.path.append('$SRC_DIR')
try:
    from localization import Localization
    print('  ✅ Localization module imports successfully')
    
    loc = Localization(use_mock=True)
    test_regions = [
        ('USA', 'en'),
        ('European Union (Germany/France)', 'de'),
        ('Japan', 'ja'),
        ('UAE / Saudi Arabia', 'ar'),
        ('Brazil', 'pt'),
        ('Scandinavia (Sweden/Denmark)', 'sv')
    ]
    
    all_pass = True
    for region, expected in test_regions:
        actual = loc.get_language_code(region)
        if actual == expected:
            print(f'    ✅ {region:40} → {actual}')
        else:
            print(f'    ❌ {region:40} → {actual} (expected {expected})')
            all_pass = False
    
    if all_pass:
        print('  ✅ All region mappings correct')
    else:
        print('  ❌ Some region mappings incorrect')
        
except Exception as e:
    print(f'  ❌ Localization module error: {e}')
"

echo ""
echo "3. Testing HeyGen integration with localization..."
python3 -c "
import sys
sys.path.append('$SRC_DIR')
try:
    from heygen_integration import HeyGenIntegration
    print('  ✅ HeyGen module imports successfully')
    
    # Test that create_avatar_video accepts language parameter
    import inspect
    sig = inspect.signature(HeyGenIntegration.create_avatar_video)
    params = list(sig.parameters.keys())
    if 'language' in params:
        print('  ✅ create_avatar_video accepts language parameter')
    else:
        print('  ❌ create_avatar_video missing language parameter')
        
except Exception as e:
    print(f'  ❌ HeyGen module error: {e}')
"

echo ""
echo "4. Testing Campaign Manager..."
python3 -c "
import sys
sys.path.append('$SRC_DIR')
try:
    from campaign_manager import CampaignManager
    print('  ✅ CampaignManager module imports successfully')
    
    import tempfile
    import os
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CampaignManager(campaigns_root=os.path.join(tmpdir, 'campaigns'))
        print('  ✅ CampaignManager instantiated')
        
        # Test folder creation
        test_brief = {
            'products': ['Test Product'],
            'target_region': 'Japan',
            'audience': 'Test',
            'campaign_message': 'Test'
        }
        
        brief_path = os.path.join(tmpdir, 'test_brief.json')
        with open(brief_path, 'w') as f:
            json.dump(test_brief, f)
        
        campaign_id, folder_path = manager.process_brief_file(brief_path)
        print(f'  ✅ Created campaign folder: {os.path.basename(folder_path)}')
        
except Exception as e:
    print(f'  ❌ CampaignManager error: {e}')
"

echo ""
echo "5. Testing Video Pipeline integration..."
python3 -c "
import sys
sys.path.append('$SRC_DIR')
try:
    from video_pipeline import VideoPipeline
    print('  ✅ VideoPipeline module imports successfully')
    
    # Test initialization with different regions
    test_cases = [
        ('USA', 'en'),
        ('Japan', 'ja'),
    ]
    
    for region, expected_lang in test_cases:
        pipeline = VideoPipeline(target_region=region)
        if pipeline.language_code == expected_lang:
            print(f'    ✅ {region:30} → {pipeline.language_code}')
        else:
            print(f'    ❌ {region:30} → {pipeline.language_code} (expected {expected_lang})')
            
except Exception as e:
    print(f'  ❌ VideoPipeline error: {e}')
"

echo ""
echo "============================================================"
echo "SUMMARY & NEXT STEPS"
echo "============================================================"
echo ""
echo "If all tests passed:"
echo "  ✅ Localization is fully integrated and working"
echo ""
echo "To test HeyGen avatar localization:"
echo "  ./scripts/campaigns/run_heygen_demo.sh --target-region \"Japan\""
echo ""
echo "To test video pipeline localization:"
echo "  ./scripts/campaigns/run_video_demo.sh --target-region \"Brazil\""
echo ""
echo "To run comprehensive test suite:"
echo "  ./scripts/tests/test_localization_complete.sh"
echo ""
echo "To see all available scripts:"
echo "  ls -la scripts/campaigns/*.sh scripts/tests/*.sh"
echo ""
echo "============================================================"
echo "VERIFICATION COMPLETE"
echo "============================================================"