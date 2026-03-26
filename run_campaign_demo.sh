#!/bin/bash
# Master Campaign Orchestrator - Complete 5-step creative automation pipeline
# Runs all steps sequentially: images → video → avatar → combined → YouTube upload
# Handles errors, provides unified progress tracking, supports simulation mode

set -e
set -u  # Treat unset variables as errors

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
SCRIPTS_DIR="$PROJECT_ROOT/scripts/campaigns"

# Default values
BRIEF_FILE=""
VERBOSE=false
SIMULATE=false
UPLOAD_TO_DRIVE=false
KEEP_INTERMEDIATES=false
DRIVE_SERVICE_ACCOUNT=""
DRIVE_FOLDER_ID=""
HEYGEN_API_KEY=""
CLIENT_SECRETS=""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if terminal supports colors
if [ -t 1 ]; then
    USE_COLORS=true
else
    USE_COLORS=false
fi

# Print colored message (conditional)
print_step() {
    if [ "$USE_COLORS" = true ]; then
        echo -e "${BLUE}▶ $1${NC}"
    else
        echo "▶ $1"
    fi
}

print_success() {
    if [ "$USE_COLORS" = true ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo "✓ $1"
    fi
}

print_warning() {
    if [ "$USE_COLORS" = true ]; then
        echo -e "${YELLOW}⚠ $1${NC}"
    else
        echo "⚠ $1"
    fi
}

print_error() {
    if [ "$USE_COLORS" = true ]; then
        echo -e "${RED}✗ $1${NC}"
    else
        echo "✗ $1"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 --brief <brief.json> [OPTIONS]"
    echo ""
    echo "Complete 5-step creative automation pipeline orchestrator"
    echo ""
    echo "Required:"
    echo "  --brief FILE              Path to campaign brief.json"
    echo ""
    echo "Optional:"
    echo "  --verbose                 Enable verbose output"
    echo "  --simulate                Simulation mode (no real API calls)"
    echo "  --upload-to-drive         Upload outputs to Google Drive"
    echo "  --drive-service-account   Google service account JSON path"
    echo "  --drive-folder-id         Google Drive folder ID"
    echo "  --heygen-api-key          HeyGen API key (for avatar generation)"
    echo "  --client-secrets          OAuth client_secrets.json for YouTube"
    echo "  --keep-intermediates      Keep intermediate files (don't clean up)"
    echo "  --help                    Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --brief configs/brief.json"
    echo "  $0 --brief configs/examples/1_Smart_Kitchen_Essentials_North_America/brief.json --verbose"
    echo "  $0 --brief configs/brief.json --simulate --verbose"
    echo ""
    echo "Pipeline Steps:"
    echo "  1. Image generation (ComfyUI)"
    echo "  2. Products video creation"
    echo "  3. Avatar video generation (HeyGen)"
    echo "  4. Combined video creation"
    echo "  5. YouTube upload (draft)"
    echo ""
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --brief)
                BRIEF_FILE="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --simulate)
                SIMULATE=true
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
            --heygen-api-key)
                HEYGEN_API_KEY="$2"
                shift 2
                ;;
            --client-secrets)
                CLIENT_SECRETS="$2"
                shift 2
                ;;
            --keep-intermediates)
                KEEP_INTERMEDIATES=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required arguments
    if [ -z "$BRIEF_FILE" ]; then
        print_error "Missing required argument: --brief"
        show_usage
        exit 1
    fi
    
    if [ ! -f "$BRIEF_FILE" ]; then
        print_error "Brief file not found: $BRIEF_FILE"
        exit 1
    fi
}

# Run a step with error handling
run_step() {
    local step_num="$1"
    local step_name="$2"
    local command="$3"
    
    echo ""
    print_step "Step ${step_num}: ${step_name}"
    echo "Command: $command"
    echo ""
    
    # Run the command directly (no grep filtering that hides errors)
    if eval "$command"; then
        print_success "Step ${step_num} completed successfully"
        return 0
    else
        local exit_code=$?
        print_error "Step ${step_num} failed with exit code $exit_code"
        return $exit_code
    fi
}

# Build command array safely
build_command() {
    local cmd_array=("$1")
    shift
    local args=("$@")
    
    # Simple string construction for now (compatible with existing run_step)
    local cmd_string="${cmd_array[0]}"
    for arg in "${args[@]}"; do
        cmd_string="$cmd_string \"$arg\""
    done
    echo "$cmd_string"
}

