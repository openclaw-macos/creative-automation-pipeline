#!/usr/bin/env python3
"""
Generate an image using a local ComfyUI server with Brand Compliance, Legal Guardrails, and Reporting.
Extended for Creative Automation Pipeline POC.
Usage:
    python comfyui_generate.py --prompt "a cat" --output cat.png
    python comfyui_generate.py --prompt "a cat" --workflow custom.json --output cat.png --compliance-check --legal-check
"""
import argparse
import json
import os
import sys
import time
import random
from typing import Any, Dict
import datetime

# Normalize hyphens in command‑line arguments (fixes copy‑paste of '‑' vs '-')
sys.argv = [arg.replace('‑', '-') for arg in sys.argv]

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not installed. Run: pip install requests")
    sys.exit(1)

# Import compliance modules (optional)
try:
    from brand_compliance import BrandComplianceChecker
    from legal_guardrail import LegalGuardrail
    from reporting import PipelineReporter
    COMPLIANCE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Compliance modules not available: {e}")
    print("  Install with: pip install -r requirements.txt")
    COMPLIANCE_MODULES_AVAILABLE = False

# Default paths (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SERVER = "http://127.0.0.1:8188"
DEFAULT_WORKFLOW = os.path.join(SCRIPT_DIR, "../configs/default_workflow.json")
DEFAULT_BRAND_CONFIG = os.path.join(SCRIPT_DIR, "../configs/brand_config.json")
DEFAULT_DB_PATH = os.path.join(SCRIPT_DIR, "../outputs/pipeline_logs.db")
DEFAULT_JSON_REPORT = os.path.join(SCRIPT_DIR, "../outputs/run_report.json")

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
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)

def run_compliance_checks(image_path: str, brand_config_path: str, checks: list) -> Dict[str, Any]:
    """Run brand compliance checks on generated image."""
    if not COMPLIANCE_MODULES_AVAILABLE:
        return {"overall_passed": False, "reason": "Compliance modules not installed", "checks": {}}
    
    try:
        checker = BrandComplianceChecker(brand_config_path)
        results = checker.run_compliance_checks(image_path, checks)
        return results
    except Exception as e:
        return {"overall_passed": False, "reason": f"Compliance check error: {e}", "checks": {}}

def run_legal_check(campaign_message: str, brand_config_path: str) -> Dict[str, Any]:
    """Check campaign message for prohibited words."""
    if not COMPLIANCE_MODULES_AVAILABLE:
        return {"passed": False, "reason": "Legal guardrail module not installed", "matches": []}
    
    try:
        guardrail = LegalGuardrail(brand_config_path)
        result = guardrail.check_campaign_message(campaign_message)
        return result
    except Exception as e:
        return {"passed": False, "reason": f"Legal check error: {e}", "matches": []}

