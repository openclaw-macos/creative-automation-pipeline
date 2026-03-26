#!/bin/bash
# Video Generation Pipeline - Creates video from product images
# Calls run_images_demo.sh if images are not present
# Automatically handles single product (video) vs multi-product (campaign slideshow)
# based on brief.json products array

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
SRC_DIR="$PROJECT_ROOT/src"
OUTPUTS_DIR="$PROJECT_ROOT/outputs"
WORKFLOW="$PROJECT_ROOT/configs/default_workflow.json"
BRAND_CONFIG="$PROJECT_ROOT/configs/brand_config.json"

# Default brief file
BRIEF_FILE="$PROJECT_ROOT/configs/brief.json"
VERBOSE=""

# Google Drive integration flags (infrastructure settings, not campaign content)
UPLOAD_TO_DRIVE=false
DRIVE_SERVICE_ACCOUNT="~/google_serviceaccount/service_account.json"
DRIVE_FOLDER_ID="1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --brief)
            BRIEF_FILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
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
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Video Generation Pipeline - Creates video from product images"
            echo "Automatically handles single product (video) vs multi-product (campaign slideshow)"
            echo ""
            echo "Options:"
            echo "  --brief FILE              Path to brief.json (default: configs/brief.json)"
            echo "  --verbose                 Enable verbose debug output"
            echo "  --upload-to-drive         Enable Google Drive upload"
            echo "  --drive-service-account   Google service account JSON path"
            echo "  --drive-folder-id         Google Drive folder ID for upload"
            echo "  --help                    Show this help"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --brief configs/examples/3_Premium_Personal_Care_Japan/brief.json"
            echo "  $0 --upload-to-drive --drive-service-account ~/google_serviceaccount/service_account.json"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=== Creative Automation Pipeline with Video Demo ==="
echo "Brief file: $BRIEF_FILE"
if [ "$UPLOAD_TO_DRIVE" = true ]; then
    echo "Google Drive Upload: ENABLED"
    echo "  Service Account: $DRIVE_SERVICE_ACCOUNT"
    echo "  Folder ID: $DRIVE_FOLDER_ID"
else
    echo "Google Drive Upload: DISABLED (use --upload-to-drive to enable)"
fi
echo ""

