#!/bin/bash
# Generate combined video: HeyGen avatar sales pitch + Products video
# Concatenates avatar video (HeyGen digital twin) with products video (run_video_demo.sh output)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
OUTPUTS_DIR="$PROJECT_ROOT/outputs"

# Default values
AVATAR_VIDEO=""
PRODUCTS_VIDEO=""
BRIEF_FILE="$PROJECT_ROOT/configs/brief.json"
OUTPUT_DIR="$OUTPUTS_DIR/combined"
REGENERATE_AVATAR=false
REGENERATE_PRODUCTS=false
KEEP_INTERMEDIATES=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --avatar-video)
            AVATAR_VIDEO="$2"
            shift 2
            ;;
        --products-video)
            PRODUCTS_VIDEO="$2"
            shift 2
            ;;
        --brief)
            BRIEF_FILE="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --regenerate-avatar)
            REGENERATE_AVATAR=true
            shift
            ;;
        --regenerate-products)
            REGENERATE_PRODUCTS=true
            shift
            ;;
        --keep-intermediates)
            KEEP_INTERMEDIATES=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Generate combined video: HeyGen avatar sales pitch + Products video"
            echo ""
            echo "Options:"
            echo "  --avatar-video FILE       Existing avatar video (generate if not provided)"
            echo "  --products-video FILE     Existing products video (generate if not provided)"
            echo "  --brief FILE              Path to brief.json (default: configs/brief.json)"
            echo "  --output-dir DIR          Output directory (default: outputs/combined)"
            echo "  --regenerate-avatar       Force regenerate avatar video even if exists"
            echo "  --regenerate-products     Force regenerate products video even if exists"
            echo "  --keep-intermediates      Keep intermediate video files"
            echo "  --verbose                 Enable verbose output"
            echo "  --help                    Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --brief configs/brief.json"
            echo "  $0 --avatar-video outputs/heygen/brief_avatar.mp4"
            echo "  $0 --regenerate-avatar --regenerate-products"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=== HeyGen Avatar + Products Video Combiner ==="
echo "Brief file: $BRIEF_FILE"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Generate timestamp for outputs
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BRIEF_NAME=$(basename "$BRIEF_FILE" .json)

# Function to check if ffmpeg is available
check_ffmpeg() {
    if ! command -v ffmpeg &> /dev/null; then
        echo "❌ ffmpeg not found. Please install ffmpeg:"
        echo "   macOS: brew install ffmpeg"
        echo "   Ubuntu/Debian: sudo apt install ffmpeg"
        exit 1
    fi
}

# Function to validate video file
validate_video() {
    local video_file="$1"
    local description="$2"
    
    if [ ! -f "$video_file" ]; then
        echo "❌ $description not found: $video_file"
        return 1
    fi
    
    # Check if file is a valid video (basic check)
    if file "$video_file" | grep -q "video"; then
        echo "✅ $description: $video_file"
        return 0
    elif ffprobe "$video_file" 2>&1 | grep -q "Stream.*Video"; then
        echo "✅ $description: $video_file"
        return 0
    else
        echo "⚠️  $description may not be a valid video: $video_file"
        return 0  # Still try to process
    fi
}

