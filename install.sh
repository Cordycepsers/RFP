#!/bin/bash
# Proposaland Installation Script

set -e

echo "=================================================="
echo "    Proposaland Opportunity Monitoring System    "
echo "              Installation Script                 "
echo "=================================================="
echo ""

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3.11+ is required but not installed."
        echo "Please install Python 3.11 or higher and try again."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
        echo "Error: Python $PYTHON_VERSION found, but 3.11+ is required."
        exit 1
    fi
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3.11"
fi

echo "✓ Python version check passed"

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Set up configuration
if [ ! -f "config/proposaland_config.json" ]; then
    echo "Setting up configuration..."
    cp config/sample_config.json config/proposaland_config.json
    echo "⚠ Please edit config/proposaland_config.json with your email settings"
fi

# Make scripts executable
chmod +x scripts/*.sh

# Create directories
mkdir -p logs output data

echo ""
echo "=================================================="
echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config/proposaland_config.json with your email settings"
echo "2. Test email configuration: ./scripts/proposaland_status.sh test-email"
echo "3. Run system test: python3 test_system.py"
echo "4. Start monitoring: ./scripts/start_proposaland.sh"
echo ""
echo "For detailed instructions, see INSTALLATION.md"
echo "=================================================="