# Function to load brief.json and extract campaign details
load_brief() {
    if [ ! -f "$BRIEF_FILE" ]; then
        echo "❌ Brief file not found: $BRIEF_FILE"
        echo "   Create configs/brief.json with at least: {\"products\": [\"Product Name\"]}"
        exit 1
    fi
    
    echo "Loading campaign brief from: $BRIEF_FILE"
    
    # Extract campaign details using Python
    eval $(python3 -c "
import sys, json
sys.path.append('$SRC_DIR')
try:
    with open('$BRIEF_FILE', 'r', encoding='utf-8') as f:
        brief = json.load(f)
    
    products = brief.get('products', ['Coffee Maker'])
    target_region = brief.get('target_region', 'USA')  # Default to USA if not in brief
    audience = brief.get('audience', 'Young professionals 25-35')
    campaign_message = brief.get('campaign_message', 'Start your day smarter with our kitchen essentials')
    target_language = brief.get('target_language', 'en')
    
    # Use newline for products to avoid space-splitting during eval
    print('PRODUCTS_LIST=\"' + '\\n'.join(products) + '\"')
    # Also keep PRODUCTS as comma-separated for compatibility
    print('PRODUCTS=\"' + ','.join(products) + '\"')
    print('PRODUCT_COUNT=' + str(len(products)))
    print('TARGET_REGION=\"' + target_region.replace('\"', '\\\\\"') + '\"')
    print('AUDIENCE=\"' + audience.replace('\"', '\\\\\"') + '\"')
    print('CAMPAIGN_MESSAGE=\"' + campaign_message.replace('\"', '\\\\\"') + '\"')
    print('TARGET_LANGUAGE=\"' + target_language + '\"')
    
    # Check for campaign_video_message
    if 'campaign_video_message' in brief:
        video_msg = brief['campaign_video_message'].replace('\n', ' ')
        print('CAMPAIGN_VIDEO_MESSAGE=\"' + video_msg.replace('\"', '\\\\\"') + '\"')
        
except Exception as e:
    print('echo \"ERROR loading brief: ' + str(e).replace('\"', '\\\\\"') + '\"; exit 1')
")

    # Set IFS to handle the newline-separated list
    OLD_IFS=$IFS
    IFS=$'\n'
    PRODUCT_ARRAY=($PRODUCTS_LIST)
    IFS=$OLD_IFS
    
    BRIEF_NAME=$(basename "$BRIEF_FILE" .json)
    
    echo "✅ Campaign loaded:"
    echo "   Products: $PRODUCTS"
    echo "   Product count: $PRODUCT_COUNT"
    echo "   Region: $TARGET_REGION (from brief.json)"
    echo "   Audience: $AUDIENCE"
    echo "   Language: $TARGET_LANGUAGE"
    echo ""
}

# Function for single product video (original behavior)
run_single_product_video() {
    local PRODUCT="$1"
    local CAMPAIGN_MESSAGE="$2"
    
    echo "=== Single Product Video Mode ==="
    echo "Product: $PRODUCT"
    echo "Campaign message: $CAMPAIGN_MESSAGE"
    echo "Target region: $TARGET_REGION (from brief.json)"
    echo ""
    
    # Create outputs directory
    mkdir -p "$OUTPUTS_DIR/images"
    mkdir -p "$OUTPUTS_DIR/video"
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
    
    # Check if product image exists (part of campaign sequence)
    CLEAN_NAME=$(echo "$PRODUCT" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
    EXPECTED_IMAGE="$OUTPUTS_DIR/images/${CLEAN_NAME}.png"
    if [ ! -f "$EXPECTED_IMAGE" ]; then
        echo "⚠️  Product image not found: $EXPECTED_IMAGE"
        echo "   This script is part of the campaign sequence:"
        echo "   1. First run: ./scripts/campaigns/run_images_demo.sh"
        echo "   2. Then run: ./scripts/campaigns/run_video_demo.sh"
        echo ""
        echo "   Would you like to continue anyway? (Image will be generated)"
        echo "   Press Enter to continue, or Ctrl+C to run images demo first."
        read -r
    fi
    
    # Run the pipeline with compliance checks and video generation
    echo "Running pipeline with compliance checks and video generation..."
    echo "=============================================================="
    
    # Use virtual environment Python if available
    if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
        PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
    else
        PYTHON_EXEC="python3"
    fi
    
    # Build command arguments (no --target-region flag needed, it's in brief.json)
    CMD_ARGS=(
        "--prompt" "a sleek $PRODUCT on a modern kitchen counter"
        "--output" "$OUTPUTS_DIR/images/${CLEAN_NAME}.png"
        "--workflow" "$WORKFLOW"
        "--product" "$PRODUCT"
        "--campaign-message" "$CAMPAIGN_MESSAGE"
        "--target-language" "$TARGET_LANGUAGE"
        "--compliance-check"
        "--legal-check"
        "--video"
        "--video-output-dir" "$OUTPUTS_DIR"
        "--seed" "42"
    )
    
    # Add Google Drive arguments if enabled
    if [ "$UPLOAD_TO_DRIVE" = true ]; then
        CMD_ARGS+=("--upload-to-drive")
        CMD_ARGS+=("--drive-service-account" "$DRIVE_SERVICE_ACCOUNT")
        CMD_ARGS+=("--drive-folder-id" "$DRIVE_FOLDER_ID")
        CMD_ARGS+=("--keep-local")
    fi

    # Add verbose flag if enabled
    if [ -n "$VERBOSE" ]; then
        CMD_ARGS+=("$VERBOSE")
    fi
    
    # Run the command
    $PYTHON_EXEC "$SRC_DIR/comfyui_generate.py" "${CMD_ARGS[@]}"
    
    echo ""
    echo "========================================="
    echo "Video Demo completed successfully!"
    echo ""
    echo "Outputs:"
    echo "  - Image: $OUTPUTS_DIR/images/${CLEAN_NAME}.png"
    echo "  - Text Overlay: $OUTPUTS_DIR/video/${PRODUCT// /_}_text_overlay.png"
    echo "  - Final Image (with logo): $OUTPUTS_DIR/video/${PRODUCT// /_}_final.png"
    echo "  - Voiceover: $OUTPUTS_DIR/video/${PRODUCT// /_}_voiceover.mp3"
    echo "  - Video: $OUTPUTS_DIR/video/${PRODUCT// /_}_video.mp4"
    echo "  - Database: $PROJECT_ROOT/outputs/logs/pipeline_logs.db"
    echo "  - JSON Report: $PROJECT_ROOT/outputs/logs/run_report.json"
    echo ""
    echo "To view the database, run:"
    echo "  sqlite3 $PROJECT_ROOT/outputs/logs/pipeline_logs.db \"SELECT * FROM generation_logs ORDER BY timestamp DESC LIMIT 5;\""
    echo ""
    echo "To play the video, run:"
    echo "  open $OUTPUTS_DIR/video/${PRODUCT// /_}_video.mp4"
}

# Function for multi-product campaign (slideshow with aspect ratios)
run_multi_product_campaign() {
    echo "=== Multi-Product Campaign Mode ==="
    echo "Products: $PRODUCTS"
    echo "Product count: $PRODUCT_COUNT"
    echo "Campaign message: $CAMPAIGN_MESSAGE"
    echo "Target region: $TARGET_REGION (from brief.json)"
    echo ""
    
    # Set campaign output directory
    CAMPAIGN_OUTPUTS_DIR="$OUTPUTS_DIR/campaign"
    
    # Create outputs directory structure
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/images/base"
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/images/aspect_ratios"
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/images/with_logo"
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/images/with_logo_and_textoverlay"
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/video"
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/audio"
    mkdir -p "$CAMPAIGN_OUTPUTS_DIR/logs"
    
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
    
    # Use virtual environment Python if available
    if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
        PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
    else
        PYTHON_EXEC="python3"
    fi
    
    # Step 1: Generate base images for each product
    echo "=== Step 1: Generating Base Product Images ==="
    BASE_IMAGES=()
    INDEX=1
    
    # Use the PRODUCT_ARRAY already created in load_brief()
    for PRODUCT in "${PRODUCT_ARRAY[@]}"; do
        if [ -z "$PRODUCT" ]; then continue; fi
        echo ""
        echo "Generating image for: $PRODUCT"
        
        # Clean product name for filename
        CLEAN_NAME=$(echo "$PRODUCT" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
        OUTPUT_PATH="$CAMPAIGN_OUTPUTS_DIR/images/base/${CLEAN_NAME}_base.png"
        
        # Generate prompt based on product
        PROMPT="a sleek $PRODUCT on a modern kitchen counter, professional photography, studio lighting"
        
        # Build command arguments (no --target-region flag, from brief.json)
        CMD_ARGS=(
            "--prompt" "$PROMPT"
            "--output" "$OUTPUT_PATH"
            "--workflow" "$WORKFLOW"
            "--product" "$PRODUCT"
            "--campaign-message" "$CAMPAIGN_MESSAGE"
            "--target-language" "$TARGET_LANGUAGE"
            "--compliance-check"
            "--legal-check"
            "--seed" "$INDEX"
        )
        
        # Add Google Drive arguments if enabled
        if [ "$UPLOAD_TO_DRIVE" = true ]; then
            CMD_ARGS+=("--upload-to-drive")
            CMD_ARGS+=("--drive-service-account" "$DRIVE_SERVICE_ACCOUNT")
            CMD_ARGS+=("--drive-folder-id" "$DRIVE_FOLDER_ID")
            CMD_ARGS+=("--keep-local")
        fi
        
        # Run generation (continue even if command fails)
        if ! $PYTHON_EXEC "$SRC_DIR/comfyui_generate.py" "${CMD_ARGS[@]}"; then
            echo "⚠️  Image generation command failed for $PRODUCT (continuing)"
        fi
        
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
    if [ ${#BASE_IMAGES[@]} -gt 0 ]; then
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
            
            ASPECT_ARGS=(
                --image "$BASE_IMAGE"
                --output-dir "$CAMPAIGN_OUTPUTS_DIR/images/aspect_ratios"
                --product "$PRODUCT_NAME"
                --method "center_crop"
            )
            
            $PYTHON_EXEC "$SRC_DIR/aspect_ratio.py" "${ASPECT_ARGS[@]}"
            
            # Add logo to each aspect ratio
            if [ -n "$LOGO_PATH" ] && [ -f "$LOGO_PATH" ]; then
                echo "  Adding logo overlay..."
                
                # Find generated aspect ratio images
                CLEAN_NAME=$(echo "$PRODUCT_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
                
                for RATIO in "1_1" "16_9" "9_16"; do
                    INPUT_IMAGE="$CAMPAIGN_OUTPUTS_DIR/images/aspect_ratios/${CLEAN_NAME}_${RATIO}.png"
                    OUTPUT_IMAGE="$CAMPAIGN_OUTPUTS_DIR/images/with_logo/${CLEAN_NAME}_${RATIO}_with_logo.png"
                    
                    if [ -f "$INPUT_IMAGE" ]; then
                        ASPECT_ARGS2=(
                            --image "$INPUT_IMAGE"
                            --output-dir "$CAMPAIGN_OUTPUTS_DIR/images/with_logo"
                            --product "${CLEAN_NAME}_${RATIO}"
                            --logo "$LOGO_PATH"
                        )
                        
                        $PYTHON_EXEC "$SRC_DIR/aspect_ratio.py" "${ASPECT_ARGS2[@]}"
                        
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
                    INPUT_IMAGE="$CAMPAIGN_OUTPUTS_DIR/images/aspect_ratios/${CLEAN_NAME}_${RATIO}.png"
                    if [ -f "$INPUT_IMAGE" ]; then
                        ALL_IMAGES_WITH_LOGO+=("$INPUT_IMAGE")
                    fi
                done
            fi
        done
        
        echo ""
        echo "✅ Generated ${#ALL_IMAGES_WITH_LOGO[@]} images with aspect ratios"
        
        # Step 2b: Add text overlay to images with logo
        if [ ${#ALL_IMAGES_WITH_LOGO[@]} -gt 0 ]; then
            echo ""
            echo "=== Step 2b: Adding Text Overlay ==="
            
            ALL_IMAGES_WITH_TEXT_OVERLAY=()
            
            echo "Adding text overlay to ${#ALL_IMAGES_WITH_LOGO[@]} images..."
            echo "Campaign message: $CAMPAIGN_MESSAGE"
            
            for LOGO_IMAGE in "${ALL_IMAGES_WITH_LOGO[@]}"; do
                # Get filename and create output path
                FILENAME=$(basename "$LOGO_IMAGE")
                BASE_NAME="${FILENAME%.*}"
                OUTPUT_IMAGE="$CAMPAIGN_OUTPUTS_DIR/images/with_logo_and_textoverlay/${BASE_NAME}_with_text.png"
                
                echo "  Processing: $FILENAME"
                
                # Use Python to add text overlay via video_pipeline
                $PYTHON_EXEC -c "
import sys
import os
sys.path.append('$SRC_DIR')

try:
    from video_pipeline import VideoPipeline
    
    # Initialize video pipeline
    pipeline = VideoPipeline(
        brand_config_path='$BRAND_CONFIG',
        target_region='$TARGET_REGION',
        language_code='$TARGET_LANGUAGE'
    )
    
    # Add text overlay
    result = pipeline.add_text_overlay(
        '$LOGO_IMAGE',
        '$CAMPAIGN_MESSAGE',
        '$OUTPUT_IMAGE'
    )
    
    if os.path.exists('$OUTPUT_IMAGE'):
        print(f'    ✅ Text overlay added: {os.path.basename(\"$OUTPUT_IMAGE\")}')
    else:
        print(f'    ⚠️  Text overlay failed, using original image')
        import shutil
        shutil.copy2('$LOGO_IMAGE', '$OUTPUT_IMAGE')
        
except Exception as e:
    print(f'    ❌ Error adding text overlay: {e}')
    import shutil
    shutil.copy2('$LOGO_IMAGE', '$OUTPUT_IMAGE')
"
                
                if [ -f "$OUTPUT_IMAGE" ]; then
                    ALL_IMAGES_WITH_TEXT_OVERLAY+=("$OUTPUT_IMAGE")
                else
                    # Fallback to original logo image
                    ALL_IMAGES_WITH_TEXT_OVERLAY+=("$LOGO_IMAGE")
                fi
            done
            
            echo ""
            echo "✅ Generated ${#ALL_IMAGES_WITH_TEXT_OVERLAY[@]} images with logo and text overlay"
        fi
        
        # Step 3: Create slideshow video with voiceover and background music
        if [ ${#ALL_IMAGES_WITH_TEXT_OVERLAY[@]} -gt 0 ]; then
            echo ""
            echo "=== Step 3: Creating Campaign Video ==="
            
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
    audio_path = '$CAMPAIGN_OUTPUTS_DIR/audio/campaign_voiceover.mp3'
    print('Generating voiceover...')
    pipeline.generate_voiceover('''$VIDEO_SCRIPT''', audio_path)
    
    # Normalize audio volume if file exists
    if os.path.exists(audio_path):
        import subprocess
        temp_path = audio_path + '.normalized.mp3'
        cmd = ['ffmpeg', '-y', '-i', audio_path, '-af', 'volume=5dB', temp_path]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            os.replace(temp_path, audio_path)
            print(f'✅ Voiceover volume normalized (+5dB)')
        except Exception as e:
            print(f'⚠️  Volume normalization failed: {e}')
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    # Create slideshow video
    video_path = '$CAMPAIGN_OUTPUTS_DIR/video/campaign_slideshow.mp4'
    
    # Get images for slideshow (use 16:9 aspect ratio images if available)
    images = '''${ALL_IMAGES_WITH_TEXT_OVERLAY[*]}'''.split()
    
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
            duration_per_image=10,  # 10 seconds per image (was 5)
            transition_duration=2.0  # 2 second crossfade (was 1.0)
        )
        
        if os.path.exists(video_path):
            print(f'✅ Campaign slideshow video created: {video_path}')
            print(f'   Size: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB')
            print(f'   Images used: {len(slideshow_images)}')
            
            # Log video generation to pipeline database
            try:
                from reporting import PipelineReporter
                import os
                db_path = os.path.join('$PROJECT_ROOT', 'outputs', 'logs', 'pipeline_logs.db')
                json_path = os.path.join('$PROJECT_ROOT', 'outputs', 'logs', 'run_report.json')
                reporter = PipelineReporter(db_path=db_path, json_log_path=json_path)
                log_id = reporter.log_video_generation(
                    product='Multi‑Product Campaign',
                    brief_name='$BRIEF_NAME',
                    video_path=video_path,
                    duration_ms=0,  # Could compute from video length if needed
                    width=1920,
                    height=1080,
                    status='success',
                    additional_info={
                        'slideshow_images': len(slideshow_images),
                        'video_size_mb': os.path.getsize(video_path) / 1024 / 1024,
                        'script_length': len('''$VIDEO_SCRIPT''')
                    }
                )
                print(f'✅ Logged video generation with ID: {log_id}')
            except Exception as e:
                print(f'⚠️  Failed to log video generation: {e}')
        else:
            print(f'❌ Slideshow creation failed')
    else:
        print('❌ No suitable images found for slideshow')
        
except Exception as e:
    print(f'❌ Error creating video: {e}')
    import traceback
    traceback.print_exc()
"
        fi
    fi
    
    echo ""
    echo "=== Campaign Demo Summary ==="
    echo ""
    echo "📁 Outputs generated:"
    echo "  Base images: $CAMPAIGN_OUTPUTS_DIR/images/base/"
    echo "  Aspect ratios: $CAMPAIGN_OUTPUTS_DIR/images/aspect_ratios/"
    echo "  Images with logo: $CAMPAIGN_OUTPUTS_DIR/images/with_logo/"
    echo "  Images with logo and text overlay: $CAMPAIGN_OUTPUTS_DIR/images/with_logo_and_textoverlay/"
    echo "  Audio: $CAMPAIGN_OUTPUTS_DIR/audio/"
    echo "  Video: $CAMPAIGN_OUTPUTS_DIR/video/"
    echo ""
    echo "🎬 Campaign video: $CAMPAIGN_OUTPUTS_DIR/video/campaign_slideshow.mp4"
    echo ""
    echo "To play the video:"
    echo "  open $CAMPAIGN_OUTPUTS_DIR/video/campaign_slideshow.mp4"
    echo ""
    echo "To view all generated images:"
    echo "  ls -la $CAMPAIGN_OUTPUTS_DIR/images/with_logo_and_textoverlay/"
    echo ""
    echo "✅ Campaign demo completed!"
}

# Main execution
echo "=== Creative Automation Pipeline with Video Demo ==="
echo "Brief file: $BRIEF_FILE"
if [ "$UPLOAD_TO_DRIVE" = true ]; then
    echo "Google Drive Upload: ENABLED"
    echo "  Service Account: $DRIVE_SERVICE_ACCOUNT"
    echo "  Folder ID: $DRIVE_FOLDER_ID"
else
    echo "Google Drive Upload: DISABLED (use --upload-to-drive to enable)"
fi
echo ""

# Load campaign brief (target_region comes from brief.json)
load_brief

# Determine mode based on product count
if [ "$PRODUCT_COUNT" -eq 1 ]; then
    # Single product mode
    run_single_product_video "$PRODUCTS" "$CAMPAIGN_MESSAGE"
else
    # Multi-product campaign mode
    run_multi_product_campaign
fi

echo ""
echo "========================================="
echo "✅ Video Pipeline Completed Successfully!"
echo ""