# Function to generate avatar video
generate_avatar_video() {
    echo ""
    echo "=== Generating Avatar Video ==="
    
    local avatar_output="$OUTPUT_DIR/${BRIEF_NAME}_avatar_${TIMESTAMP}.mp4"
    
    echo "Running HeyGen avatar generation..."
    echo "  Brief: $BRIEF_FILE"
    echo "  Output: $avatar_output"
    echo ""
    
    # Run consolidated HeyGen script (without --output, script generates its own path)
    cd "$PROJECT_ROOT"
    if [ "$VERBOSE" = true ]; then
        ./scripts/campaigns/run_heygen_demo.sh \
            --brief "$BRIEF_FILE" \
            --verbose 2>&1 | tee "$OUTPUT_DIR/avatar_generation.log"
    else
        ./scripts/campaigns/run_heygen_demo.sh \
            --brief "$BRIEF_FILE" 2>&1 | tee "$OUTPUT_DIR/avatar_generation.log"
    fi
    
    # Find the generated avatar video (run_heygen_demo.sh outputs to outputs/heygen/)
    HEYGEN_OUTPUT_DIR="$OUTPUTS_DIR/heygen"
    GENERATED_AVATAR=$(find "$HEYGEN_OUTPUT_DIR" -name "*${BRIEF_NAME}*avatar*.mp4" -type f | sort -r | head -1)
    
    if [ ${PIPESTATUS[0]} -eq 0 ] && [ -n "$GENERATED_AVATAR" ] && [ -f "$GENERATED_AVATAR" ]; then
        # Copy to our expected location
        cp "$GENERATED_AVATAR" "$avatar_output"
        echo "✅ Avatar video generated: $avatar_output (from $GENERATED_AVATAR)"
        AVATAR_VIDEO="$avatar_output"
    else
        echo "❌ Avatar video generation failed or output not found"
        if [ -f "$OUTPUT_DIR/avatar_generation.log" ]; then
            echo "Log output:"
            tail -20 "$OUTPUT_DIR/avatar_generation.log"
        fi
        echo "Searched in: $HEYGEN_OUTPUT_DIR for *${BRIEF_NAME}*avatar*.mp4"
        exit 1
    fi
}

