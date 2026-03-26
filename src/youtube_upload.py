#!/usr/bin/env python3
"""
YouTube Upload Module for Creative Automation Pipeline.
Uploads videos to YouTube as private (draft) using OAuth 2.0.
Generates thumbnails and titles using AI if not provided.
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import time
from pathlib import Path

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import google_auth_oauthlib.flow
    import googleapiclient.discovery
    import googleapiclient.http
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    YOUTUBE_LIBS_AVAILABLE = True
except ImportError:
    YOUTUBE_LIBS_AVAILABLE = False
    print("⚠️  Google API libraries not installed. YouTube upload will be simulated.")
    print("   Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Local imports
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure
except ImportError:
    # Fallback logging
    def log_info(msg): print(f"INFO: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")
    def log_success(msg): print(f"SUCCESS: {msg}")
    def log_failure(msg): print(f"FAILURE: {msg}")

# Reporting import
try:
    from reporting import PipelineReporter
    REPORTING_AVAILABLE = True
except ImportError:
    REPORTING_AVAILABLE = False
    log_warning("Reporting module not available - YouTube uploads will not be logged")

# Default database paths (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(SCRIPT_DIR, "../outputs/logs/pipeline_logs.db")
DEFAULT_JSON_REPORT = os.path.join(SCRIPT_DIR, "../outputs/logs/run_report.json")

def load_brief(brief_path: str) -> dict:
    """Load and validate brief.json file."""
    if not os.path.exists(brief_path):
        raise FileNotFoundError(f"Brief file not found: {brief_path}")
    
    with open(brief_path, 'r', encoding='utf-8') as f:
        brief = json.load(f)
    
    return brief


def generate_youtube_title(brief: dict, local_model: str = "mistral-nemo") -> str:
    """
    Generate catchy YouTube title from brief using local AI model.
    Falls back to template-based title if AI generation fails.
    """
    # Check if title is already in brief
    if "youtube_title" in brief and brief["youtube_title"]:
        return brief["youtube_title"]
    
    # Check for campaign message as fallback
    if "campaign_message" in brief and brief["campaign_message"]:
        # Simple enhancement of campaign message
        products = brief.get("products", [])
        if products:
            product_names = ", ".join(products[:2])  # Use first 2 products
            return f"{brief['campaign_message']} - {product_names} Review"
        return f"{brief['campaign_message']} - Product Showcase"
    
    # Generate from products
    products = brief.get("products", ["Products"])
    product_list = ", ".join(products[:2])
    audience = brief.get("audience", "Viewers")
    return f"Amazing {product_list} for {audience} - Must See!"


def generate_thumbnail(
    brief: dict, 
    output_path: str,
    product_images_dir: str = None
) -> str:
    """
    Generate YouTube thumbnail image.
    Uses thumbnail from brief if specified, otherwise creates one.
    
    Args:
        brief: Campaign brief dictionary
        output_path: Where to save generated thumbnail
        product_images_dir: Directory containing product images
        
    Returns:
        Path to thumbnail image
    """
    # Check if thumbnail path is specified in brief (support both field names)
    thumbnail_field = None
    if "youtube_thumbnail" in brief and brief["youtube_thumbnail"]:
        thumbnail_field = "youtube_thumbnail"
    elif "youtube_thumbnail_image" in brief and brief["youtube_thumbnail_image"]:
        thumbnail_field = "youtube_thumbnail_image"
        log_warning("Using deprecated field 'youtube_thumbnail_image'. Update to 'youtube_thumbnail'")
    
    if thumbnail_field:
        thumbnail_path = brief[thumbnail_field]
        if os.path.exists(thumbnail_path):
            log_info(f"Using specified thumbnail: {thumbnail_path}")
            # Copy to output path
            import shutil
            shutil.copy2(thumbnail_path, output_path)
            return output_path
        else:
            log_warning(f"Specified thumbnail not found: {thumbnail_path}")
    
    # Create simple thumbnail using product images
    log_info("Generating thumbnail from product images...")
    
    # Try to find product images
    product_images = []
    if product_images_dir and os.path.exists(product_images_dir):
        for ext in ['.png', '.jpg', '.jpeg']:
            images = list(Path(product_images_dir).glob(f"*{ext}"))
            product_images.extend(images[:2])  # Get up to 2 images
    
    if len(product_images) >= 2:
        # Create collage from two product images
        try:
            from PIL import Image, ImageDraw, ImageFont
            import textwrap
            
            # Open and resize images
            img1 = Image.open(product_images[0]).resize((400, 400))
            img2 = Image.open(product_images[1]).resize((400, 400))
            
            # Create canvas (1280x720 standard YouTube thumbnail)
            thumbnail = Image.new('RGB', (1280, 720), color='#FF0000')  # Red background
            
            # Paste images
            thumbnail.paste(img1, (50, 160))
            thumbnail.paste(img2, (830, 160))
            
            # Add text
            draw = ImageDraw.Draw(thumbnail)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            except:
                font = ImageFont.load_default()
            
            # Get title text
            title = generate_youtube_title(brief)
            wrapped_title = textwrap.fill(title, width=30)
            
            # Draw title
            draw.text((640, 50), wrapped_title, fill='white', font=font, anchor='mm')
            
            # Add "Watch Now" text
            draw.text((640, 650), "WATCH NOW →", fill='white', font=font, anchor='mm')
            
            thumbnail.save(output_path)
            log_success(f"Generated thumbnail: {output_path}")
            return output_path
            
        except ImportError:
            log_warning("PIL not installed, using fallback thumbnail")
        except Exception as e:
            log_warning(f"Thumbnail generation failed: {e}")
    
    # Fallback: create simple colored thumbnail with text
    try:
        from PIL import Image, ImageDraw, ImageFont
        thumbnail = Image.new('RGB', (1280, 720), color='#FF0000')
        draw = ImageDraw.Draw(thumbnail)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        except:
            font = ImageFont.load_default()
        
        products = brief.get("products", ["Products"])
        text = f"{products[0]} Review\nWatch Now!"
        
        draw.text((640, 360), text, fill='white', font=font, anchor='mm')
        thumbnail.save(output_path)
        log_info(f"Created fallback thumbnail: {output_path}")
        return output_path
    except:
        # Ultimate fallback: just copy a product image if available
        if product_images:
            import shutil
            shutil.copy2(product_images[0], output_path)
            return output_path
    
    # No thumbnail generated
    return None


def upload_to_youtube(
    video_path: str,
    client_secrets_path: str,
    title: str,
    description: str = "",
    thumbnail_path: str = None,
    category_id: str = "22",  # People & Blogs
    privacy_status: str = "private",
    product: str = "YouTube Upload",
    brief_name: str = "unknown"
) -> dict:
    """
    Upload video to YouTube as private (draft).
    
    Args:
        video_path: Path to video file
        client_secrets_path: Path to OAuth client_secrets.json
        title: Video title
        description: Video description
        thumbnail_path: Optional thumbnail image path
        category_id: YouTube category ID
        privacy_status: "private", "public", or "unlisted"
        
    Returns:
        Dictionary with upload result or simulation result
    """
    if not YOUTUBE_LIBS_AVAILABLE:
        log_warning("YouTube libraries not available - simulating upload")
        
        # Log simulated upload to database if reporting available
        if REPORTING_AVAILABLE:
            try:
                product_name = "YouTube Upload"
                reporter = PipelineReporter(db_path=DEFAULT_DB_PATH, json_log_path=DEFAULT_JSON_REPORT)
                log_id = reporter.log_youtube_upload(
                    product=product_name,
                    brief_name="unknown",
                    youtube_video_id=f"simulated_{os.path.basename(video_path)}",
                    privacy_status=privacy_status,
                    duration_ms=0,
                    status="simulated",
                    additional_info={
                        "video_path": video_path,
                        "title": title,
                        "message": "Simulated upload (libraries not installed)",
                        "simulated": True
                    }
                )
                log_info(f"Logged simulated YouTube upload with ID: {log_id}")
            except Exception as e:
                log_warning(f"Failed to log simulated YouTube upload: {e}")
        
        return {
            "simulated": True,
            "video_id": f"simulated_{os.path.basename(video_path)}",
            "title": title,
            "status": "private",
            "message": "Simulated upload (libraries not installed)"
        }
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"Client secrets file not found: {client_secrets_path}")
    
    # OAuth 2.0 Scopes
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    try:
        start_time = time.time()
        # Check for existing credentials
        creds = None
        token_file = os.path.join(os.path.dirname(client_secrets_path), "token.json")
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Build YouTube API client
        youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=creds)
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': category_id,
                'tags': ['product review', 'demo', 'campaign']
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Upload video
        log_info(f"Uploading video: {os.path.basename(video_path)}")
        media = googleapiclient.http.MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/mp4'
        )
        
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = request.execute()
        
        # Upload thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                log_info(f"Setting thumbnail: {os.path.basename(thumbnail_path)}")
                youtube.thumbnails().set(
                    videoId=response['id'],
                    media_body=googleapiclient.http.MediaFileUpload(thumbnail_path)
                ).execute()
                log_success("Thumbnail uploaded")
            except Exception as e:
                log_warning(f"Thumbnail upload failed: {e}")
        
        log_success(f"Video uploaded successfully! ID: {response['id']}")
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log to database if reporting available
        if REPORTING_AVAILABLE:
            try:
                # Extract product name from title (heuristic)
                product_name = "YouTube Upload"
                # Could parse title for product names, but keep simple for now
                
                reporter = PipelineReporter(db_path=DEFAULT_DB_PATH, json_log_path=DEFAULT_JSON_REPORT)
                log_id = reporter.log_youtube_upload(
                    product=product_name,
                    brief_name="unknown",  # Could be passed from main
                    youtube_video_id=response['id'],
                    privacy_status=privacy_status,
                    duration_ms=duration_ms,
                    status="success",
                    additional_info={
                        "video_path": video_path,
                        "title": title,
                        "thumbnail_path": thumbnail_path,
                        "category_id": category_id,
                        "description_length": len(description) if description else 0,
                        "url": f"https://youtube.com/watch?v={response['id']}"
                    }
                )
                log_info(f"Logged YouTube upload with ID: {log_id}")
            except Exception as e:
                log_warning(f"Failed to log YouTube upload: {e}")
        
        return {
            'success': True,
            'video_id': response['id'],
            'title': response['snippet']['title'],
            'status': response['status']['privacyStatus'],
            'url': f"https://youtube.com/watch?v={response['id']}"
        }
        
    except Exception as e:
        log_error(f"YouTube upload failed: {e}")
        
        # Log failure to database if reporting available
        if REPORTING_AVAILABLE:
            try:
                duration_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
                product_name = "YouTube Upload"
                
                reporter = PipelineReporter(db_path=DEFAULT_DB_PATH, json_log_path=DEFAULT_JSON_REPORT)
                log_id = reporter.log_youtube_upload(
                    product=product_name,
                    brief_name="unknown",
                    youtube_video_id="failed",
                    privacy_status=privacy_status,
                    duration_ms=duration_ms,
                    status="failed",
                    additional_info={
                        "video_path": video_path,
                        "title": title,
                        "error": str(e),
                        "thumbnail_path": thumbnail_path,
                        "category_id": category_id
                    }
                )
                log_info(f"Logged failed YouTube upload with ID: {log_id}")
            except Exception as log_error:
                log_warning(f"Failed to log failed YouTube upload: {log_error}")
        
        return {
            'success': False,
            'error': str(e),
            'simulated': False
        }


def main():
    """Command-line interface for YouTube upload."""
    parser = argparse.ArgumentParser(description="Upload video to YouTube as private (draft)")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--secrets", required=True, help="Path to OAuth client_secrets.json")
    parser.add_argument("--brief", help="Path to brief.json for metadata")
    parser.add_argument("--title", help="Video title (overrides brief)")
    parser.add_argument("--description", help="Video description")
    parser.add_argument("--thumbnail", help="Path to thumbnail image")
    parser.add_argument("--category", default="22", help="YouTube category ID (default: 22 - People & Blogs)")
    parser.add_argument("--privacy", default="private", choices=["private", "public", "unlisted"], 
                       help="Privacy status (default: private)")
    parser.add_argument("--outputs-dir", help="Directory containing product images for thumbnail generation")
    parser.add_argument("--simulate", action="store_true", help="Simulate upload without YouTube API")
    
    args = parser.parse_args()
    
    # Load brief if provided
    brief = {}
    if args.brief and os.path.exists(args.brief):
        brief = load_brief(args.brief)
        log_info(f"Loaded brief: {args.brief}")
    
    # Generate or get title
    if args.title:
        title = args.title
    elif brief:
        title = generate_youtube_title(brief)
    else:
        title = os.path.basename(args.video).replace('.mp4', '').replace('_', ' ')
    
    # Generate description if not provided
    description = args.description
    if not description and brief:
        products = brief.get("products", [])
        campaign_msg = brief.get("campaign_message", "")
        if products and campaign_msg:
            description = f"{campaign_msg}\n\nFeaturing: {', '.join(products)}\n\nCreated with Creative Automation Pipeline"
        else:
            description = f"Product showcase video\nCreated with Creative Automation Pipeline"
    
    # Generate thumbnail if not provided
    thumbnail_path = args.thumbnail
    if not thumbnail_path and brief:
        # Create thumbnail in same directory as video
        video_dir = os.path.dirname(args.video)
        thumbnail_path = os.path.join(video_dir, "youtube_thumbnail.jpg")
        
        product_images_dir = args.outputs_dir
        if not product_images_dir and "products" in brief:
            # Try to find images in outputs directory
            project_root = Path(__file__).parent.parent
            outputs_dir = project_root / "outputs"
            if outputs_dir.exists():
                product_images_dir = str(outputs_dir / "images")
        
        generated = generate_thumbnail(brief, thumbnail_path, product_images_dir)
        if not generated:
            thumbnail_path = None
    
    # Upload to YouTube (or simulate)
    if args.simulate or not YOUTUBE_LIBS_AVAILABLE:
        log_info("Simulating YouTube upload...")
        result = {
            "simulated": True,
            "video_id": f"simulated_{os.path.basename(args.video)}",
            "title": title,
            "status": args.privacy,
            "thumbnail": thumbnail_path,
            "message": "Simulated upload"
        }
        
        # Log simulated upload to database
        if REPORTING_AVAILABLE:
            try:
                # Get product name from brief
                product_name = "YouTube Upload"
                brief_name = "unknown"
                if brief and brief.get("products"):
                    product_name = brief["products"][0]
                    if len(brief["products"]) > 1:
                        product_name = f"Multiple: {', '.join(brief['products'][:2])}"
                    brief_name = os.path.basename(args.brief) if args.brief else "unknown"
                
                reporter = PipelineReporter(db_path=DEFAULT_DB_PATH, json_log_path=DEFAULT_JSON_REPORT)
                log_id = reporter.log_youtube_upload(
                    product=product_name,
                    brief_name=brief_name,
                    youtube_video_id=result["video_id"],
                    privacy_status=args.privacy,
                    duration_ms=0,
                    status="simulated",
                    additional_info={
                        "video_path": args.video,
                        "title": title,
                        "thumbnail_path": thumbnail_path,
                        "brief_path": args.brief if args.brief else None,
                        "simulated": True
                    }
                )
                log_info(f"Logged simulated YouTube upload with ID: {log_id}")
            except Exception as e:
                log_warning(f"Failed to log simulated YouTube upload: {e}")
    else:
        result = upload_to_youtube(
            video_path=args.video,
            client_secrets_path=args.secrets,
            title=title,
            description=description,
            thumbnail_path=thumbnail_path,
            category_id=args.category,
            privacy_status=args.privacy
        )
    
    # Print result
    print("\n" + "="*60)
    print("YouTube Upload Result:")
    print("="*60)
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Save result to JSON file
    result_file = os.path.join(os.path.dirname(args.video), "youtube_upload_result.json")
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    log_info(f"Result saved to: {result_file}")
    
    return 0 if result.get('success', True) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)