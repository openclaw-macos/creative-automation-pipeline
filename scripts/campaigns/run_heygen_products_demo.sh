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
    
    # Run consolidated HeyGen script
    cd "$PROJECT_ROOT"
    ./scripts/campaigns/run_heygen_demo.sh \
        --brief "$BRIEF_FILE" \
        --verbose "$VERBOSE" \
        --output "$avatar_output" 2>&1 | tee "$OUTPUT_DIR/avatar_generation.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ] && [ -f "$avatar_output" ]; then
        echo "✅ Avatar video generated: $avatar_output"
        AVATAR_VIDEO="$avatar_output"
    else
        echo "❌ Avatar video generation failed"
        if [ -f "$OUTPUT_DIR/avatar_generation.log" ]; then
            echo "Log output:"
            tail -20 "$OUTPUT_DIR/avatar_generation.log"
        fi
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
    
    # Extract target region from brief for video demo
    TARGET_REGION=$(python3 -c "
import json
with open('$BRIEF_FILE', 'r', encoding='utf-8') as f:
    brief = json.load(f)
print(brief.get('target_region', 'USA'))
")
    
    # Run video demo script
    cd "$PROJECT_ROOT"
    ./scripts/campaigns/run_video_demo.sh \
        --brief "$BRIEF_FILE" \
        --target-region "$TARGET_REGION" \
        --output "$products_output" 2>&1 | tee "$OUTPUT_DIR/products_generation.log"
    
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
    
    # Concatenate videos (preserve audio streams)
    ffmpeg -f concat -safe 0 -i "$CONCAT_LIST" -c copy "$output_video" 2>&1 | tee "$OUTPUT_DIR/concatenation.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ] && [ -f "$output_video" ]; then
        echo "✅ Videos concatenated successfully: $output_video"
        
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
                    product_name = f'Multiple: {", ".join(brief["products"][:2])}'
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
        echo "❌ Video concatenation failed"
        if [ -f "$OUTPUT_DIR/concatenation.log" ]; then
            echo "Error output:"
            tail -20 "$OUTPUT_DIR/concatenation.log"
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
                    product_name = f'Multiple: {", ".join(brief["products"][:2])}'
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