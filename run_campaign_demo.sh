#!/bin/bash
# Master Campaign Orchestrator - Complete 5-step creative automation pipeline
# Runs all steps sequentially: images → video → avatar → combined → YouTube upload
# Handles errors, provides unified progress tracking, supports simulation mode

set -e

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

# Print colored message
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
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
    
    if [ "$VERBOSE" = true ]; then
        eval "$command"
    else
        eval "$command" 2>&1 | grep -E "(✅|❌|⚠️|Running|Generating|Creating|Uploading|Step|Complete|Finished)" || true
    fi
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        print_success "Step ${step_num} completed successfully"
        return 0
    else
        print_error "Step ${step_num} failed with exit code $exit_code"
        return $exit_code
    fi
}

# Main execution
main() {
    echo "============================================================"
    echo "🎬 Creative Automation Pipeline - Complete Campaign Orchestrator"
    echo "============================================================"
    echo "Brief: $BRIEF_FILE"
    echo "Mode: $([ "$SIMULATE" = true ] && echo "Simulation" || echo "Production")"
    echo "Verbose: $([ "$VERBOSE" = true ] && echo "Yes" || echo "No")"
    echo ""
    
    # Start timer
    START_TIME=$(date +%s)
    
    # Step 1: Image Generation
    STEP1_CMD="./scripts/campaigns/run_images_demo.sh --brief \"$BRIEF_FILE\""
    if [ "$VERBOSE" = true ]; then
        STEP1_CMD="$STEP1_CMD --verbose"
    fi
    if [ "$UPLOAD_TO_DRIVE" = true ]; then
        STEP1_CMD="$STEP1_CMD --upload-to-drive"
        if [ -n "$DRIVE_SERVICE_ACCOUNT" ]; then
            STEP1_CMD="$STEP1_CMD --drive-service-account \"$DRIVE_SERVICE_ACCOUNT\""
        fi
        if [ -n "$DRIVE_FOLDER_ID" ]; then
            STEP1_CMD="$STEP1_CMD --drive-folder-id \"$DRIVE_FOLDER_ID\""
        fi
    fi
    run_step 1 "Image Generation" "$STEP1_CMD" || {
        print_error "Pipeline stopped at Step 1"
        exit 1
    }
    
    # Step 2: Products Video Creation
    STEP2_CMD="./scripts/campaigns/run_video_demo.sh --brief \"$BRIEF_FILE\""
    if [ "$VERBOSE" = true ]; then
        STEP2_CMD="$STEP2_CMD --verbose"
    fi
    if [ "$UPLOAD_TO_DRIVE" = true ]; then
        STEP2_CMD="$STEP2_CMD --upload-to-drive"
        if [ -n "$DRIVE_SERVICE_ACCOUNT" ]; then
            STEP2_CMD="$STEP2_CMD --drive-service-account \"$DRIVE_SERVICE_ACCOUNT\""
        fi
        if [ -n "$DRIVE_FOLDER_ID" ]; then
            STEP2_CMD="$STEP2_CMD --drive-folder-id \"$DRIVE_FOLDER_ID\""
        fi
    fi
    run_step 2 "Products Video Creation" "$STEP2_CMD" || {
        print_error "Pipeline stopped at Step 2"
        exit 1
    }
    
    # Step 3: Avatar Video Generation (HeyGen)
    STEP3_CMD="./scripts/campaigns/run_heygen_demo.sh --brief \"$BRIEF_FILE\""
    if [ "$VERBOSE" = true ]; then
        STEP3_CMD="$STEP3_CMD --verbose"
    fi
    if [ -n "$HEYGEN_API_KEY" ]; then
        STEP3_CMD="$STEP3_CMD --api-key \"$HEYGEN_API_KEY\""
    fi
    if [ "$SIMULATE" = true ]; then
        STEP3_CMD="$STEP3_CMD --use-real-translation false"
    fi
    run_step 3 "Avatar Video Generation" "$STEP3_CMD" || {
        print_error "Pipeline stopped at Step 3"
        exit 1
    }
    
    # Step 4: Combined Video Creation
    STEP4_CMD="./scripts/campaigns/run_heygen_products_demo.sh --brief \"$BRIEF_FILE\""
    if [ "$VERBOSE" = true ]; then
        STEP4_CMD="$STEP4_CMD --verbose"
    fi
    if [ "$KEEP_INTERMEDIATES" = true ]; then
        STEP4_CMD="$STEP4_CMD --keep-intermediates"
    fi
    run_step 4 "Combined Video Creation" "$STEP4_CMD" || {
        print_error "Pipeline stopped at Step 4"
        exit 1
    }
    
    # Step 5: YouTube Upload
    STEP5_CMD="./scripts/campaigns/run_youtube_heygen_products_demo.sh --brief \"$BRIEF_FILE\""
    if [ "$VERBOSE" = true ]; then
        STEP5_CMD="$STEP5_CMD --verbose"
    fi
    if [ -n "$CLIENT_SECRETS" ]; then
        STEP5_CMD="$STEP5_CMD --secrets \"$CLIENT_SECRETS\""
    fi
    if [ "$SIMULATE" = true ]; then
        STEP5_CMD="$STEP5_CMD --simulate"
    fi
    run_step 5 "YouTube Upload" "$STEP5_CMD" || {
        print_error "Pipeline stopped at Step 5"
        exit 1
    }
    
    # Calculate total duration
    END_TIME=$(date +%s)
    TOTAL_DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "============================================================"
    print_success "All 5 steps completed successfully!"
    echo "============================================================"
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