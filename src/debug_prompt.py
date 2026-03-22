#!/usr/bin/env python3
import requests
import json
import sys

server = "http://127.0.0.1:8188"
prompt_id = "54d3b603-a960-495a-8874-85802356030b"
try:
    resp = requests.get(f"{server}/history/{prompt_id}")
    resp.raise_for_status()
    data = resp.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)