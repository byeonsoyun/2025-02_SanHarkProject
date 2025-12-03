#!/bin/bash
# Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated"
echo "Django version: $(python -m django --version)"
echo "To deactivate, run: deactivate"
