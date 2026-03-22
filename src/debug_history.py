#!/usr/bin/env python3
import requests
import json
import sys

server = "http://127.0.0.1:8188"
try:
    resp = requests.get(f"{server}/history")
    resp.raise_for_status()
    history = resp.json()
    print(f"History keys: {list(history.keys())}")
    for prompt_id, data in history.items():
        print(f"\n--- Prompt ID: {prompt_id} ---")
        print(f"  Outputs keys: {list(data.get('outputs', {}).keys())}")
        for node_id, node_out in data.get('outputs', {}).items():
            print(f"    Node {node_id}: {list(node_out.keys())}")
            if 'images' in node_out:
                for img in node_out['images']:
                    print(f"      Image: {img}")
        print(f"  Status: {data.get('status', {})}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)