#!/usr/bin/env python3
"""
Generate an image using a local ComfyUI server with Brand Compliance, Legal Guardrails, Reporting, and Video Pipeline.
Extended for Creative Automation Pipeline POC.
Usage:
    python comfyui_generate.py --prompt "a cat" --output cat.png
    python comfyui_generate.py --prompt "a cat" --workflow custom.json --output cat.png --compliance-check --legal-check --video
"""
import argparse
import json
import os
import sys
import time
import random
from typing import Any, Dict
import datetime
import logging

# Normalize hyphens in command‑line arguments (fixes copy‑paste of '‑' vs '-')
sys.argv = [arg.replace('‑', '-') for arg in sys.argv]

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level

try:
    import requests
except ImportError:
    log_error("'requests' library not installed. Run: pip install requests")
    sys.exit(1)

# Import compliance modules (optional)
try:
    from brand_compliance import BrandComplianceChecker
    from legal_guardrail import LegalGuardrail
    from reporting import PipelineReporter
    COMPLIANCE_MODULES_AVAILABLE = True
except ImportError as e:
    log_warning(f"Compliance modules not available: {e}")
    log_warning("Install with: pip install -r requirements.txt")
    COMPLIANCE_MODULES_AVAILABLE = False

# Import video pipeline (optional)
try:
    from video_pipeline import VideoPipeline
    VIDEO_PIPELINE_AVAILABLE = True
except ImportError as e:
    log_warning(f"Video pipeline not available: {e}")
    log_warning("Video features will be disabled")
    VIDEO_PIPELINE_AVAILABLE = False

# Import Google Drive integration (optional)
try:
    from google_drive_integration import GoogleDriveIntegration
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError as e:
    log_warning(f"Google Drive integration not available: {e}")
    log_warning("Google Drive upload will be disabled")
    GOOGLE_DRIVE_AVAILABLE = False

# Default paths (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SERVER = "http://127.0.0.1:8188"
DEFAULT_WORKFLOW = os.path.join(SCRIPT_DIR, "../configs/default_workflow.json")
DEFAULT_BRAND_CONFIG = os.path.join(SCRIPT_DIR, "../configs/brand_config.json")
DEFAULT_DB_PATH = os.path.join(SCRIPT_DIR, "../outputs/logs/pipeline_logs.db")
DEFAULT_JSON_REPORT = os.path.join(SCRIPT_DIR, "../outputs/logs/run_report.json")
DEFAULT_SERVICE_ACCOUNT = "~/google_serviceaccount/service_account.json"
DEFAULT_OAUTH_SECRETS = "~/google_oauth_info/client_secrets.json"
DEFAULT_DRIVE_FOLDER_ID = "1XdhY-6U624J_ml-MulmMfhQ5zrn9ja1H"  # creative-automation-pipeline folder

def load_workflow(path: str) -> Dict[str, Any]:
    """Load workflow JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_prompt_node(workflow: Dict[str, Any], target_class: str) -> str:
    """Find the first node ID of a given class type."""
    for node_id, node in workflow.items():
        if node.get("class_type") == target_class:
            return node_id
    raise ValueError(f"No node of class '{target_class}' found in workflow")

def queue_prompt(server: str, workflow: Dict[str, Any]) -> str:
    """Queue the prompt and return the prompt_id."""
    resp = requests.post(f"{server}/prompt", json={"prompt": workflow})
    resp.raise_for_status()
    data = resp.json()
    return data["prompt_id"]

def wait_for_completion(server: str, prompt_id: str, poll_interval: float = 1.0) -> Dict[str, Any]:
    """Poll the history until the prompt completes, then return its output."""
    while True:
        resp = requests.get(f"{server}/history")
        resp.raise_for_status()
        history = resp.json()
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(poll_interval)

def download_image(server: str, filename: str, output_path: str):
    """Download an image from ComfyUI's output directory."""
    # ComfyUI serves images under /view?filename=...&subfolder=...
    resp = requests.get(f"{server}/view?filename={filename}")
    resp.raise_for_status()
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)

