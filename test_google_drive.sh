#!/bin/bash
# Test Google Drive integration for Creative Automation Pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"

echo "=== Testing Google Drive Integration ==="
echo ""

# Check if service account file exists
SERVICE_ACCOUNT="/Users/youee-mac/A42_Folder/google_serviceaccount/service_account.json"
if [ -f "$SERVICE_ACCOUNT" ]; then
    echo "✅ Service account file found: $SERVICE_ACCOUNT"
    echo "   File size: $(wc -c < "$SERVICE_ACCOUNT") bytes"
else
    echo "❌ Service account file not found: $SERVICE_ACCOUNT"
    echo "   Please ensure the Google Drive API key JSON file exists at this path"
    exit 1
fi

# Test Python imports
echo ""
echo "Testing Python imports..."
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

echo ""
echo "Google Drive Folder: https://drive.google.com/drive/folders/1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"
echo ""
echo "To test full integration:"
echo "  1. Run video pipeline with Google Drive upload:"
echo "     ./run_video_demo.sh --target-region \"USA\" --upload-to-drive"
echo ""
echo "  2. Or manually test upload:"
echo "     python3 src/google_drive_integration.py --test-auth --service-account \"$SERVICE_ACCOUNT\""
echo ""
echo "Note: The service account needs 'Editor' permission on the Google Drive folder."
echo "      Folder ID: 1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"
echo ""