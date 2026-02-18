#!/bin/bash
set -e

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing poker-agent..."
pip install -e .

echo ""
echo "Installation complete!"
echo ""
echo "To activate the environment, run:"
echo "    source venv/bin/activate"
echo ""
echo "To start the agent, run:"
echo "    poker-agent"
echo ""
echo "Don't forget to create your .env file from .env.example"
