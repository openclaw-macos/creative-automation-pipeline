#!/usr/bin/env python3
"""
Print the absolute path where the generated image will be saved.
This helps verify the output location when using the ComfyUI skill.
"""
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_output.py <output_path>")
        sys.exit(1)
    
    output_path = sys.argv[1]
    abs_path = os.path.abspath(output_path)
    print(f"Output will be saved to:")
    print(f"  {abs_path}")
    print(f"Directory: {os.path.dirname(abs_path)}")
    
    # Check if directory exists
    dir_path = os.path.dirname(abs_path)
    if dir_path:
        if os.path.isdir(dir_path):
            print("✓ Directory exists.")
        else:
            print("⚠ Directory does not exist; it will be created by the script.")
    else:
        print("⚠ Output is in current directory.")
    
    # Suggest absolute path for pipeline integration
    print("\nFor integration with the FDE pipeline, use an absolute path:")
    print(f'  --output "{abs_path}"')

if __name__ == "__main__":
    main()