# Function to generate products video
generate_products_video() {
    echo ""
    echo "=== Generating Products Video ==="
    
    local products_output="$OUTPUT_DIR/${BRIEF_NAME}_products_${TIMESTAMP}.mp4"
    
    echo "Running products video generation..."
    echo "  Brief: $BRIEF_FILE"
    echo "  Output: $products_output"
    echo ""
    
    # Run video demo script (target region comes from brief.json)
    cd "$PROJECT_ROOT"
    if [ "$VERBOSE" = true ]; then
        ./scripts/campaigns/run_video_demo.sh \
            --brief "$BRIEF_FILE" \
            --verbose 2>&1 | tee "$OUTPUT_DIR/products_generation.log"
    else
        ./scripts/campaigns/run_video_demo.sh \
            --brief "$BRIEF_FILE" 2>&1 | tee "$OUTPUT_DIR/products_generation.log"
    fi
    
    # Find the generated video file (run_video_demo.sh outputs to different locations)
    # For single product: outputs/video/Product_Name_video.mp4
    # For multi-product: outputs/campaign/video/campaign_slideshow.mp4
    # We need to locate it and copy to our expected location
    if [ -f "$OUTPUTS_DIR/campaign/video/campaign_slideshow.mp4" ]; then
        # Multi-product campaign
        cp "$OUTPUTS_DIR/campaign/video/campaign_slideshow.mp4" "$products_output"
    else
        # Single product - find the video file
        # Get first product from brief
        FIRST_PRODUCT=$(python3 -c "
import json
with open('$BRIEF_FILE', 'r', encoding='utf-8') as f:
    brief = json.load(f)
products = brief.get('products', ['Coffee Maker'])
print(products[0].replace(' ', '_'))
")
        SINGLE_VIDEO="$OUTPUTS_DIR/video/${FIRST_PRODUCT}_video.mp4"
        if [ -f "$SINGLE_VIDEO" ]; then
            cp "$SINGLE_VIDEO" "$products_output"
        else
            echo "❌ Could not find generated video file"
            echo "   Checked: $OUTPUTS_DIR/campaign/video/campaign_slideshow.mp4"
            echo "   Checked: $SINGLE_VIDEO"
            exit 1
        fi
    fi
    
    if [ ${PIPESTATUS[0]} -eq 0 ] && [ -f "$products_output" ]; then
        echo "✅ Products video generated: $products_output"
        PRODUCTS_VIDEO="$products_output"
    else
        echo "❌ Products video generation failed"
        if [ -f "$OUTPUT_DIR/products_generation.log" ]; then
            echo "Log output:"
            tail -20 "$OUTPUT_DIR/products_generation.log"
        fi
        exit 1
    fi
}

# Function to concatenate videos
concatenate_videos() {
    echo ""
    echo "=== Concatenating Videos ==="
    
    local avatar_video="$1"
    local products_video="$2"
    local output_video="$OUTPUT_DIR/${BRIEF_NAME}_combined_${TIMESTAMP}.mp4"
    
    echo "Avatar video: $avatar_video"
    echo "Products video: $products_video"
    echo "Output: $output_video"
    echo ""
    
    # Check ffmpeg
    check_ffmpeg
    
    # Validate videos
    validate_video "$avatar_video" "Avatar video" || exit 1
    validate_video "$products_video" "Products video" || exit 1
    
    # Create temporary file list for concatenation
    CONCAT_LIST="$OUTPUT_DIR/concat_list.txt"
    echo "file '$avatar_video'" > "$CONCAT_LIST"
    echo "file '$products_video'" >> "$CONCAT_LIST"
    
    echo "Concatenating videos with ffmpeg..."
    echo "  Using concat list:"
    cat "$CONCAT_LIST"
    echo ""
    
    # Check if videos have audio streams
    has_audio_avatar=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$avatar_video" 2>/dev/null | head -1)
    has_audio_products=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$products_video" 2>/dev/null | head -1)
    
    # Prepare and Concatenate Videos
    echo "  Standardizing frame rates and merging segments..."
    
    # We use a complex filter to ensure both videos are normalized to 30fps
    # and have the exact same resolution/codec/pixel format to prevent "freezing"
    # Logic: 
    # [v0][a0] = Avatar processed to 1080p, 30fps, 44.1k Stereo
    # [v1][a1] = Products processed to 1080p, 30fps, 44.1k Stereo
    # Output piped to both the final file and concatenation.log
    
    ffmpeg -hide_banner -loglevel info -y \
      -i "$avatar_video" -i "$products_video" \
      -filter_complex \
      "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p[v0]; \
       [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p[v1]; \
       [0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0]; \
       [1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1]; \
       [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
      -map "[v]" -map "[a]" \
      -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k \
      "$output_video" 2>&1 | tee "$OUTPUT_DIR/concatenation.log"

    # Capture ffmpeg exit status from the pipe
    FFMPEG_EXIT=${PIPESTATUS[0]}

    if [ $FFMPEG_EXIT -eq 0 ] && [ -f "$output_video" ]; then
        echo "✅ Combined video created: $output_video"
        echo "   Log available at: $OUTPUT_DIR/concatenation.log"
        
        # Get video info
        VIDEO_INFO=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 "$output_video")
        IFS=, read -r WIDTH HEIGHT DURATION <<< "$VIDEO_INFO"
        FILE_SIZE_BYTES=$(stat -f%z "$output_video" 2>/dev/null || stat -c%s "$output_video" 2>/dev/null || echo 0)
        echo "  Resolution: ${WIDTH}x${HEIGHT}"
        echo "  Duration: ${DURATION} seconds"
        echo "  File size: $(du -h "$output_video" | cut -f1)"
        
        # Log to database
        echo "  Logging combination to database..."
        python3 -c "
import os, sys, json, time
sys.path.insert(0, '$PROJECT_ROOT/src')
try:
    from reporting import PipelineReporter
    import json as json_module
    
    # Load brief to get product name
    product_name = 'Combined Video'
    try:
        with open('$BRIEF_FILE', 'r') as f:
            brief = json_module.load(f)
            if brief.get('products'):
                product_name = brief['products'][0]
                if len(brief['products']) > 1:
                    product_name = f'Multiple: {\", \".join(brief[\"products\"][:2])}'
    except:
        pass
    
    db_path = os.path.join('$PROJECT_ROOT', 'outputs', 'logs', 'pipeline_logs.db')
    json_path = os.path.join('$PROJECT_ROOT', 'outputs', 'logs', 'run_report.json')
    reporter = PipelineReporter(db_path=db_path, json_log_path=json_path)
    log_id = reporter.log_combination_generation(
        product=product_name,
        brief_name='$BRIEF_NAME',
        output_path='$output_video',
        duration_ms=0,  # Concatenation is fast file copy
        status='success',
        additional_info={
            'avatar_video': '$avatar_video',
            'products_video': '$products_video',
            'width': $WIDTH,
            'height': $HEIGHT,
            'duration_seconds': $DURATION,
            'file_size_bytes': $FILE_SIZE_BYTES,
            'resolution': '${WIDTH}x${HEIGHT}'
        }
    )
    print(f'    ✅ Logged combination with ID: {log_id}')
except Exception as e:
    print(f'    ⚠️  Failed to log combination: {e}')
"
        
        FINAL_OUTPUT="$output_video"
    else
        # Only enter here if the exit code was non-zero
        echo "❌ Concatenation failed with exit code $FFMPEG_EXIT."
        echo "   See log for details: $OUTPUT_DIR/concatenation.log"
        
        # Log failure to database if reporting is available
        if [[ $(type -t log_failure_to_db) == function ]]; then
             log_failure_to_db "$FFMPEG_EXIT" "ffmpeg concatenation failed"
        fi
        
        # Log failure to database
        echo "  Logging failure to database..."
        python3 -c "
import os, sys, json
sys.path.insert(0, '$PROJECT_ROOT/src')
try:
    from reporting import PipelineReporter
    import json as json_module
    
    # Load brief to get product name
    product_name = 'Combined Video'
    try:
        with open('$BRIEF_FILE', 'r') as f:
            brief = json_module.load(f)
            if brief.get('products'):
                product_name = brief['products'][0]
                if len(brief['products']) > 1:
                    product_name = f'Multiple: {\", \".join(brief[\"products\"][:2])}'
    except:
        pass
    
    db_path = os.path.join('$PROJECT_ROOT', 'outputs', 'logs', 'pipeline_logs.db')
    json_path = os.path.join('$PROJECT_ROOT', 'outputs', 'logs', 'run_report.json')
    reporter = PipelineReporter(db_path=db_path, json_log_path=json_path)
    log_id = reporter.log_combination_generation(
        product=product_name,
        brief_name='$BRIEF_NAME',
        output_path='',
        duration_ms=0,
        status='failed',
        additional_info={
            'error': 'Video concatenation failed',
            'avatar_video': '$avatar_video',
            'products_video': '$products_video',
            'concatenation_log': '$OUTPUT_DIR/concatenation.log'
        }
    )
    print(f'    ✅ Logged failure with ID: {log_id}')
except Exception as e:
    print(f'    ⚠️  Failed to log failure: {e}')
"
        exit 1
    fi
    
    # Clean up temporary files
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
    
    # Clean up temporary files
    if [ "$KEEP_INTERMEDIATES" = false ]; then
        rm -f "$CONCAT_LIST"
        echo "  Cleaned up temporary files"
    fi
    
    echo ""
}

