#!/bin/bash
# Production startup script with Gunicorn

echo "Starting PixelWeather API in production mode..."

# Activate virtual environment
source venv/bin/activate

# Check if required environment variables are set
if [ -z "$DB_PASSWORD" ]; then
    echo "Loading environment variables from .env file..."
fi

# Start with Gunicorn
echo "Starting Gunicorn server..."
gunicorn --config gunicorn.conf.py main:app