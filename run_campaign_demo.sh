#!/bin/bash
# Complete Campaign Demo for Creative Automation Pipeline
# Generates images for all products in brief.json, creates aspect ratios,
# adds logo overlay, and produces slideshow video with voiceover + background music

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUTS_DIR="$SCRIPT_DIR/outputs/campaign"
WORKFLOW="$SCRIPT_DIR/configs/default_workflow.json"
BRAND_CONFIG="$SCRIPT_DIR/configs/brand_config.json"
BRIEF_FILE="$SCRIPT_DIR/configs/brief.json"

# Default target region
TARGET_REGION="USA"
UPLOAD_TO_DRIVE=false
DRIVE_SERVICE_ACCOUNT="/Users/youee-mac/A42_Folder/google_serviceaccount/service_account.json"
DRIVE_FOLDER_ID="1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target-region)
            TARGET_REGION="$2"
            shift 2
            ;;
        --upload-to-drive)
            UPLOAD_TO_DRIVE=true
            shift
            ;;
        --drive-service-account)
            DRIVE_SERVICE_ACCOUNT="$2"
            shift 2
            ;;
        --drive-folder-id)
            DRIVE_FOLDER_ID="$2"
            shift 2
            ;;
        --brief)
            BRIEF_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--target-region REGION] [--upload-to-drive] [--drive-service-account PATH] [--drive-folder-id ID] [--brief PATH]"
            exit 1
            ;;
    esac
done

echo "=== Creative Automation Pipeline - Complete Campaign Demo ==="
echo "Brief: $BRIEF_FILE"
echo "Target Region: $TARGET_REGION"
if [ "$UPLOAD_TO_DRIVE" = true ]; then
    echo "Google Drive Upload: ENABLED"
    echo "  Service Account: $DRIVE_SERVICE_ACCOUNT"
    echo "  Folder ID: $DRIVE_FOLDER_ID"
else
    echo "Google Drive Upload: DISABLED (use --upload-to-drive to enable)"
fi
echo ""

# Create outputs directory structure
mkdir -p "$OUTPUTS_DIR/images/base"
mkdir -p "$OUTPUTS_DIR/images/aspect_ratios"
mkdir -p "$OUTPUTS_DIR/images/with_logo"
mkdir -p "$OUTPUTS_DIR/video"
mkdir -p "$OUTPUTS_DIR/audio"
mkdir -p "$OUTPUTS_DIR/logs"

# Check if ComfyUI server is running
echo "Checking ComfyUI server connectivity..."
if ! curl -s http://127.0.0.1:8188/prompt > /dev/null; then
    echo "⚠️  ComfyUI server not running at http://127.0.0.1:8188"
    echo "Please start ComfyUI with: cd /path/to/ComfyUI && python main.py --port 8188"
    exit 1
fi
echo "✅ ComfyUI server is accessible"

# Check if Voicebox is running (optional)
echo "Checking Voicebox TTS server..."
if curl -s http://127.0.0.1:17493/health > /dev/null 2>&1; then
    echo "✅ Voicebox server is accessible"
    VOICEBOX_AVAILABLE=true
else
    echo "⚠️  Voicebox server not running at http://127.0.0.1:17493"
    echo "   Video will use silent audio fallback"
    VOICEBOX_AVAILABLE=false
fi

echo ""

# Load brief.json to get campaign details
echo "Loading campaign brief..."
if [ ! -f "$BRIEF_FILE" ]; then
    echo "❌ Brief file not found: $BRIEF_FILE"
    exit 1
fi

