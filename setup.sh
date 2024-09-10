#!/bin/bash

# Setup script for Python project

# Set the project directory
PROJECT_DIR=$(dirname "$0")

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the application (optional)
echo "Running the application..."
python main.py

# Deactivate the virtual environment
echo "Deactivating the virtual environment..."
deactivate

echo "Setup complete!"