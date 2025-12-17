#!/bin/bash
# Quick script to run blog automation

echo "🚀 Starting Blog Automation..."
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
            echo "Installing virtual env..."
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
python3 run_blog_automation.py