def run_compliance_checks(image_path: str, brand_config_path: str, checks: list) -> Dict[str, Any]:
    """Run brand compliance checks on generated image."""
    try:
        checker = BrandComplianceChecker(brand_config_path)
        results = checker.run_compliance_checks(image_path, checks)
        return results
    except Exception as e:
        return {
            "overall_passed": False,
            "reason": f"Compliance check error: {e}",
            "checks": {}
        }

def run_legal_check(text: str, brand_config_path: str) -> Dict[str, Any]:
    """Run legal guardrail check on campaign message."""
    try:
        guardrail = LegalGuardrail(brand_config_path)
        results = guardrail.check_text(text)
        return results
    except Exception as e:
        return {
            "passed": False,
            "reason": f"Legal check error: {e}",
            "matches": []
        }

def log_generation(
    reporter,
    product: str,
    width: int,
    height: int,
    compliance_results: Dict[str, Any],
    legal_results: Dict[str, Any],
    generation_time_ms: int,
    image_path: str,
    campaign_message: str,
    workflow_name: str,
    seed: int
) -> int:
    """Log generation to database."""
    # Determine compliance status
    compliance_passed = compliance_results.get("overall_passed", False)
    legal_passed = legal_results.get("passed", False)
    
    if compliance_passed and legal_passed:
        compliance_status = "PASS"
    elif not compliance_passed and not legal_passed:
        compliance_status = "FAIL_BOTH"
    elif not compliance_passed:
        compliance_status = "FAIL_COMPLIANCE"
    else:
        compliance_status = "FAIL_LEGAL"
    
    checks = compliance_results.get("checks", {})
    
    # Count passed vs total checks
    total_checks = len(checks)
    checks_passed = sum(1 for check in checks.values() if check.get("passed", False))
    
    # Individual check results
    brand_colors_passed = checks.get("brand_colors", {}).get("passed", False) if checks else False
    logo_presence_passed = checks.get("logo_presence", {}).get("passed", False) if checks else False
    legal_check_passed = legal_passed
    
    log_id = reporter.log_generation(
        product=product,
        width=width,
        height=height,
        aspect_ratio=f"{width}:{height}",
        compliance_status=compliance_status,
        generation_time_ms=generation_time_ms,
        image_path=image_path,
        checks_passed=checks_passed,
        total_checks=total_checks,
        brand_colors_passed=brand_colors_passed,
        logo_presence_passed=logo_presence_passed,
        legal_check_passed=legal_check_passed,
        campaign_message=campaign_message,
        workflow_name=workflow_name,
        seed=seed,
        additional_info={
            "compliance_results": compliance_results,
            "legal_results": legal_results
        }
    )
    
    return log_id

