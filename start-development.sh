#!/bin/bash
# Development startup script with Flask dev server

echo "Starting PixelWeather API in development mode..."

# Activate virtual environment
source venv/bin/activate

# Start with Flask development server
echo "Starting Flask development server..."
python3 main.py