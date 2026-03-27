#!/bin/bash
# Test Google Drive integration for Creative Automation Pipeline
# Supports both OAuth2 (preferred) and service account authentication

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"

echo "=== Testing Google Drive Integration ==="
echo ""

# Check for authentication files
SERVICE_ACCOUNT="~/google_serviceaccount/service_account.json"
OAUTH_SECRETS="~/google_oauth_info/client_secrets.json"
AUTH_MODE=""

if [ -f "$OAUTH_SECRETS" ]; then
    echo "✅ OAuth client secrets found: $OAUTH_SECRETS"
    echo "   File size: $(wc -c < "$OAUTH_SECRETS") bytes"
    AUTH_MODE="oauth"
elif [ -f "$SERVICE_ACCOUNT" ]; then
    echo "✅ Service account file found: $SERVICE_ACCOUNT"
    echo "   File size: $(wc -c < "$SERVICE_ACCOUNT") bytes"
    AUTH_MODE="service_account"
else
    echo "❌ No authentication files found."
    echo "   Expected one of:"
    echo "     - OAuth client secrets: $OAUTH_SECRETS (preferred, higher quota)"
    echo "     - Service account: $SERVICE_ACCOUNT (legacy)"
    echo "   Please ensure one of these JSON files exists."
    exit 1
fi

# Test Python imports
echo ""
echo "Testing Python imports..."
if [ "$AUTH_MODE" = "oauth" ]; then
    python3 -c "
import sys
sys.path.append('$SRC_DIR')

try:
    from google_drive_integration import GoogleDriveIntegration
    print('✅ GoogleDriveIntegration imports successfully')
    
    # Test initialization (will fail if authentication fails)
    try:
        drive = GoogleDriveIntegration(oauth_client_secrets_file='$OAUTH_SECRETS')
        print('✅ Google Drive authentication successful')
        print(f'   Authenticated via OAuth2')
        
    except Exception as e:
        print(f'❌ Google Drive authentication failed: {e}')
        print('   This may be expected if OAuth token needs first‑time browser flow')
        print('   Run the pipeline with --drive-use-oauth to complete authentication')
        
except ImportError as e:
    print(f'❌ Failed to import GoogleDriveIntegration: {e}')
    print('   Install dependencies with: pip install -r requirements.txt')
    sys.exit(1)
"
else
    python3 -c "
import sys
sys.path.append('$SRC_DIR')

try:
    from google_drive_integration import GoogleDriveIntegration
    print('✅ GoogleDriveIntegration imports successfully')
    
    # Test initialization (will fail if authentication fails)
    try:
        drive = GoogleDriveIntegration(service_account_file='$SERVICE_ACCOUNT')
        print('✅ Google Drive authentication successful')
        print(f'   Authenticated as service account')
        
    except Exception as e:
        print(f'❌ Google Drive authentication failed: {e}')
        print('   This may be expected if the service account lacks permissions')
        
except ImportError as e:
    print(f'❌ Failed to import GoogleDriveIntegration: {e}')
    print('   Install dependencies with: pip install -r requirements.txt')
    sys.exit(1)
"
fi

echo ""
echo "Google Drive Folder: https://drive.google.com/drive/folders/1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"
echo ""
echo "To test full integration:"
if [ "$AUTH_MODE" = "oauth" ]; then
    echo "  1. Run video pipeline with OAuth (first time opens browser):"
    echo "     ./run_video_demo.sh --upload-to-drive --drive-use-oauth"
    echo ""
    echo "  2. Or manually test upload:"
    echo "     python3 src/google_drive_integration.py --oauth-secrets \"$OAUTH_SECRETS\" --test-auth"
else
    echo "  1. Run video pipeline with Google Drive upload:"
    echo "     ./run_video_demo.sh --target-region \"USA\" --upload-to-drive"
    echo ""
    echo "  2. Or manually test upload:"
    echo "     python3 src/google_drive_integration.py --test-auth --service-account \"$SERVICE_ACCOUNT\""
fi
echo ""
echo "Note: The service account or OAuth app needs 'Editor' permission on the Google Drive folder."
echo "      Folder ID: 1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"
echo ""