# Main execution
echo "Starting combined video generation..."
echo ""

# Step 1: Get or generate avatar video
if [ -n "$AVATAR_VIDEO" ] && [ "$REGENERATE_AVATAR" = false ]; then
    validate_video "$AVATAR_VIDEO" "Provided avatar video" || exit 1
    echo "Using existing avatar video: $AVATAR_VIDEO"
else
    generate_avatar_video
fi

# Step 2: Get or generate products video
if [ -n "$PRODUCTS_VIDEO" ] && [ "$REGENERATE_PRODUCTS" = false ]; then
    validate_video "$PRODUCTS_VIDEO" "Provided products video" || exit 1
    echo "Using existing products video: $PRODUCTS_VIDEO"
else
    generate_products_video
fi

# Step 3: Concatenate videos
concatenate_videos "$AVATAR_VIDEO" "$PRODUCTS_VIDEO"

echo ""
echo "========================================="
echo "✅ Combined Video Generation Completed!"
echo ""
echo "Final output: $FINAL_OUTPUT"
echo ""
echo "To play the video:"
echo "  open \"$FINAL_OUTPUT\""
echo ""
echo "To upload to Google Drive (if configured):"
echo "  python3 $PROJECT_ROOT/src/google_drive_integration.py --upload \"$FINAL_OUTPUT\""
echo ""
echo "Intermediate files:"
if [ "$KEEP_INTERMEDIATES" = true ]; then
    echo "  Avatar video: $AVATAR_VIDEO"
    echo "  Products video: $PRODUCTS_VIDEO"
else
    echo "  (Cleaned up, use --keep-intermediates to preserve)"
fi
echo ""
echo "Log files in: $OUTPUT_DIR/"