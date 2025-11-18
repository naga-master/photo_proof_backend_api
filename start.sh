#!/bin/bash

# Photo Proof API Startup Script
# This script sets up the Python environment and starts the FastAPI server

echo "🚀 Starting Photo Proof API..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Generate mock data if data directory doesn't exist
if [ ! -d "data" ] || [ ! -f "data/projects.json" ]; then
    echo "🎲 Generating mock data..."
    python generate_mock_data.py
fi

# Get network IP address for mobile access
NETWORK_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

# Start the FastAPI server
echo "🚀 Photo Proof API Server"
echo "=================================================="
echo "📍 Local:   http://localhost:8000"
echo "🌐 Network: http://${NETWORK_IP}:8000"
echo "📚 Docs:    http://localhost:8000/docs"
echo "=================================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
