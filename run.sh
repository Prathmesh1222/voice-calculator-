#!/bin/bash
# Script to run the Voice Calculator using the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Run the python script
python "$SCRIPT_DIR/voice_calculator.py"
