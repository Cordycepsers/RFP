#!/bin/bash
# Proposaland Startup Script
# Starts the Proposaland opportunity monitoring system

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/proposaland.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            error "Proposaland is already running (PID: $PID)"
            exit 1
        else
            warning "Stale PID file found, removing..."
            rm -f "$PID_FILE"
        fi
    fi
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Create logs directory
    mkdir -p "$LOG_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install/update dependencies
    log "Installing dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    success "Environment setup complete"
}

# Validate configuration
validate_config() {
    log "Validating configuration..."
    
    CONFIG_FILE="$PROJECT_DIR/config/proposaland_config.json"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    
    # Test JSON validity
    if ! python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
        error "Invalid JSON in configuration file"
        exit 1
    fi
    
    success "Configuration validated"
}

# Test email configuration
test_email() {
    log "Testing email configuration..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    if python3 scheduler.py --test-email; then
        success "Email configuration test passed"
    else
        warning "Email configuration test failed - check email settings"
    fi
}

# Start the scheduler
start_scheduler() {
    log "Starting Proposaland scheduler..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Start scheduler in background
    nohup python3 scheduler.py > "$LOG_DIR/scheduler_output.log" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        success "Proposaland scheduler started successfully (PID: $(cat "$PID_FILE"))"
        log "Logs are being written to: $LOG_DIR/"
        log "To stop the scheduler, run: $SCRIPT_DIR/stop_proposaland.sh"
    else
        error "Failed to start scheduler - check logs for details"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Main execution
main() {
    echo "=================================================="
    echo "    Proposaland Opportunity Monitoring System    "
    echo "=================================================="
    echo ""
    
    check_running
    setup_environment
    validate_config
    test_email
    start_scheduler
    
    echo ""
    echo "=================================================="
    echo "Proposaland is now running and monitoring opportunities!"
    echo "Daily reports will be sent at 9:00 AM."
    echo "=================================================="
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Start the Proposaland opportunity monitoring system"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --no-email     Skip email configuration test"
        echo ""
        exit 0
        ;;
    --no-email)
        test_email() { log "Skipping email test"; }
        ;;
esac

# Run main function
main

