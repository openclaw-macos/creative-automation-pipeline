#!/usr/bin/env python3
import requests
import json
import os
import sys
import time
import random

server = "http://127.0.0.1:8188"
workflow_path = "sdxl_workflow.json"
with open(workflow_path, 'r') as f:
    workflow = json.load(f)

# Modify with unique values
unique_seed = random.randint(1, 999999999)
unique_prompt = f"a sleek modern coffee maker with unique {unique_seed}"
# Update nodes
for node_id, node in workflow.items():
    if node.get('class_type') == 'CLIPTextEncode':
        if 'text' in node['inputs'] and node['inputs']['text'] == 'PROMPT_PLACEHOLDER':
            node['inputs']['text'] = unique_prompt
        elif 'text' in node['inputs'] and node['inputs']['text'] == 'NEGATIVE_PROMPT_PLACEHOLDER':
            node['inputs']['text'] = 'blurry, distorted, ugly'
    elif node.get('class_type') == 'EmptyLatentImage':
        node['inputs']['width'] = 512
        node['inputs']['height'] = 512
    elif node.get('class_type') == 'KSampler':
        node['inputs']['seed'] = unique_seed

print(f"Using seed {unique_seed}, prompt: {unique_prompt}")
print("Workflow updated.")

# Queue prompt
resp = requests.post(f"{server}/prompt", json={"prompt": workflow})
resp.raise_for_status()
prompt_id = resp.json()["prompt_id"]
print(f"Prompt queued: {prompt_id}")

# Wait for completion
while True:
    resp = requests.get(f"{server}/history")
    resp.raise_for_status()
    history = resp.json()
    if prompt_id in history:
        result = history[prompt_id]
        break
    time.sleep(1)

print(f"Result keys: {list(result.keys())}")
outputs = result.get('outputs', {})
print(f"Outputs keys: {list(outputs.keys())}")
for node_id, node_out in outputs.items():
    if 'images' in node_out:
        for img in node_out['images']:
            filename = img['filename']
            subfolder = img.get('subfolder', '')
            full = os.path.join(subfolder, filename) if subfolder else filename
            print(f"Image generated: {full}")
            # Download
            resp = requests.get(f"{server}/view?filename={full}")
            resp.raise_for_status()
            out_path = f"/tmp/unique_{unique_seed}.png"
            with open(out_path, 'wb') as f:
                f.write(resp.content)
            print(f"Saved to {out_path}")
            sys.exit(0)

print("No images in outputs.")
print(f"Status: {result.get('status', {})}")
sys.exit(1)