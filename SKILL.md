---
name: comfyui
description: Generate images using a local ComfyUI server. Use when you need to produce product visuals, ad creatives, or any image based on a text prompt.
---

# ComfyUI Skill

This skill enables OpenClaw to call a local ComfyUI server (typically `http://127.0.0.1:8188`) to generate images from text prompts. It handles workflow loading, prompt queuing, and image downloading.

## Prerequisites

- **ComfyUI server** running locally (default port `8188`). Start it with:
  ```bash
  cd /path/to/ComfyUI && python main.py --port 8188
  ```
- **Python 3** with `requests` library installed:
  ```bash
  pip install requests
  ```
- **A valid workflow JSON** that defines the image‑generation pipeline. A default workflow is included in `scripts/default_workflow.json`.

## Quick Start

1. Ensure ComfyUI server is reachable at `http://127.0.0.1:8188`.
2. Install dependencies:
   ```bash
   cd skills/comfyui && pip install -r requirements.txt
   ```
3. Use the provided Python script to generate an image:
   ```bash
   python src/comfyui_generate.py --prompt "a photo of a coffee maker on a kitchen counter" --output outputs/images/coffee_maker.png
   ```
4. The script will:
   - Load the default workflow from `configs/default_workflow.json`.
   - Replace the positive prompt node.
   - Queue the prompt and poll for completion.
   - Save the resulting image to the specified path.
   - Optionally run brand compliance and legal checks (see `--compliance-check` and `--legal-check` flags).

## API Details

ComfyUI exposes a simple REST API:

- `GET /history` – retrieve past execution results.
- `POST /prompt` – queue a new prompt; returns a `prompt_id`.
- `GET /history/{prompt_id}` – get output images for a completed prompt.

The skill’s Python script abstracts these steps into a single function call.

## Workflow Customization

The default workflow (`configs/default_workflow.json`) uses:
- **CheckpointLoader** (SD1.5 or SDXL)
- **CLIPTextEncode** for positive/negative prompts
- **KSampler** with standard settings
- **VAEDecode** and **SaveImage**

To modify the workflow (change model, sampler, dimensions), edit the JSON file or pass a custom workflow path to the script.

## Usage in OpenClaw Tasks

When a creative automation pipeline needs to generate product images, call the script with the product‑specific prompt:

```python
import subprocess
import json

prompt = "professional product photo of a blender, studio lighting, white background, high detail"
subprocess.run([
    "python", "scripts/comfyui_generate.py",
    "--prompt", prompt,
    "--output", "images/blender_16_9.png"
])
```

## Error Handling

- If the server is unreachable, the script exits with a connection error.
- If the prompt fails (e.g., out‑of‑memory), the script will report the ComfyUI error message.
- Always verify the output file exists after generation.

## Example

Given a campaign brief for “Coffee Maker” and “Blender”, you would generate two images with full compliance and reporting:

```bash
python src/comfyui_generate.py --prompt "a sleek modern coffee maker, stainless steel, morning light, kitchen counter" --output outputs/images/coffee_maker.png --product "Coffee Maker" --compliance-check --legal-check
python src/comfyui_generate.py --prompt "a high‑speed blender with glass pitcher, vibrant green smoothie, clean background" --output outputs/images/blender.png --product "Blender" --compliance-check --legal-check
```

For a quick demo, run the provided script:
```bash
cd skills/comfyui && ./run_demo.sh
```

## Notes

- The first generation may be slow as models load into VRAM.
- Keep prompts concise but descriptive for best results.
- For batch generation, consider extending the script to accept a list of prompts.

---

**Skill ready.** Use `openclaw skills check` to verify it appears in the list.