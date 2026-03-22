#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Simulate sys.argv with Unicode hyphen
sys.argv = ['comfyui_generate.py', '--prompt', 'test', '--no‑photo', '--output', 'test.png']

# Import the module's main function but we'll just check parsing
import comfyui_generate as mod

# Monkey-patch the main function to just print args
original_main = mod.main
def test_main():
    parser = mod.argparse.ArgumentParser(description="Generate an image with ComfyUI")
    parser.add_argument("--prompt", required=True, help="Positive prompt text")
    parser.add_argument("--negative", default="blurry, low quality, watermark, text", help="Negative prompt text")
    parser.add_argument("--output", required=True, help="Output image file path")
    parser.add_argument("--workflow", default=mod.DEFAULT_WORKFLOW, help="Path to workflow JSON file")
    parser.add_argument("--server", default=mod.DEFAULT_SERVER, help=f"ComfyUI server URL (default: {mod.DEFAULT_SERVER})")
    parser.add_argument("--width", type=int, default=1024, help="Image width")
    parser.add_argument("--height", type=int, default=1024, help="Image height")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--no-photo", action="store_true", help="Disable automatic photographic enhancement (keep raw prompt)")
    args = parser.parse_args()
    print(f"no_photo = {args.no_photo}")
    print(f"prompt = {args.prompt}")
    return args

# Call test
try:
    args = test_main()
    print("SUCCESS: Argument parsing with Unicode hyphen works.")
except SystemExit as e:
    print(f"FAILED: {e}")