# Extract campaign details using Python
CAMPAIGN_DETAILS=$(python3 -c "
import sys, json
sys.path.append('$SRC_DIR')
try:
    with open('$BRIEF_FILE', 'r', encoding='utf-8') as f:
        brief = json.load(f)
    
    products = brief.get('products', ['Coffee Maker'])
    target_region = brief.get('target_region', '$TARGET_REGION')
    audience = brief.get('audience', 'Young professionals 25-35')
    campaign_message = brief.get('campaign_message', 'Start your day smarter with our kitchen essentials')
    target_language = brief.get('target_language', 'en')
    
    print(f'PRODUCTS={','.join(products)}')
    print(f'TARGET_REGION={target_region}')
    print(f'AUDIENCE={audience}')
    print(f'CAMPAIGN_MESSAGE={campaign_message}')
    print(f'TARGET_LANGUAGE={target_language}')
    
    # Check for campaign_video_message
    if 'campaign_video_message' in brief:
        video_msg = brief['campaign_video_message'].replace('\n', ' ')
        print(f'CAMPAIGN_VIDEO_MESSAGE={video_msg}')
        
except Exception as e:
    print(f'ERROR loading brief: {e}')
    sys.exit(1)
")

# Export campaign details
eval "$CAMPAIGN_DETAILS"

echo "✅ Campaign loaded:"
echo "   Products: $PRODUCTS"
echo "   Region: $TARGET_REGION"
echo "   Audience: $AUDIENCE"
echo "   Language: $TARGET_LANGUAGE"
echo ""

# Use virtual environment Python if available
if [ -f "./venv/bin/python" ]; then
    PYTHON_EXEC="./venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Step 1: Generate base images for each product
echo "=== Step 1: Generating Base Product Images ==="
BASE_IMAGES=()
INDEX=1

for PRODUCT in $(echo $PRODUCTS | tr ',' ' '); do
    echo ""
    echo "Generating image for: $PRODUCT"
    
    # Clean product name for filename
    CLEAN_NAME=$(echo "$PRODUCT" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
    OUTPUT_PATH="$OUTPUTS_DIR/images/base/${CLEAN_NAME}_base.png"
    
    # Generate prompt based on product
    PROMPT="a sleek $PRODUCT on a modern kitchen counter, professional photography, studio lighting"
    
    # Build command arguments
    CMD_ARGS=(
        "--prompt" "$PROMPT"
        "--output" "$OUTPUT_PATH"
        "--workflow" "$WORKFLOW"
        "--product" "$PRODUCT"
        "--campaign-message" "$CAMPAIGN_MESSAGE"
        "--target-region" "$TARGET_REGION"
        "--target-language" "$TARGET_LANGUAGE"
        "--compliance-check"
        "--legal-check"
        "--seed" "$INDEX"
        "--no-report"
    )
    
    # Run generation
    $PYTHON_EXEC "$SRC_DIR/comfyui_generate.py" "${CMD_ARGS[@]}"
    
    if [ -f "$OUTPUT_PATH" ]; then
        BASE_IMAGES+=("$OUTPUT_PATH")
        echo "✅ Generated base image: $OUTPUT_PATH"
    else
        echo "❌ Failed to generate image for $PRODUCT"
    fi
    
    INDEX=$((INDEX + 1))
done

echo ""
echo "✅ Generated ${#BASE_IMAGES[@]} base images"

# Step 2: Generate aspect ratios for each base image
echo ""
echo "=== Step 2: Generating Aspect Ratios ==="

# Load logo path from brand config
LOGO_PATH=$(python3 -c "
import sys, json
sys.path.append('$SRC_DIR')
try:
    with open('$BRAND_CONFIG', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(config.get('logo_path', ''))
except:
    print('')
")

ALL_IMAGES_WITH_LOGO=()

for BASE_IMAGE in "${BASE_IMAGES[@]}"; do
    PRODUCT_NAME=$(basename "$BASE_IMAGE" | sed 's/_base\.png//' | tr '_' ' ')
    
    echo ""
    echo "Processing: $PRODUCT_NAME"
    
    # Generate aspect ratios
    echo "  Generating 3 aspect ratios (1:1, 16:9, 9:16)..."
    
    $PYTHON_EXEC "$SRC_DIR/aspect_ratio.py" \
        --image "$BASE_IMAGE" \
        --output-dir "$OUTPUTS_DIR/images/aspect_ratios" \
        --product "$PRODUCT_NAME" \
        --method "center_crop"
    
    # Add logo to each aspect ratio
    if [ -n "$LOGO_PATH" ] && [ -f "$LOGO_PATH" ]; then
        echo "  Adding logo overlay..."
        
        # Find generated aspect ratio images
        CLEAN_NAME=$(echo "$PRODUCT_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
        
        for RATIO in "1_1" "16_9" "9_16"; do
            INPUT_IMAGE="$OUTPUTS_DIR/images/aspect_ratios/${CLEAN_NAME}_${RATIO}.png"
            OUTPUT_IMAGE="$OUTPUTS_DIR/images/with_logo/${CLEAN_NAME}_${RATIO}_with_logo.png"
            
            if [ -f "$INPUT_IMAGE" ]; then
                $PYTHON_EXEC "$SRC_DIR/aspect_ratio.py" \
                    --image "$INPUT_IMAGE" \
                    --output-dir "$OUTPUTS_DIR/images/with_logo" \
                    --product "${CLEAN_NAME}_${RATIO}" \
                    --logo "$LOGO_PATH"
                
                if [ -f "$OUTPUT_IMAGE" ]; then
                    ALL_IMAGES_WITH_LOGO+=("$OUTPUT_IMAGE")
                    echo "    ✅ ${RATIO} with logo: $(basename "$OUTPUT_IMAGE")"
                fi
            fi
        done
    else
        echo "  ⚠️  Logo not found, skipping logo overlay"
        # Add images without logo to the list
        CLEAN_NAME=$(echo "$PRODUCT_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
        for RATIO in "1_1" "16_9" "9_16"; do
            INPUT_IMAGE="$OUTPUTS_DIR/images/aspect_ratios/${CLEAN_NAME}_${RATIO}.png"
            if [ -f "$INPUT_IMAGE" ]; then
                ALL_IMAGES_WITH_LOGO+=("$INPUT_IMAGE")
            fi
        done
    fi
done

echo ""
echo "✅ Generated ${#ALL_IMAGES_WITH_LOGO[@]} images with aspect ratios"

# Step 3: Create slideshow video with voiceover and background music
echo ""
echo "=== Step 3: Creating Campaign Video ==="

if [ ${#ALL_IMAGES_WITH_LOGO[@]} -eq 0 ]; then
    echo "❌ No images available for video creation"
    exit 1
fi

# Use campaign_video_message if available, otherwise use campaign_message
VIDEO_SCRIPT="${CAMPAIGN_VIDEO_MESSAGE:-$CAMPAIGN_MESSAGE}"
echo "Video script length: ${#VIDEO_SCRIPT} characters"

# Create video using Python script
echo "Creating slideshow video..."

$PYTHON_EXEC -c "
import sys
import os
import json
sys.path.append('$SRC_DIR')

try:
    from video_pipeline import VideoPipeline
    
    # Initialize video pipeline
    pipeline = VideoPipeline(
        brand_config_path='$BRAND_CONFIG',
        target_region='$TARGET_REGION',
        language_code='$TARGET_LANGUAGE'
    )
    
    # Generate voiceover
    audio_path = '$OUTPUTS_DIR/audio/campaign_voiceover.mp3'
    print('Generating voiceover...')
    pipeline.generate_voiceover('''$VIDEO_SCRIPT''', audio_path)
    
    # Create slideshow video
    video_path = '$OUTPUTS_DIR/video/campaign_slideshow.mp4'
    
    # Get images for slideshow (use 16:9 aspect ratio images if available)
    images = '''${ALL_IMAGES_WITH_LOGO[*]}'''.split()
    
    # Filter for 16:9 aspect ratio images if we have them
    slideshow_images = []
    for img in images:
        if '16_9' in img:
            slideshow_images.append(img)
    
    # If no 16:9 images, use whatever we have
    if not slideshow_images:
        slideshow_images = images
    
    if slideshow_images:
        print(f'Creating slideshow with {len(slideshow_images)} images...')
        
        # Use create_slideshow method
        result = pipeline.create_slideshow(
            slideshow_images, 
            audio_path, 
            video_path,
            duration_per_image=5,  # 5 seconds per image
            transition_duration=1.0  # 1 second crossfade
        )
        
        if os.path.exists(video_path):
            print(f'✅ Campaign slideshow video created: {video_path}')
            print(f'   Size: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB')
            print(f'   Images used: {len(slideshow_images)}')
        else:
            print(f'❌ Slideshow creation failed')
    else:
        print('❌ No suitable images found for slideshow')
        
except Exception as e:
    print(f'❌ Error creating video: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "=== Campaign Demo Summary ==="
echo ""
echo "📁 Outputs generated:"
echo "  Base images: $OUTPUTS_DIR/images/base/"
echo "  Aspect ratios: $OUTPUTS_DIR/images/aspect_ratios/"
echo "  Images with logo: $OUTPUTS_DIR/images/with_logo/"
echo "  Audio: $OUTPUTS_DIR/audio/"
echo "  Video: $OUTPUTS_DIR/video/"
echo ""
echo "🎬 Campaign video: $OUTPUTS_DIR/video/campaign_slideshow.mp4"
echo ""
echo "To play the video:"
echo "  open $OUTPUTS_DIR/video/campaign_slideshow.mp4"
echo ""
echo "To view all generated images:"
echo "  ls -la $OUTPUTS_DIR/images/with_logo/"
echo ""
echo "✅ Campaign demo completed!"