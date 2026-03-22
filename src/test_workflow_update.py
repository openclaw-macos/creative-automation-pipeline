#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '.')
from comfyui_generate import load_workflow, find_prompt_node

workflow = load_workflow('sdxl_workflow.json')
print("Original workflow nodes:")
for k, v in workflow.items():
    if v.get('class_type') in ['CLIPTextEncode', 'EmptyLatentImage', 'KSampler']:
        print(f"  {k}: {v['class_type']} inputs: {v.get('inputs', {})}")

# Simulate what comfyui_generate.py does
pos_node = find_prompt_node(workflow, 'CLIPTextEncode')
print(f"\nFirst CLIPTextEncode node: {pos_node}")
workflow[pos_node]['inputs']['text'] = 'TEST PROMPT'
for node_id, node in workflow.items():
    if node.get('class_type') == 'CLIPTextEncode' and node_id != pos_node:
        node['inputs']['text'] = 'TEST NEGATIVE'
        print(f"Second CLIPTextEncode node: {node_id}")
        break

for node_id, node in workflow.items():
    if node.get('class_type') == 'EmptyLatentImage':
        node['inputs']['width'] = 512
        node['inputs']['height'] = 512
        print(f"EmptyLatentImage node {node_id} updated to 512x512")
        break

for node_id, node in workflow.items():
    if node.get('class_type') == 'KSampler':
        node['inputs']['seed'] = 42
        print(f"KSampler node {node_id} seed updated to 42")
        break

print("\nUpdated workflow nodes:")
for k, v in workflow.items():
    if v.get('class_type') in ['CLIPTextEncode', 'EmptyLatentImage', 'KSampler']:
        print(f"  {k}: {v['class_type']} inputs: {v.get('inputs', {})}")

# Save to temp file to inspect
with open('/tmp/updated_workflow.json', 'w') as f:
    json.dump(workflow, f, indent=2)
print("\nSaved updated workflow to /tmp/updated_workflow.json")