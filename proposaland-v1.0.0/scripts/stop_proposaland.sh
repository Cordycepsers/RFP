#!/bin/bash
# Proposaland Stop Script
# Stops the Proposaland opportunity monitoring system

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
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

# Stop the scheduler
stop_scheduler() {
    if [ ! -f "$PID_FILE" ]; then
        warning "PID file not found - Proposaland may not be running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p "$PID" > /dev/null 2>&1; then
        warning "Process with PID $PID is not running"
        rm -f "$PID_FILE"
        return 1
    fi
    
    log "Stopping Proposaland scheduler (PID: $PID)..."
    
    # Try graceful shutdown first
    kill "$PID"
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            success "Proposaland scheduler stopped successfully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if graceful shutdown failed
    warning "Graceful shutdown failed, forcing termination..."
    kill -9 "$PID" 2>/dev/null || true
    
    # Wait a bit more
    sleep 2
    
    if ! ps -p "$PID" > /dev/null 2>&1; then
        success "Proposaland scheduler forcefully stopped"
        rm -f "$PID_FILE"
        return 0
    else
        error "Failed to stop Proposaland scheduler"
        return 1
    fi
}

# Check status
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Proposaland is running (PID: $PID)"
            return 0
        else
            echo "Proposaland is not running (stale PID file)"
            return 1
        fi
    else
        echo "Proposaland is not running"
        return 1
    fi
}

# Main execution
main() {
    echo "=================================================="
    echo "    Proposaland Opportunity Monitoring System    "
    echo "              Shutdown Script                     "
    echo "=================================================="
    echo ""
    
    if stop_scheduler; then
        echo ""
        echo "=================================================="
        echo "Proposaland has been stopped successfully."
        echo "To restart, run: $SCRIPT_DIR/start_proposaland.sh"
        echo "=================================================="
    else
        echo ""
        echo "=================================================="
        echo "Failed to stop Proposaland or it was not running."
        echo "=================================================="
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Stop the Proposaland opportunity monitoring system"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --status       Check if Proposaland is running"
        echo "  --force        Force kill the process"
        echo ""
        exit 0
        ;;
    --status)
        check_status
        exit $?
        ;;
    --force)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            log "Force killing Proposaland (PID: $PID)..."
            kill -9 "$PID" 2>/dev/null || true
            rm -f "$PID_FILE"
            success "Proposaland forcefully terminated"
        else
            warning "No PID file found"
        fi
        exit 0
        ;;
esac

# Run main function
main

