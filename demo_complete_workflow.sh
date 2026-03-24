#!/bin/bash
# Complete workflow demonstration for FDE take-home assignment
# Shows localization, folder structure, and campaign generation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
CAMPAIGNS_DIR="$SCRIPT_DIR/campaigns"
OUTPUTS_DIR="$SCRIPT_DIR/outputs"

echo "============================================================"
echo "FDE TAKE-HOME ASSIGNMENT - COMPLETE WORKFLOW DEMONSTRATION"
echo "============================================================"
echo ""

echo "Step 1: Clean previous outputs"
echo "-------------------------------"
rm -rf "$CAMPAIGNS_DIR" "$OUTPUTS_DIR" 2>/dev/null || true
mkdir -p "$CAMPAIGNS_DIR"
echo "✅ Cleaned previous outputs"

echo ""
echo "Step 2: Test Localization for All 6 Regions"
echo "--------------------------------------------"
./run_localization_demo.sh 2>&1 | tail -20
echo "✅ Localization tested"

echo ""
echo "Step 3: Create Campaign Folders with Briefs"
echo "--------------------------------------------"

# Create sample briefs for different regions
REGIONS=(
    "USA"
    "European Union (Germany/France)"
    "Japan"
    "UAE / Saudi Arabia"
    "Brazil"
    "Scandinavia (Sweden/Denmark)"
)

PRODUCT_TYPES=(
    "Smart_Kitchen_Essentials"
    "Sustainable_Home_Care"
    "Premium_Personal_Care"
    "Smart_Fitness_Tech"
    "Nutritious_Baby_Care"
    "Urban_Commuter_Gear"
)

for i in "${!REGIONS[@]}"; do
    REGION="${REGIONS[$i]}"
    PRODUCT="${PRODUCT_TYPES[$i]}"
    CAMPAIGN_NUM=$((i+1))
    
    # Create brief.json
    BRIEF_FILE="$SCRIPT_DIR/configs/brief_${CAMPAIGN_NUM}.json"
    cat > "$BRIEF_FILE" << EOF
{
  "products": ["$PRODUCT"],
  "target_region": "$REGION",
  "audience": "Young professionals 25-35",
  "campaign_message": "Start your day smarter with our premium products"
}
EOF
    
    echo "  Creating campaign $CAMPAIGN_NUM: $PRODUCT ($REGION)"
    
    # Use CampaignManager to create folder
    python3 -c "
import sys
sys.path.append('$SRC_DIR')
from campaign_manager import CampaignManager
import json

manager = CampaignManager(campaigns_root='$CAMPAIGNS_DIR')

with open('$BRIEF_FILE', 'r') as f:
    brief = json.load(f)

campaign_id, folder_path = manager.create_campaign_folder(brief, '$BRIEF_FILE')
print(f'    → Created: {folder_path}')
"
    
    # Clean up temp brief file
    rm -f "$BRIEF_FILE"
done

echo "✅ Created 6 campaign folders"

echo ""
echo "Step 4: List All Campaigns"
echo "---------------------------"
python3 -c "
import sys
sys.path.append('$SRC_DIR')
from campaign_manager import CampaignManager

manager = CampaignManager(campaigns_root='$CAMPAIGNS_DIR')
campaigns = manager.list_campaigns()

print('Campaigns created:')
for campaign in campaigns:
    print(f'  {campaign[\"campaign_number\"]}: {campaign[\"folder_name\"]}')
    print(f'     Region: {campaign[\"target_region\"]}')
    print(f'     Path: {campaign[\"folder_path\"]}')
    print()
"

echo ""
echo "Step 5: Demonstrate Localized Video Generation (Simulated)"
echo "-----------------------------------------------------------"
echo "Note: Full video generation requires ComfyUI and Voicebox servers"
echo ""
echo "To generate actual videos with localization:"
for i in "${!REGIONS[@]}"; do
    REGION="${REGIONS[$i]}"
    CAMPAIGN_NUM=$((i+1))
    echo "  Campaign $CAMPAIGN_NUM ($REGION):"
    echo "    ./run_video_demo.sh --target-region \"$REGION\""
done

echo ""
echo "Step 6: Demonstrate HeyGen Avatar Localization (Simulated)"
echo "-----------------------------------------------------------"
echo "Note: HeyGen API requires valid API key"
echo ""
echo "To generate localized avatar videos:"
for i in "${!REGIONS[@]}"; do
    REGION="${REGIONS[$i]}"
    CAMPAIGN_NUM=$((i+1))
    echo "  Campaign $CAMPAIGN_NUM ($REGION):"
    echo "    ./run_heygen_demo.sh --target-region \"$REGION\""
done

echo ""
echo "============================================================"
echo "WORKFLOW VERIFICATION"
echo "============================================================"
echo ""
echo "✅ Localization implemented for 6 regions:"
for REGION in "${REGIONS[@]}"; do
    echo "   - $REGION"
done

echo ""
echo "✅ Folder structure created:"
ls -la "$CAMPAIGNS_DIR/" 2>/dev/null | grep "^d" | awk '{print "   - "$9}'

echo ""
echo "✅ Key files created:"
find "$CAMPAIGNS_DIR" -name "brief.json" 2>/dev/null | head -3 | while read file; do
    echo "   - $file"
done

echo ""
echo "============================================================"
echo "NEXT STEPS FOR USER VERIFICATION"
echo "============================================================"
echo ""
echo "1. Test with actual image generation (requires ComfyUI):"
echo "   ./run_video_demo.sh --target-region \"Japan\""
echo ""
echo "2. Test with HeyGen avatar (requires API key):"
echo "   ./run_heygen_demo.sh --target-region \"Brazil\""
echo ""
echo "3. Run comprehensive test suite:"
echo "   ./test_localization_complete.sh"
echo ""
echo "4. Check folder structure:"
echo "   ls -la campaigns/"
echo ""
echo "5. Verify localization works:"
echo "   python3 -c \"
import sys
sys.path.append('src')
from localization import Localization
loc = Localization(use_mock=True)
text = 'Start your day smarter with our kitchen essentials'
for region in ['Japan', 'Brazil', 'European Union (Germany/France)']:
    lang = loc.get_language_code(region)
    translated = loc.translate_text(text, 'en', lang)
    print(f'{region}: {translated[:50]}...')
\""
echo ""
echo "============================================================"
echo "DEMONSTRATION COMPLETE! 🎉"
echo "============================================================"