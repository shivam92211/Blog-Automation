#!/bin/bash

# Quick start script for Blog Automation System

set -e

echo "=========================================="
echo "Blog Automation System - Quick Start"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."

    # Remove any incomplete venv directory
    rm -rf venv

    # Try python3 -m venv first
    if python3 -m venv venv 2>/dev/null && [ -f "venv/bin/activate" ]; then
        echo "✓ Virtual environment created"
    else
        echo "⚠ python3-venv not available, trying virtualenv..."

        # Clean up failed attempt
        rm -rf venv

        # Check if virtualenv is installed
        if ! command -v virtualenv &> /dev/null && ! python3 -m virtualenv --version &> /dev/null; then
            echo "Installing virtualenv..."
            if ! python3 -m pip install --user virtualenv 2>/dev/null; then
                echo "Trying with --break-system-packages flag..."
                python3 -m pip install --user --break-system-packages virtualenv
            fi
        fi

        # Create venv with virtualenv
        if command -v virtualenv &> /dev/null; then
            virtualenv venv
        else
            python3 -m virtualenv venv
        fi
        echo "✓ Virtual environment created using virtualenv"
    fi
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Activated"
echo ""

# Check if dependencies are installed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
    echo ""
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠ No .env file found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    exit 1
fi

# Ask if user wants to initialize database
# echo "Initialize database? (y/n)"
# read -r response
# if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
#     echo ""
#     echo "Initializing database..."
#     python scripts/init_db.py
#     echo ""
# fi

# Ask if user wants to test setup
# echo "Test setup? (y/n)"
# read -r response
# if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
#     echo ""
#     echo "Testing setup..."
#     python scripts/test_setup.py
#     echo ""
# fi

# Start the application
echo "=========================================="
echo "Starting application..."
echo "=========================================="
echo ""
echo "API will be available at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
