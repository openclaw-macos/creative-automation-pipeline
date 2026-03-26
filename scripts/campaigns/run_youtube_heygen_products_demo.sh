#!/bin/bash
# Step 5: YouTube Upload Pipeline - Publish HeyGen avatar products video to YouTube as draft
# Calls run_heygen_products_demo.sh if video not present, generates thumbnails and titles

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
SRC_DIR="$PROJECT_ROOT/src"
CONFIGS_DIR="$PROJECT_ROOT/configs"
OUTPUTS_DIR="$PROJECT_ROOT/outputs"

# Default values
BRIEF_FILE="$CONFIGS_DIR/brief.json"
CLIENT_SECRETS=""
REGENERATE_VIDEO=false
SIMULATE_UPLOAD=false
VERBOSE=false
KEEP_THUMBNAIL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --brief)
            BRIEF_FILE="$2"
            shift 2
            ;;
        --secrets)
            CLIENT_SECRETS="$2"
            shift 2
            ;;
        --regenerate-video)
            REGENERATE_VIDEO=true
            shift
            ;;
        --simulate)
            SIMULATE_UPLOAD=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --keep-thumbnail)
            KEEP_THUMBNAIL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Step 5: Upload HeyGen avatar products video to YouTube as draft"
            echo ""
            echo "Options:"
            echo "  --brief FILE              Path to brief.json (default: configs/brief.json)"
            echo "  --secrets FILE            Path to OAuth client_secrets.json (REQUIRED for real upload)"
            echo "  --regenerate-video        Force regenerate video even if exists"
            echo "  --simulate                Simulate upload without YouTube API (for testing)"
            echo "  --verbose                 Enable verbose output"
            echo "  --keep-thumbnail          Keep generated thumbnail file"
            echo "  --help                    Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --brief configs/brief.json --secrets ~/client_secrets.json"
            echo "  $0 --simulate --verbose (test without YouTube API)"
            echo ""
            echo "Campaign Sequence:"
            echo "  1. ./scripts/campaigns/run_images_demo.sh"
            echo "  2. ./scripts/campaigns/run_video_demo.sh"
            echo "  3. ./scripts/campaigns/run_heygen_demo.sh"
            echo "  4. ./scripts/campaigns/run_heygen_products_demo.sh"
            echo "  5. $0 (this script)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=== Step 5: YouTube Upload Pipeline ==="
echo "Brief file: $BRIEF_FILE"
echo ""

# Check if brief file exists
if [ ! -f "$BRIEF_FILE" ]; then
    echo "❌ Brief file not found: $BRIEF_FILE"
    echo "   Create a brief.json file or specify with --brief"
    exit 1
fi

# Check for client secrets (unless simulating)
if [ "$SIMULATE_UPLOAD" = false ] && [ -z "$CLIENT_SECRETS" ]; then
    echo "❌ OAuth client_secrets.json not specified."
    echo "   Use --secrets to specify path to client_secrets.json"
    echo "   Or use --simulate for testing without YouTube API"
    exit 1
fi

if [ -n "$CLIENT_SECRETS" ] && [ ! -f "$CLIENT_SECRETS" ]; then
    echo "❌ Client secrets file not found: $CLIENT_SECRETS"
    exit 1
fi

# Use virtual environment Python if available
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Step 1: Determine video file path
BRIEF_NAME=$(basename "$BRIEF_FILE" .json)
VIDEO_SEARCH_DIR="$OUTPUTS_DIR/combined"

# Look for existing combined video
EXISTING_VIDEO=""
if [ -d "$VIDEO_SEARCH_DIR" ]; then
    # Look for most recent combined video for this brief
    EXISTING_VIDEO=$(find "$VIDEO_SEARCH_DIR" -name "*${BRIEF_NAME}*combined*.mp4" -type f | sort -r | head -1)
fi

# Also check heygen_products_demo output directory
HEYGEN_PRODUCTS_DIR="$OUTPUTS_DIR/heygen_products"
if [ -z "$EXISTING_VIDEO" ] && [ -d "$HEYGEN_PRODUCTS_DIR" ]; then
    EXISTING_VIDEO=$(find "$HEYGEN_PRODUCTS_DIR" -name "*.mp4" -type f | sort -r | head -1)
fi

# Step 2: Generate video if needed
VIDEO_TO_UPLOAD=""
if [ -n "$EXISTING_VIDEO" ] && [ "$REGENERATE_VIDEO" = false ]; then
    echo "✅ Found existing video: $(basename "$EXISTING_VIDEO")"
    VIDEO_TO_UPLOAD="$EXISTING_VIDEO"