def log_generation(
    reporter: PipelineReporter,
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
    """Log generation details to database and JSON."""
    aspect_ratio = f"{width}:{height}"
    
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
    
    # Extract check details
    checks = compliance_results.get("checks", {})
    brand_colors_passed = checks.get("brand_colors", {}).get("passed", False)
    logo_presence_passed = checks.get("logo_presence", {}).get("passed", False)
    
    checks_passed = sum(1 for check in checks.values() if check.get("passed", False))
    total_checks = len(checks) if checks else 0
    
    log_id = reporter.log_generation(
        product=product,
        aspect_ratio=aspect_ratio,
        width=width,
        height=height,
        compliance_status=compliance_status,
        generation_time_ms=generation_time_ms,
        image_path=image_path,
        checks_passed=checks_passed,
        total_checks=total_checks,
        brand_colors_passed=brand_colors_passed,
        logo_presence_passed=logo_presence_passed,
        legal_check_passed=legal_passed,
        campaign_message=campaign_message,
        workflow_name=workflow_name,
        seed=seed,
        additional_info={
            "compliance_results": compliance_results,
            "legal_results": legal_results
        }
    )
    
    return log_id

def main():
    parser = argparse.ArgumentParser(description="Generate an image with ComfyUI (with Compliance & Reporting)")
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
    
    args = parser.parse_args()
    
    # If using default seed (42), replace with random to avoid cache collisions
    if args.seed == 42:
        args.seed = random.randint(1, 999999999)
    
    # Automatic photographic enhancement (unless --no-photo is given)
    if not args.no_photo:
        photo_positive = ", professional photography, studio lighting, white background, high detail, photorealistic, 8K, sharp focus"
        photo_negative = ", cartoon, drawing, sketch, painting, illustration, CGI, 3D render, line art"
        args.prompt = args.prompt + photo_positive
        args.negative = args.negative + photo_negative
        print(f"Enhanced prompt for photorealism (use --no-photo to disable)")
    
    # Legal check (if enabled)
    legal_results = {"passed": True, "matches": []}
    if args.legal_check and COMPLIANCE_MODULES_AVAILABLE:
        print("Running legal guardrail check...")
        legal_results = run_legal_check(args.campaign_message or args.prompt, args.brand_config)
        if not legal_results["passed"]:
            print(f"⚠️  Legal guardrail flagged {len(legal_results.get('matches', []))} prohibited words")
            if legal_results.get("flagged_text"):
                print(f"   Flagged text: {legal_results['flagged_text'][:200]}...")
            if not args.compliance_check:
                # If only legal check fails, we may still want to generate but warn
                print("   Continuing with generation (legal check failure logged)")
        else:
            print("✅ Legal check passed")
    
    # Load workflow
    try:
        workflow = load_workflow(args.workflow)
    except FileNotFoundError:
        print(f"ERROR: Workflow file not found: {args.workflow}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in workflow file: {e}")
        sys.exit(1)
    
    # Find positive and negative prompt nodes (assuming they are CLIPTextEncode)
    try:
        pos_node = find_prompt_node(workflow, "CLIPTextEncode")
        # Replace first CLIPTextEncode with positive prompt
        workflow[pos_node]["inputs"]["text"] = args.prompt
        # Try to find a second CLIPTextEncode for negative
        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncode" and node_id != pos_node:
                node["inputs"]["text"] = args.negative
                break
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Make sure the workflow contains CLIPTextEncode nodes.")
        sys.exit(1)
    
    # Update EmptyLatentImage dimensions if present
    for node_id, node in workflow.items():
        if node.get("class_type") == "EmptyLatentImage":
            node["inputs"]["width"] = args.width
            node["inputs"]["height"] = args.height
            break
    
    # Update KSampler seed if present
    for node_id, node in workflow.items():
        if node.get("class_type") == "KSampler":
            node["inputs"]["seed"] = args.seed
            break
    
    print(f"Queueing prompt to {args.server}...")
    start_time = time.time()
    try:
        prompt_id = queue_prompt(args.server, workflow)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to ComfyUI server at {args.server}")
        print("Make sure ComfyUI is running and the port is correct.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Server returned {e.response.status_code}")
        print(e.response.text)
        sys.exit(1)
    
    print(f"Prompt queued with ID: {prompt_id}")
    print("Waiting for completion...")
    
    try:
        result = wait_for_completion(args.server, prompt_id)
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(1)
    
    generation_time_ms = int((time.time() - start_time) * 1000)
    
    # Extract output images
    outputs = result.get("outputs", {})
    if not outputs:
        print("ERROR: No outputs in completed prompt.")
        # Check if the execution was fully cached
        status = result.get("status", {})
        messages = status.get("messages", [])
        cached = any(msg[0] == "execution_cached" and msg[1].get("nodes") for msg in messages)
        if cached:
            print("  The workflow nodes were fully cached by ComfyUI.")
            print("  This can happen when identical inputs are re‑used.")
            print("  Try changing the --seed, --width, --height, or prompt text.")
        print(f"Debug: result keys = {list(result.keys())}")
        if status:
            print(f"Status: {status}")
        sys.exit(1)
    
    # Find the SaveImage node output
    image_saved = False
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                filename = img["filename"]
                subfolder = img.get("subfolder", "")
                full_path = os.path.join(subfolder, filename) if subfolder else filename
                print(f"Downloading {full_path}...")
                download_image(args.server, full_path, args.output)
                print(f"Saved to {args.output}")
                image_saved = True
                break
        if image_saved:
            break
    
    if not image_saved:
        print("ERROR: No image found in outputs.")
        sys.exit(1)
    
    # Compliance checks (if enabled)
    compliance_results = {"overall_passed": True, "checks": {}}
    if args.compliance_check and COMPLIANCE_MODULES_AVAILABLE:
        print("Running brand compliance checks...")
        compliance_results = run_compliance_checks(
            args.output,
            args.brand_config,
            checks=["brand_colors"]
        )
        
        if compliance_results.get("overall_passed"):
            print("✅ Brand compliance passed")
        else:
            print("⚠️  Brand compliance failed")
            for check_name, check_result in compliance_results.get("checks", {}).items():
                if not check_result.get("passed", False):
                    print(f"   {check_name}: {check_result.get('reason', 'Unknown')}")
    
    # Reporting (if not disabled)
    if not args.no_report and COMPLIANCE_MODULES_AVAILABLE:
        print("Logging generation to database...")
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
            print(f"✅ Logged generation with ID: {log_id}")
            
            # Print summary stats
            stats = reporter.get_summary_stats()
            print(f"   Total generations: {stats.get('total_generations', 0)}")
            print(f"   Compliance pass rate: {stats.get('compliance_pass_rate', 0):.1f}%")
            
        except Exception as e:
            print(f"⚠️  Failed to log generation: {e}")
    
    print(f"\n🎉 Generation completed in {generation_time_ms}ms")
    print(f"   Image: {args.output}")
    print(f"   Dimensions: {args.width}x{args.height}")
    if args.compliance_check:
        print(f"   Compliance: {'PASS' if compliance_results.get('overall_passed') else 'FAIL'}")
    if args.legal_check:
        print(f"   Legal: {'PASS' if legal_results.get('passed') else 'FAIL'}")
    
    # Exit with non-zero code if compliance/legal failed and strict mode?
    # For now, just warn.

if __name__ == "__main__":
    main()