#!/bin/bash
# Install Python dependencies for the ComfyUI skill with compliance & reporting
# Creates a virtual environment and installs dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "=== Installing dependencies for Creative Automation Pipeline ==="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "✅ Virtual environment created at $PROJECT_ROOT/venv"
else
    echo "Virtual environment already exists at $PROJECT_ROOT/venv"
fi

# Install dependencies
echo "Installing dependencies from requirements.txt..."
"$PROJECT_ROOT/venv/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "To activate the virtual environment:"
echo "  source $PROJECT_ROOT/venv/bin/activate"
echo ""
echo "To run the demo:"
echo "  cd $PROJECT_ROOT && ./run_demo.sh"