#!/bin/bash
# Script to run the Voice Calculator Web App using the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Kill any existing process on port 5000
echo "Clearing port 5000..."
fuser -k 5000/tcp > /dev/null 2>&1 || true

# Run the Flask app
echo "Starting Web Server at http://127.0.0.1:5000"
python "$SCRIPT_DIR/app.py"
