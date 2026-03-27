#!/usr/bin/env python3
"""
Google Drive Integration for Creative Automation Pipeline.
Uploads generated assets to Google Drive for cloud storage.
Uses service account authentication.
"""
import os
import sys
import json
import mimetypes
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import time
from datetime import datetime

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level

# Try to import Google API libraries
try:
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    log_warning("Google API libraries not available. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

class GoogleDriveIntegration:
    """
    Google Drive integration for uploading generated assets.
    Supports OAuth2 (preferred) or service account authentication.
    """
    
    def __init__(self, service_account_file: str = None, folder_id: str = None,
                 oauth_client_secrets_file: str = None, oauth_token_file: str = None):
        """
        Initialize Google Drive integration.
        
        Args:
            service_account_file: Path to service account JSON file (legacy)
            folder_id: Google Drive folder ID to upload to (default: creative-automation-pipeline folder)
            oauth_client_secrets_file: Path to OAuth client secrets JSON file (preferred)
            oauth_token_file: Path to store/load OAuth token (default: ~/.google_token.json)
        """
        self.service_account_file = service_account_file
        self.oauth_client_secrets_file = oauth_client_secrets_file
        self.oauth_token_file = oauth_token_file or os.path.expanduser("~/.google_token.json")
        self.folder_id = folder_id or "1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"  # Default folder ID from user
        
        # Determine authentication mode
        self.use_oauth = False
        if self.oauth_client_secrets_file:
            self.use_oauth = True
            if not os.path.exists(self.oauth_client_secrets_file):
                raise FileNotFoundError(f"OAuth client secrets file not found: {self.oauth_client_secrets_file}")
        elif not self.service_account_file:
            # Try default service account paths
            default_paths = [
                "~/google_serviceaccount/service_account.json",
                "~/google_serviceaccount/credentials.json",
                "~/google_serviceaccount/google_service_account.json",
            ]
            for path in default_paths:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    self.service_account_file = expanded
                    break
        
        if self.use_oauth:
            # OAuth mode: client secrets must exist
            pass
        elif not self.service_account_file or not os.path.exists(self.service_account_file):
            raise FileNotFoundError(f"Service account file not found: {self.service_account_file}")
        
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive using OAuth2 or service account."""
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not installed")
        
        try:
            if self.use_oauth:
                # OAuth2 authentication flow
                SCOPES = ['https://www.googleapis.com/auth/drive']
                creds = None
                
                # Load existing token if available
                if os.path.exists(self.oauth_token_file):
                    try:
                        creds = Credentials.from_authorized_user_info(
                            json.load(open(self.oauth_token_file)),
                            SCOPES
                        )
                    except Exception as e:
                        log_warning(f"Failed to load OAuth token: {e}")
                
                # If no valid credentials, run the OAuth flow
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.oauth_client_secrets_file, SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    
                    # Save the credentials for future use
                    with open(self.oauth_token_file, 'w') as token:
                        token.write(creds.to_json())
                
                credentials = creds
                log_success(f"Authenticated with Google Drive as: {creds.client_id}")
            else:
                # Service account authentication (legacy)
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                log_success(f"Authenticated with Google Drive as: {credentials.service_account_email}")
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=credentials)
            
        except Exception as e:
            log_error(f"Google Drive authentication failed: {e}")
            raise
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict[str, Any]:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Parent folder ID (defaults to root folder_id)
            
        Returns:
            Dictionary with folder metadata
        """
        if not self.service:
            raise RuntimeError("Google Drive service not initialized")
        
        parent_id = parent_folder_id or self.folder_id
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }
        
        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            log_success(f"Created Google Drive folder: {folder_name} (ID: {folder.get('id')})")
            return folder
            
        except HttpError as e:
            log_error(f"Failed to create folder: {e}")
            raise
    
    def upload_file(self, local_path: str, remote_name: str = None, 
                   parent_folder_id: str = None, mime_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.
        
        Args:
            local_path: Local file path to upload
            remote_name: Name to use in Google Drive (defaults to local filename)
            parent_folder_id: Parent folder ID (defaults to root folder_id)
            mime_type: MIME type (auto-detected if None)
            
        Returns:
            Dictionary with file metadata
        """
        if not self.service:
            raise RuntimeError("Google Drive service not initialized")
        
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        # Use local filename if remote_name not provided
        if remote_name is None:
            remote_name = os.path.basename(local_path)
        
        # Determine MIME type
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(local_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
        
        parent_id = parent_folder_id or self.folder_id
        
        file_metadata = {
            'name': remote_name,
            'parents': [parent_id] if parent_id else []
        }
        
        try:
            media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
            
            log_info(f"Uploading {local_path} to Google Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, webViewLink, mimeType'
            ).execute()
            
            file_size = int(file.get('size', 0))
            log_success(f"Uploaded: {remote_name} ({file_size / 1024:.1f} KB)")
            log_info(f"   Link: {file.get('webViewLink')}")
            
            return file
            
        except HttpError as e:
            log_error(f"Failed to upload {local_path}: {e}")
            raise
    
    def upload_folder(self, local_folder: str, remote_folder_name: str = None,
                     parent_folder_id: str = None) -> Dict[str, Any]:
        """
        Upload entire folder recursively to Google Drive.
        
        Args:
            local_folder: Local folder path to upload
            remote_folder_name: Name to use in Google Drive (defaults to local folder name)
            parent_folder_id: Parent folder ID (defaults to root folder_id)
            
        Returns:
            Dictionary with upload summary
        """
        if not os.path.isdir(local_folder):
            raise NotADirectoryError(f"Not a directory: {local_folder}")
        
        # Create remote folder
        if remote_folder_name is None:
            remote_folder_name = os.path.basename(local_folder.rstrip('/'))
        
        remote_folder = self.create_folder(remote_folder_name, parent_folder_id)
        remote_folder_id = remote_folder.get('id')
        
        uploaded_files = []
        failed_files = []
        
        # Walk through local folder
        for root, dirs, files in os.walk(local_folder):
            # Calculate relative path for Google Drive structure
            rel_path = os.path.relpath(root, local_folder)
            if rel_path == '.':
                current_remote_folder_id = remote_folder_id
            else:
                # Create subfolder in Google Drive
                subfolder_name = os.path.basename(root)
                subfolder = self.create_folder(subfolder_name, remote_folder_id)
                current_remote_folder_id = subfolder.get('id')
            
            # Upload files in current directory
            for filename in files:
                local_file_path = os.path.join(root, filename)
                
                try:
                    # Skip hidden files
                    if filename.startswith('.'):
                        continue
                    
                    file_metadata = self.upload_file(
                        local_file_path,
                        remote_name=filename,
                        parent_folder_id=current_remote_folder_id
                    )
                    uploaded_files.append({
                        'local_path': local_file_path,
                        'remote_id': file_metadata.get('id'),
                        'remote_name': file_metadata.get('name'),
                        'link': file_metadata.get('webViewLink')
                    })
                    
                except Exception as e:
                    log_error(f"Failed to upload {filename}: {e}")
                    failed_files.append({
                        'local_path': local_file_path,
                        'error': str(e)
                    })
        
        return {
            'success': True,
            'remote_folder_id': remote_folder_id,
            'remote_folder_link': remote_folder.get('webViewLink'),
            'uploaded_count': len(uploaded_files),
            'failed_count': len(failed_files),
            'uploaded_files': uploaded_files,
            'failed_files': failed_files
        }
    
    def get_shareable_link(self, file_id: str, permission_type: str = 'anyone',
                          role: str = 'reader') -> str:
        """
        Create a shareable link for a file/folder.
        
        Args:
            file_id: Google Drive file ID
            permission_type: 'anyone', 'user', 'group', 'domain'
            role: 'reader', 'writer', 'commenter'
            
        Returns:
            Shareable link
        """
        if not self.service:
            raise RuntimeError("Google Drive service not initialized")
        
        try:
            # Check if permission already exists
            existing_permissions = self.service.permissions().list(
                fileId=file_id,
                fields='permissions(id, type, role)'
            ).execute()
            
            # Look for existing 'anyone' permission
            for perm in existing_permissions.get('permissions', []):
                if perm.get('type') == permission_type and perm.get('role') == role:
                    # Permission already exists, return existing link
                    file_info = self.service.files().get(
                        fileId=file_id,
                        fields='webViewLink'
                    ).execute()
                    return file_info.get('webViewLink')
            
            # Create new permission
            permission = {
                'type': permission_type,
                'role': role,
            }
            
            if permission_type == 'anyone':
                permission['allowFileDiscovery'] = False
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()
            
            # Get the file with link
            file_info = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return file_info.get('webViewLink')
            
        except HttpError as e:
            log_error(f"Failed to create shareable link: {e}")
            raise
    
    def upload_campaign_outputs(self, campaign_folder: str, 
                               campaign_name: str = None) -> Dict[str, Any]:
        """
        Upload campaign outputs to Google Drive.
        Organized by campaign folder structure.
        
        Args:
            campaign_folder: Local campaign folder path (should contain outputs/)
            campaign_name: Campaign name for Google Drive (defaults to folder name)
            
        Returns:
            Dictionary with upload results
        """
        if not os.path.exists(campaign_folder):
            raise FileNotFoundError(f"Campaign folder not found: {campaign_folder}")
        
        if campaign_name is None:
            campaign_name = os.path.basename(campaign_folder.rstrip('/'))
        
        # Check for outputs folder
        outputs_folder = os.path.join(campaign_folder, 'outputs')
        if not os.path.exists(outputs_folder):
            log_warning(f"No outputs folder found in {campaign_folder}")
            return {'success': False, 'error': 'No outputs folder found'}
        
        log_info(f"Uploading campaign outputs: {campaign_name}")
        log_info(f"Local folder: {campaign_folder}")
        
        # Upload the entire outputs folder
        return self.upload_folder(outputs_folder, f"{campaign_name}_outputs", self.folder_id)


def main():
    """Test Google Drive integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Google Drive integration")
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument("--service-account", help="Path to service account JSON file (legacy)")
    auth_group.add_argument("--oauth-secrets", help="Path to OAuth client secrets JSON file (preferred)")
    parser.add_argument("--oauth-token", default="~/.google_token.json", help="Path to OAuth token file (default: ~/.google_token.json)")
    parser.add_argument("--folder-id", default="1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H", help="Google Drive folder ID")
    parser.add_argument("--upload", help="Local file or folder to upload")
    parser.add_argument("--test-auth", action="store_true", help="Test authentication only")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                       default="INFO", help="Set log level (default: INFO)")
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag or log-level argument
    if args.verbose:
        set_log_level(logging.DEBUG)
        log_debug("Verbose debug output enabled")
    else:
        level = get_log_level(args.log_level)
        set_log_level(level)
        if level <= logging.DEBUG:
            log_debug(f"Log level set to {args.log_level}")
    
    if not GOOGLE_API_AVAILABLE:
        log_error("Google API libraries not installed.")
        log_info("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        sys.exit(1)
    
    try:
        # Initialize Google Drive integration
        drive = GoogleDriveIntegration(
            service_account_file=args.service_account if not args.oauth_secrets else None,
            oauth_client_secrets_file=args.oauth_secrets,
            oauth_token_file=args.oauth_token,
            folder_id=args.folder_id
        )
        
        if args.test_auth:
            log_success("Authentication successful")
            sys.exit(0)
        
        if args.upload:
            if os.path.isfile(args.upload):
                # Upload single file
                result = drive.upload_file(args.upload)
                log_success(f"\nFile uploaded successfully!")
                log_info(f"   ID: {result.get('id')}")
                log_info(f"   Link: {result.get('webViewLink')}")
                
            elif os.path.isdir(args.upload):
                # Upload folder
                result = drive.upload_folder(args.upload)
                log_success(f"\nFolder uploaded successfully!")
                log_info(f"   Uploaded: {result['uploaded_count']} files")
                log_info(f"   Failed: {result['failed_count']} files")
                log_info(f"   Folder link: {result['remote_folder_link']}")
                
            else:
                log_error(f"Path not found: {args.upload}")
                sys.exit(1)
        
        else:
            log_info("\nUsage examples:")
            log_info("  # OAuth2 (preferred, higher quota):")
            log_info("  python google_drive_integration.py --oauth-secrets ~/google_oauth_info/client_secrets.json --upload /path/to/file.jpg")
            log_info("  # Service account (legacy):")
            log_info("  python google_drive_integration.py --service-account ~/google_serviceaccount/service_account.json --upload /path/to/folder")
            log_info("  python google_drive_integration.py --oauth-secrets ~/google_oauth_info/client_secrets.json --test-auth")
    
    except Exception as e:
        log_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()