else
    echo "📹 Generating HeyGen avatar products video..."
    echo "   This will run steps 3-4 of the campaign sequence"
    echo ""
    
    # Run the combined video generation
    cd "$PROJECT_ROOT"
    if [ "$VERBOSE" = true ]; then
        ./scripts/campaigns/run_heygen_products_demo.sh \
            --brief "$BRIEF_FILE" \
            --verbose \
            --keep-intermediates
    else
        ./scripts/campaigns/run_heygen_products_demo.sh \
            --brief "$BRIEF_FILE" \
            --keep-intermediates
    fi
    
    # Check for generated video
    if [ $? -eq 0 ]; then
        # Look for the generated video
        GENERATED_VIDEO=$(find "$VIDEO_SEARCH_DIR" -name "*${BRIEF_NAME}*combined*.mp4" -type f | sort -r | head -1)
        if [ -n "$GENERATED_VIDEO" ]; then
            echo "✅ Video generated: $(basename "$GENERATED_VIDEO")"
            VIDEO_TO_UPLOAD="$GENERATED_VIDEO"
        else
            # Try alternative location
            GENERATED_VIDEO=$(find "$HEYGEN_PRODUCTS_DIR" -name "*.mp4" -type f | sort -r | head -1)
            if [ -n "$GENERATED_VIDEO" ]; then
                echo "✅ Video generated: $(basename "$GENERATED_VIDEO")"
                VIDEO_TO_UPLOAD="$GENERATED_VIDEO"
            else
                echo "❌ Could not find generated video"
                exit 1
            fi
        fi
    else
        echo "❌ Video generation failed"
        exit 1
    fi
fi

echo ""
echo "📊 Video ready for YouTube upload:"
echo "   File: $(basename "$VIDEO_TO_UPLOAD")"
echo "   Size: $(du -h "$VIDEO_TO_UPLOAD" | cut -f1)"
echo "   Path: $VIDEO_TO_UPLOAD"
echo ""

# Step 3: Prepare for YouTube upload
echo "🎬 Preparing YouTube upload..."
echo ""

# Build Python command arguments
PYTHON_CMD=(
    "$PYTHON_EXEC" "$SRC_DIR/youtube_upload.py"
    "--video" "$VIDEO_TO_UPLOAD"
    "--brief" "$BRIEF_FILE"
    "--category" "22"
    "--privacy" "private"
)

if [ -n "$CLIENT_SECRETS" ]; then
    PYTHON_CMD+=("--secrets" "$CLIENT_SECRETS")
fi

if [ "$SIMULATE_UPLOAD" = true ]; then
    PYTHON_CMD+=("--simulate")
    echo "⚠️  SIMULATION MODE: No actual YouTube upload will occur"
fi

if [ "$VERBOSE" = true ]; then
    PYTHON_CMD+=("--verbose")
fi

# Add outputs directory for thumbnail generation
PRODUCT_IMAGES_DIR="$OUTPUTS_DIR/images"
if [ -d "$PRODUCT_IMAGES_DIR" ]; then
    PYTHON_CMD+=("--outputs-dir" "$PRODUCT_IMAGES_DIR")
fi

echo "Running YouTube upload script:"
echo "  ${PYTHON_CMD[*]}"
echo ""

# Step 4: Execute YouTube upload
"${PYTHON_CMD[@]}"

UPLOAD_RESULT=$?

echo ""
echo "========================================="

# Step 5: Process result
if [ $UPLOAD_RESULT -eq 0 ]; then
    echo "✅ YouTube Upload Pipeline Completed!"
    echo ""
    
    # Show result file if it exists
    RESULT_FILE="$(dirname "$VIDEO_TO_UPLOAD")/youtube_upload_result.json"
    if [ -f "$RESULT_FILE" ]; then
        echo "📋 Upload Result Summary:"
        echo "   $(cat "$RESULT_FILE" | grep -E 'title|video_id|status|simulated' | sed 's/^/   /')"
        echo "   Full result: $RESULT_FILE"
    fi
    
    echo ""
    echo "🎉 Campaign Sequence Complete!"
    echo ""
    echo "All 5 steps completed successfully:"
    echo "  1. ✅ Images generated (run_images_demo.sh)"
    echo "  2. ✅ Products video created (run_video_demo.sh)"
    echo "  3. ✅ Avatar video generated (run_heygen_demo.sh)"
    echo "  4. ✅ Combined video created (run_heygen_products_demo.sh)"
    echo "  5. ✅ Video uploaded to YouTube as draft (this script)"
    echo ""
    echo "Next steps:"
    echo "  - Review video in YouTube Studio"
    echo "  - Add final touches (description, tags, etc.)"
    echo "  - Change privacy from 'private' to 'public' when ready"
    echo "  - Share your campaign!"
    
else
    echo "❌ YouTube upload failed"
    echo ""
    echo "Troubleshooting tips:"
    echo "  1. Check OAuth credentials are valid"
    echo "  2. Ensure client_secrets.json has correct redirect URIs"
    echo "  3. Try --simulate flag to test without YouTube API"
    echo "  4. Check Python dependencies: pip install google-api-python-client"
    exit 1
fi

# Clean up thumbnail if requested
if [ "$KEEP_THUMBNAIL" = false ]; then
    THUMBNAIL_FILE="$(dirname "$VIDEO_TO_UPLOAD")/youtube_thumbnail.jpg"
    if [ -f "$THUMBNAIL_FILE" ]; then
        rm -f "$THUMBNAIL_FILE"
        echo "🗑️  Cleaned up temporary thumbnail"
    fi
fi

echo ""
echo "========================================="
echo "📁 Output files in: $(dirname "$VIDEO_TO_UPLOAD")/"
echo "📄 YouTube result: $(dirname "$VIDEO_TO_UPLOAD")/youtube_upload_result.json"
echo ""