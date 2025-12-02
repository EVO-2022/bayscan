#!/bin/bash
# BayScan Setup Script for Ubuntu

set -e  # Exit on error

echo "=================================="
echo "BayScan Setup"
echo "=================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
else
    echo "✓ Python 3 is installed: $(python3 --version)"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Review and edit config.yaml with your preferences"
echo "2. Run the application:"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080"
echo ""
echo "3. Open your browser to http://localhost:8080"
echo "   Or from another device: http://YOUR_SERVER_IP:8080"
echo ""
echo "To run in the background, see README.md for systemd service setup."
echo ""