def generate_video(
    image_path: str,
    campaign_message: str,
    brand_config_path: str,
    output_dir: str,
    product_name: str,
    target_region: str = "USA",
    target_language: str = None,
    brief_path: str = None
) -> Dict[str, Any]:
    """Generate video with text/logo overlays and voiceover."""
    if not VIDEO_PIPELINE_AVAILABLE:
        return {"success": False, "reason": "Video pipeline not available"}
    
    try:
        # Create output directory
        video_output_dir = os.path.join(output_dir, "video")
        os.makedirs(video_output_dir, exist_ok=True)
        
        # Initialize video pipeline with localization
        pipeline = VideoPipeline(
            brand_config_path, 
            target_region=target_region,
            language_code=target_language
        )
        
        # Step 1: Add text overlay
        text_overlay_path = os.path.join(video_output_dir, f"{product_name}_text_overlay.png")
        pipeline.add_text_overlay(image_path, campaign_message, text_overlay_path)
        
        # Step 2: Add logo overlay
        final_image_path = os.path.join(video_output_dir, f"{product_name}_final.png")
        pipeline.add_logo_overlay(text_overlay_path, final_image_path)
        
        # Step 3: Generate voiceover
        audio_path = os.path.join(video_output_dir, f"{product_name}_voiceover.mp3")
        pipeline.generate_voiceover(campaign_message, audio_path, duration=10)
        
        # Step 4: Create video
        video_path = os.path.join(video_output_dir, f"{product_name}_video.mp4")
        pipeline.create_video(final_image_path, audio_path, video_path)
        
        return {
            "success": True,
            "text_overlay_path": text_overlay_path,
            "final_image_path": final_image_path,
            "audio_path": audio_path,
            "video_path": video_path
        }
        
    except Exception as e:
        return {"success": False, "reason": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Generate an image with ComfyUI (with Compliance, Reporting & Video)")
    parser.add_argument("--prompt", required=True, help="Positive prompt text")
    parser.add_argument("--negative", default="blurry, low quality, watermark, text", help="Negative prompt text")
    parser.add_argument("--output", required=True, help="Output image file path")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help=f"Path to workflow JSON file (default: {DEFAULT_WORKFLOW})")
    parser.add_argument("--server", default=DEFAULT_SERVER, help=f"ComfyUI server URL (default: {DEFAULT_SERVER})")
    parser.add_argument("--width", type=int, default=512, help="Image width (default: 512)")
    parser.add_argument("--height", type=int, default=512, help="Image height (default: 512)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: random if 42)")
    parser.add_argument("--no-photo", action="store_true", help="Disable automatic photographic enhancement")
    
    # Compliance & Reporting arguments
    parser.add_argument("--compliance-check", action="store_true", help="Run brand compliance checks on generated image")
    parser.add_argument("--legal-check", action="store_true", help="Check campaign message for prohibited words")
    parser.add_argument("--brand-config", default=DEFAULT_BRAND_CONFIG, help=f"Path to brand configuration JSON (default: {DEFAULT_BRAND_CONFIG})")
    parser.add_argument("--no-report", action="store_true", help="Skip logging to database/JSON")
    parser.add_argument("--product", default="Unspecified", help="Product name for reporting")
    parser.add_argument("--campaign-message", default="", help="Campaign message for legal check")
    
    # Video pipeline arguments
    parser.add_argument("--video", action="store_true", help="Generate video with text/logo overlays and voiceover")
    parser.add_argument("--video-output-dir", help="Directory for video outputs (default: same as image output dir)")
    parser.add_argument("--voicebox-url", default="http://127.0.0.1:17493", help="Voicebox TTS server URL")
    parser.add_argument("--target-region", default="USA", help="Target region for localization (e.g., USA, Japan, Brazil)")
    parser.add_argument("--target-language", help="Target language code (e.g., en, ja, de). Overrides region-based mapping")
    parser.add_argument("--brief", help="Path to brief.json file (overrides individual campaign arguments)")
    
    # Google Drive upload arguments (cloud storage integration)
    parser.add_argument("--upload-to-drive", action="store_true", help="Upload outputs to Google Drive")
    parser.add_argument("--drive-service-account", default=DEFAULT_SERVICE_ACCOUNT, help=f"Path to Google service account JSON (default: {DEFAULT_SERVICE_ACCOUNT})")
    parser.add_argument("--drive-oauth-secrets", default=DEFAULT_OAUTH_SECRETS, help=f"Path to OAuth client secrets JSON (default: {DEFAULT_OAUTH_SECRETS})")
    parser.add_argument("--drive-oauth-token", default="~/.google_token.json", help="Path to store/load OAuth token (default: ~/.google_token.json)")
    parser.add_argument("--drive-use-oauth", action="store_true", help="Use OAuth authentication instead of service account")
    parser.add_argument("--drive-folder-id", default=DEFAULT_DRIVE_FOLDER_ID, help=f"Google Drive folder ID (default: {DEFAULT_DRIVE_FOLDER_ID})")
    parser.add_argument("--keep-local", action="store_true", default=True, help="Keep local copy of files (always enabled)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output (sets log level to DEBUG)")
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
    
    # Load brief.json if provided (overrides individual arguments)
    if args.brief:
        try:
            with open(args.brief, 'r', encoding='utf-8') as f:
                brief = json.load(f)
            
            # Override arguments with brief values
            if "products" in brief and len(brief["products"]) > 0 and not args.prompt:
                # Generate prompt from first product if prompt not provided
                args.prompt = f"a sleek {brief['products'][0].lower()} on a modern kitchen counter"
            
            if "target_region" in brief:
                args.target_region = brief["target_region"]
            
            if "target_language" in brief:
                args.target_language = brief["target_language"]
            
            if "audience" in brief and not args.campaign_message:
                # Use audience in campaign message if not provided
                pass  # We'll handle this later
            
            if "campaign_message" in brief:
                args.campaign_message = brief["campaign_message"]
            
            if "campaign_video_message" in brief:
                # Store for video generation
                args.campaign_video_message = brief["campaign_video_message"]
            
            log_success(f"Loaded brief from {args.brief}")
            log_info(f"Region: {args.target_region}, Language: {args.target_language or 'auto'}")
            
        except Exception as e:
            log_warning(f"Failed to load brief.json: {e}")
    
    # If using default seed (42), replace with random to avoid cache collisions
    if args.seed == 42:
        args.seed = random.randint(1, 999999999)
    
    # Automatic photographic enhancement (unless --no-photo is given)
    if not args.no_photo:
        photo_positive = ", professional photography, studio lighting, white background, high detail, photorealistic, 8K, sharp focus"
        photo_negative = ", cartoon, drawing, sketch, painting, illustration, CGI, 3D render, line art"
        args.prompt = args.prompt + photo_positive
        args.negative = args.negative + photo_negative
        log_info(f"Enhanced prompt for photorealism (use --no-photo to disable)")
    
    # Legal check (if enabled)
    legal_results = {"passed": True, "matches": []}
    if args.legal_check and COMPLIANCE_MODULES_AVAILABLE:
        log_info("Running legal guardrail check...")
        legal_results = run_legal_check(args.campaign_message or args.prompt, args.brand_config)
        if not legal_results["passed"]:
            log_warning(f"Legal guardrail flagged {len(legal_results.get('matches', []))} prohibited words")
            if legal_results.get("flagged_text"):
                log_info(f"Flagged text: {legal_results['flagged_text'][:200]}...")
            if not args.compliance_check:
                # If only legal check fails, we may still want to generate but warn
                log_warning("Continuing with generation (legal check failure logged)")
        else:
            log_success("Legal check passed")
    
    # Load workflow
    try:
        workflow = load_workflow(args.workflow)
    except FileNotFoundError:
        log_error(f"Workflow file not found: {args.workflow}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in workflow file: {e}")
        sys.exit(1)
    
    # Find positive and negative prompt nodes (assuming they are CLIPTextEncode)
    try:
        pos_node = find_prompt_node(workflow, "CLIPTextEncode")
        # Usually negative is next node ID, but let's search for it
        neg_node = None
        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncode" and node_id != pos_node:
                neg_node = node_id
                break
        if neg_node is None:
            neg_node = pos_node  # fallback
    except ValueError:
        log_error("Could not find CLIPTextEncode nodes in workflow.")
        log_info("Make sure your workflow has at least one CLIPTextEncode node.")
        sys.exit(1)
    
    # Update prompts in workflow
    workflow[pos_node]["inputs"]["text"] = args.prompt
    workflow[neg_node]["inputs"]["text"] = args.negative
    
    # Update latent dimensions if EmptyLatentImage node exists
    for node_id, node in workflow.items():
        if node.get("class_type") == "EmptyLatentImage":
            node["inputs"]["width"] = args.width
            node["inputs"]["height"] = args.height
            break
    
    # Queue prompt and wait
    log_info(f"Queueing prompt to {args.server}...")
    start_time = time.time()
    
    try:
        prompt_id = queue_prompt(args.server, workflow)
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to connect to ComfyUI server at {args.server}")
        log_info("Make sure ComfyUI is running and accessible.")
        log_error(f"Error: {e}")
        sys.exit(1)
    
    log_info(f"Prompt queued with ID: {prompt_id}")
    log_info("Waiting for completion...")
    
    try:
        result = wait_for_completion(args.server, prompt_id)
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to get result from ComfyUI server: {e}")
        sys.exit(1)
    
    generation_time_ms = int((time.time() - start_time) * 1000)
    
    # Download the generated image
    outputs = result.get("outputs", {})
    image_saved = False
    
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                filename = img["filename"]
                subfolder = img.get("subfolder", "")
                full_path = os.path.join(subfolder, filename) if subfolder else filename
                log_info(f"Downloading {full_path}...")
                download_image(args.server, full_path, args.output)
                log_success(f"Saved to {args.output}")
                image_saved = True
                break
        if image_saved:
            break
    
    if not image_saved:
        log_error("No image found in outputs.")
        sys.exit(1)
    
    # Compliance checks (if enabled)
    compliance_results = {"overall_passed": True, "checks": {}}
    if args.compliance_check and COMPLIANCE_MODULES_AVAILABLE:
        log_info("Running brand compliance checks...")
        compliance_results = run_compliance_checks(
            args.output,
            args.brand_config,
            checks=["brand_colors"]
        )
        
        if compliance_results.get("overall_passed"):
            log_success("Brand compliance passed")
        else:
            log_warning("Brand compliance failed")
            for check_name, check_result in compliance_results.get("checks", {}).items():
                if not check_result.get("passed", False):
                    log_info(f"{check_name}: {check_result.get('reason', 'Unknown')}")
    
    # Video generation (if enabled)
    video_results = {"success": False}
    if args.video and VIDEO_PIPELINE_AVAILABLE:
        log_info("\n=== Starting Video Pipeline ===")
        
        # Determine output directory
        video_output_dir = args.video_output_dir or os.path.dirname(args.output)
        
        # Determine which message to use for video
        # Prefer campaign_video_message, then campaign_message, then prompt
        video_message = None
        if hasattr(args, 'campaign_video_message') and args.campaign_video_message:
            video_message = args.campaign_video_message
            log_info("Using campaign_video_message from brief")
        elif args.campaign_message:
            video_message = args.campaign_message
        else:
            video_message = args.prompt
        
        video_results = generate_video(
            image_path=args.output,
            campaign_message=video_message,
            brand_config_path=args.brand_config,
            output_dir=video_output_dir,
            product_name=args.product.replace(" ", "_"),
            target_region=args.target_region,
            target_language=args.target_language if hasattr(args, 'target_language') else None,
            brief_path=args.brief
        )
        
        if video_results.get("success"):
            log_success("Video pipeline completed successfully!")
            log_info(f"Text overlay: {video_results.get('text_overlay_path')}")
            log_info(f"Final image: {video_results.get('final_image_path')}")
            log_info(f"Voiceover: {video_results.get('audio_path')}")
            log_info(f"Video: {video_results.get('video_path')}")
        else:
            log_warning(f"Video pipeline failed: {video_results.get('reason', 'Unknown error')}")
    
    # Log video generation if enabled
    if args.video and not args.no_report and COMPLIANCE_MODULES_AVAILABLE:
        try:
            # Extract brief name from brief path if provided
            brief_name = None
            if args.brief and os.path.exists(args.brief):
                brief_name = os.path.basename(args.brief)
            
            reporter = PipelineReporter(db_path=DEFAULT_DB_PATH, json_log_path=DEFAULT_JSON_REPORT)
            status = "success" if video_results.get("success") else "failed"
            video_log_id = reporter.log_video_generation(
                product=args.product,
                brief_name=brief_name,
                video_path=video_results.get("video_path") if video_results.get("success") else None,
                duration_ms=generation_time_ms,  # Total generation time includes image generation
                width=args.width,
                height=args.height,
                status=status,
                additional_info={
                    "text_overlay_path": video_results.get("text_overlay_path"),
                    "final_image_path": video_results.get("final_image_path"),
                    "audio_path": video_results.get("audio_path"),
                    "generation_time_ms": generation_time_ms,
                    "reason": video_results.get("reason") if not video_results.get("success") else None
                }
            )
            log_success(f"Logged video generation with ID: {video_log_id} (status: {status})")
        except Exception as e:
            log_warning(f"Failed to log video generation: {e}")
    
    # Reporting (if not disabled)
    if not args.no_report and COMPLIANCE_MODULES_AVAILABLE:
        log_info("Logging generation to database...")
        try:
            reporter = PipelineReporter(db_path=DEFAULT_DB_PATH, json_log_path=DEFAULT_JSON_REPORT)
            log_id = log_generation(
                reporter=reporter,
                product=args.product,
                width=args.width,
                height=args.height,
                compliance_results=compliance_results,
                legal_results=legal_results,
                generation_time_ms=generation_time_ms,
                image_path=args.output,
                campaign_message=args.campaign_message or args.prompt,
                workflow_name=os.path.basename(args.workflow),
                seed=args.seed
            )
            log_success(f"Logged generation with ID: {log_id}")
            
            # Print summary stats
            stats = reporter.get_summary_stats()
            log_info(f"Total generations: {stats.get('total_generations', 0)}")
            log_info(f"Compliance pass rate: {stats.get('compliance_pass_rate', 0):.1f}%")
            
        except Exception as e:
            log_warning(f"Failed to log generation: {e}")
    
    # Google Drive upload (if enabled)
    drive_results = {"success": False}
    if args.upload_to_drive and GOOGLE_DRIVE_AVAILABLE:
        log_info("\n=== Uploading to Google Drive ===")
        try:
            # Determine authentication mode
            oauth_secrets = args.drive_oauth_secrets if args.drive_use_oauth else None
            service_account = args.drive_service_account if not args.drive_use_oauth else None
            
            # Initialize Google Drive integration
            drive = GoogleDriveIntegration(
                service_account_file=service_account,
                oauth_client_secrets_file=oauth_secrets,
                oauth_token_file=args.drive_oauth_token,
                folder_id=args.drive_folder_id
            )
            
            # Collect files to upload
            files_to_upload = []
            
            # Main image
            if os.path.exists(args.output):
                files_to_upload.append(args.output)
            
            # Video outputs if generated
            if args.video and video_results.get("success"):
                video_files = [
                    video_results.get("text_overlay_path"),
                    video_results.get("final_image_path"),
                    video_results.get("audio_path"),
                    video_results.get("video_path")
                ]
                for file_path in video_files:
                    if file_path and os.path.exists(file_path):
                        files_to_upload.append(file_path)
            
            # Upload files
            uploaded_files = []
            for file_path in files_to_upload:
                try:
                    file_metadata = drive.upload_file(file_path)
                    uploaded_files.append({
                        'local_path': file_path,
                        'remote_id': file_metadata.get('id'),
                        'link': file_metadata.get('webViewLink')
                    })
                except Exception as e:
                    log_warning(f"Failed to upload {file_path}: {e}")
            
            drive_results = {
                "success": len(uploaded_files) > 0,
                "uploaded_count": len(uploaded_files),
                "uploaded_files": uploaded_files,
                "total_files": len(files_to_upload)
            }
            
            if drive_results["success"]:
                log_success(f"Google Drive upload completed: {drive_results['uploaded_count']}/{drive_results['total_files']} files uploaded")
                for uploaded in uploaded_files:
                    log_info(f"📎 {os.path.basename(uploaded['local_path'])}: {uploaded['link']}")
            else:
                log_warning("Google Drive upload failed or no files were uploaded")
                
        except Exception as e:
            log_warning(f"Google Drive upload failed: {e}")
            drive_results = {"success": False, "error": str(e)}
    elif args.upload_to_drive and not GOOGLE_DRIVE_AVAILABLE:
        log_warning("Google Drive upload requested but Google API libraries not available")
        log_info("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    
    log_success(f"Generation completed in {generation_time_ms}ms")
    log_info(f"Image: {args.output}")
    log_info(f"Dimensions: {args.width}x{args.height}")
    if args.compliance_check:
        log_info(f"Compliance: {'PASS' if compliance_results.get('overall_passed') else 'FAIL'}")
    if args.legal_check:
        log_info(f"Legal: {'PASS' if legal_results.get('passed') else 'FAIL'}")
    if args.video:
        log_info(f"Video: {'SUCCESS' if video_results.get('success') else 'FAILED'}")
    if args.upload_to_drive:
        log_info(f"Google Drive: {'UPLOADED' if drive_results.get('success') else 'FAILED'}")
    
    # Exit with non-zero code if compliance/legal failed and strict mode?
    # For now, just warn.

if __name__ == "__main__":
    main()