# Main execution
main() {
    local separator="============================================================"
    echo "$separator"
    echo "🎬 Creative Automation Pipeline - Complete Campaign Orchestrator"
    echo "$separator"
    echo "Brief: $BRIEF_FILE"
    echo "Mode: $([ "$SIMULATE" = true ] && echo "Simulation" || echo "Production")"
    echo "Verbose: $([ "$VERBOSE" = true ] && echo "Yes" || echo "No")"
    echo ""
    
    # Start timer
    START_TIME=$(date +%s)
    
    # Step 1: Image Generation
    local step1_args=()
    step1_args+=("./scripts/campaigns/run_images_demo.sh")
    step1_args+=("--brief" "$BRIEF_FILE")
    if [ "$VERBOSE" = true ]; then
        step1_args+=("--verbose")
    fi
    # Image generation is local (ComfyUI), so we run it even in simulation mode
    # Note: We don't add simulation-specific flags as they may not be supported
    if [ "$UPLOAD_TO_DRIVE" = true ] && [ "$SIMULATE" = false ]; then
        step1_args+=("--upload-to-drive")
        if [ -n "$DRIVE_SERVICE_ACCOUNT" ]; then
            step1_args+=("--drive-service-account" "$DRIVE_SERVICE_ACCOUNT")
        fi
        if [ -n "$DRIVE_FOLDER_ID" ]; then
            step1_args+=("--drive-folder-id" "$DRIVE_FOLDER_ID")
        fi
    fi
    
    STEP1_CMD=$(build_command "${step1_args[@]}")
    run_step 1 "Image Generation" "$STEP1_CMD" || {
        print_error "Pipeline stopped at Step 1"
        exit 1
    }
    
    # Step 2: Products Video Creation
    local step2_args=()
    step2_args+=("./scripts/campaigns/run_video_demo.sh")
    step2_args+=("--brief" "$BRIEF_FILE")
    if [ "$VERBOSE" = true ]; then
        step2_args+=("--verbose")
    fi
    if [ "$UPLOAD_TO_DRIVE" = true ] && [ "$SIMULATE" = false ]; then
        step2_args+=("--upload-to-drive")
        if [ -n "$DRIVE_SERVICE_ACCOUNT" ]; then
            step2_args+=("--drive-service-account" "$DRIVE_SERVICE_ACCOUNT")
        fi
        if [ -n "$DRIVE_FOLDER_ID" ]; then
            step2_args+=("--drive-folder-id" "$DRIVE_FOLDER_ID")
        fi
    fi
    
    STEP2_CMD=$(build_command "${step2_args[@]}")
    run_step 2 "Products Video Creation" "$STEP2_CMD" || {
        print_error "Pipeline stopped at Step 2"
        exit 1
    }
    
    # Step 3: Avatar Video Generation (HeyGen)
    local step3_args=()
    step3_args+=("./scripts/campaigns/run_heygen_demo.sh")
    step3_args+=("--brief" "$BRIEF_FILE")
    if [ "$VERBOSE" = true ]; then
        step3_args+=("--verbose")
    fi
    # HeyGen flag handling: Default is mock/offline
    # In simulation mode: keep default (mock) - don't add any flags
    # In production mode: add API key if provided
    if [ "$SIMULATE" = false ] && [ -n "$HEYGEN_API_KEY" ]; then
        step3_args+=("--api-key" "$HEYGEN_API_KEY")
    fi
    # Note: We don't add --use-real-translation in either mode
    # because default is mock/offline (safe for simulation)
    # and real translation requires explicit user request
    
    STEP3_CMD=$(build_command "${step3_args[@]}")
    run_step 3 "Avatar Video Generation" "$STEP3_CMD" || {
        print_error "Pipeline stopped at Step 3"
        exit 1
    }
    
    # Step 4: Combined Video Creation
    local step4_args=()
    step4_args+=("./scripts/campaigns/run_heygen_products_demo.sh")
    step4_args+=("--brief" "$BRIEF_FILE")
    if [ "$VERBOSE" = true ]; then
        step4_args+=("--verbose")
    fi
    if [ "$KEEP_INTERMEDIATES" = true ]; then
        step4_args+=("--keep-intermediates")
    fi
    # In simulation mode, we can't actually combine videos, but script handles gracefully
    
    STEP4_CMD=$(build_command "${step4_args[@]}")
    run_step 4 "Combined Video Creation" "$STEP4_CMD" || {
        print_error "Pipeline stopped at Step 4"
        exit 1
    }
    
    # Step 5: YouTube Upload
    local step5_args=()
    step5_args+=("./scripts/campaigns/run_youtube_heygen_products_demo.sh")
    step5_args+=("--brief" "$BRIEF_FILE")
    if [ "$VERBOSE" = true ]; then
        step5_args+=("--verbose")
    fi
    if [ -n "$CLIENT_SECRETS" ]; then
        step5_args+=("--secrets" "$CLIENT_SECRETS")
    fi
    if [ "$SIMULATE" = true ]; then
        step5_args+=("--simulate")
    fi
    
    STEP5_CMD=$(build_command "${step5_args[@]}")
    run_step 5 "YouTube Upload" "$STEP5_CMD" || {
        print_error "Pipeline stopped at Step 5"
        exit 1
    }
    
    # Calculate total duration
    END_TIME=$(date +%s)
    TOTAL_DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "$separator"
    print_success "All 5 steps completed successfully!"
    echo "$separator"
    echo ""
    echo "📊 Campaign Summary:"
    echo "  • Brief: $(basename "$BRIEF_FILE")"
    echo "  • Total duration: ${TOTAL_DURATION} seconds"
    echo "  • Mode: $([ "$SIMULATE" = true ] && echo "Simulation" || echo "Production")"
    echo ""
    echo "📁 Outputs generated:"
    echo "  • Images: outputs/images/"
    echo "  • Videos: outputs/video/ or outputs/campaign/"
    echo "  • Avatar videos: outputs/heygen/"
    echo "  • Combined videos: outputs/combined/"
    echo "  • Database logs: outputs/logs/pipeline_logs.db"
    echo ""
    
    # Show database query suggestion
    if [ -f "outputs/logs/pipeline_logs.db" ]; then
        echo "📈 To view pipeline logs:"
        echo "  sqlite3 outputs/logs/pipeline_logs.db \"SELECT stage, product, status FROM generation_logs ORDER BY timestamp DESC LIMIT 5;\""
    fi
    
    echo ""
    echo "✅ Campaign pipeline complete!"
}

# Execute
parse_args "$@"
main