#!/bin/bash
# Proposaland Status and Maintenance Script
# Provides system status, logs, and maintenance functions

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
OUTPUT_DIR="$PROJECT_DIR/output"
PID_FILE="$PROJECT_DIR/proposaland.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Check if Proposaland is running
check_running_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            success "Proposaland is RUNNING (PID: $PID)"
            
            # Get process info
            PROCESS_INFO=$(ps -p "$PID" -o pid,ppid,etime,pcpu,pmem,cmd --no-headers)
            echo "Process Info: $PROCESS_INFO"
            
            return 0
        else
            warning "Proposaland is NOT RUNNING (stale PID file found)"
            return 1
        fi
    else
        warning "Proposaland is NOT RUNNING (no PID file)"
        return 1
    fi
}

# Show system information
show_system_info() {
    echo ""
    echo "=== SYSTEM INFORMATION ==="
    
    # Disk space
    echo "Disk Usage:"
    df -h "$PROJECT_DIR" | tail -1 | awk '{print "  Available: " $4 " (" $5 " used)"}'
    
    # Memory usage
    echo "Memory Usage:"
    free -h | grep "Mem:" | awk '{print "  Available: " $7 " / " $2}'
    
    # Load average
    echo "Load Average:"
    uptime | awk -F'load average:' '{print "  " $2}'
    
    # Python version
    echo "Python Version:"
    python3 --version | awk '{print "  " $0}'
}

# Show log summary
show_log_summary() {
    echo ""
    echo "=== LOG SUMMARY ==="
    
    if [ -d "$LOG_DIR" ]; then
        # Count log files
        LOG_COUNT=$(find "$LOG_DIR" -name "*.log" | wc -l)
        echo "Log Files: $LOG_COUNT"
        
        # Show latest log files
        echo "Recent Log Files:"
        find "$LOG_DIR" -name "*.log" -type f -printf '%T@ %p\n' | sort -n | tail -5 | while read timestamp file; do
            filename=$(basename "$file")
            size=$(du -h "$file" | cut -f1)
            date=$(date -d "@${timestamp%.*}" '+%Y-%m-%d %H:%M')
            echo "  $filename ($size) - $date"
        done
        
        # Show recent errors
        echo "Recent Errors (last 24 hours):"
        find "$LOG_DIR" -name "*.log" -type f -newermt "24 hours ago" -exec grep -l "ERROR" {} \; | head -3 | while read logfile; do
            echo "  From $(basename "$logfile"):"
            grep "ERROR" "$logfile" | tail -2 | sed 's/^/    /'
        done
        
    else
        warning "Log directory not found: $LOG_DIR"
    fi
}

# Show output summary
show_output_summary() {
    echo ""
    echo "=== OUTPUT SUMMARY ==="
    
    if [ -d "$OUTPUT_DIR" ]; then
        # Count output files
        EXCEL_COUNT=$(find "$OUTPUT_DIR" -name "*.xlsx" | wc -l)
        JSON_COUNT=$(find "$OUTPUT_DIR" -name "*.json" | wc -l)
        
        echo "Excel Files: $EXCEL_COUNT"
        echo "JSON Files: $JSON_COUNT"
        
        # Show latest outputs
        echo "Recent Output Files:"
        find "$OUTPUT_DIR" -type f \( -name "*.xlsx" -o -name "*.json" \) -printf '%T@ %p\n' | sort -n | tail -5 | while read timestamp file; do
            filename=$(basename "$file")
            size=$(du -h "$file" | cut -f1)
            date=$(date -d "@${timestamp%.*}" '+%Y-%m-%d %H:%M')
            echo "  $filename ($size) - $date"
        done
        
    else
        warning "Output directory not found: $OUTPUT_DIR"
    fi
}

# Show configuration summary
show_config_summary() {
    echo ""
    echo "=== CONFIGURATION SUMMARY ==="
    
    CONFIG_FILE="$PROJECT_DIR/config/proposaland_config.json"
    
    if [ -f "$CONFIG_FILE" ]; then
        success "Configuration file exists"
        
        # Extract key configuration values
        if command -v jq > /dev/null 2>&1; then
            echo "Email Recipient: $(jq -r '.email.recipient_email // "Not configured"' "$CONFIG_FILE")"
            echo "Daily Schedule: $(jq -r '.scheduler.daily_time // "09:00"' "$CONFIG_FILE")"
            echo "Target Websites: $(jq -r '[.target_websites.high_priority[], .target_websites.medium_priority[], .target_websites.low_priority[]] | length' "$CONFIG_FILE")"
            echo "Primary Keywords: $(jq -r '.keywords.primary | length' "$CONFIG_FILE")"
        else
            echo "Configuration details require 'jq' to display"
        fi
        
        # File info
        CONFIG_SIZE=$(du -h "$CONFIG_FILE" | cut -f1)
        CONFIG_DATE=$(date -r "$CONFIG_FILE" '+%Y-%m-%d %H:%M')
        echo "File Size: $CONFIG_SIZE"
        echo "Last Modified: $CONFIG_DATE"
        
    else
        error "Configuration file not found: $CONFIG_FILE"
    fi
}

# Show recent activity
show_recent_activity() {
    echo ""
    echo "=== RECENT ACTIVITY ==="
    
    # Check for recent execution summaries
    SUMMARY_DIR="$LOG_DIR/execution_summaries"
    if [ -d "$SUMMARY_DIR" ]; then
        echo "Recent Executions:"
        find "$SUMMARY_DIR" -name "*.json" -type f -printf '%T@ %p\n' | sort -n | tail -3 | while read timestamp file; do
            filename=$(basename "$file")
            date=$(date -d "@${timestamp%.*}" '+%Y-%m-%d %H:%M')
            
            if command -v jq > /dev/null 2>&1; then
                success_status=$(jq -r '.success' "$file" 2>/dev/null || echo "unknown")
                opportunities=$(jq -r '.opportunities_found' "$file" 2>/dev/null || echo "unknown")
                duration=$(jq -r '.duration_seconds' "$file" 2>/dev/null || echo "unknown")
                
                status_icon="❓"
                [ "$success_status" = "true" ] && status_icon="✅"
                [ "$success_status" = "false" ] && status_icon="❌"
                
                echo "  $status_icon $date - $opportunities opportunities (${duration}s)"
            else
                echo "  📄 $date - $filename"
            fi
        done
    else
        info "No execution summaries found"
    fi
    
    # Check for recent log entries
    echo "Recent Log Entries:"
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "*.log" -type f -newermt "24 hours ago" -exec tail -5 {} \; | tail -10 | sed 's/^/  /'
    fi
}

# Run maintenance tasks
run_maintenance() {
    echo ""
    echo "=== RUNNING MAINTENANCE ==="
    
    log "Starting maintenance tasks..."
    
    # Clean old logs (older than 30 days)
    if [ -d "$LOG_DIR" ]; then
        OLD_LOGS=$(find "$LOG_DIR" -name "*.log" -type f -mtime +30)
        if [ -n "$OLD_LOGS" ]; then
            echo "$OLD_LOGS" | wc -l | xargs echo "Cleaning old log files:"
            echo "$OLD_LOGS" | xargs rm -f
            success "Old log files cleaned"
        else
            info "No old log files to clean"
        fi
    fi
    
    # Clean old outputs (older than 60 days)
    if [ -d "$OUTPUT_DIR" ]; then
        OLD_OUTPUTS=$(find "$OUTPUT_DIR" -type f -mtime +60)
        if [ -n "$OLD_OUTPUTS" ]; then
            echo "$OLD_OUTPUTS" | wc -l | xargs echo "Cleaning old output files:"
            echo "$OLD_OUTPUTS" | xargs rm -f
            success "Old output files cleaned"
        else
            info "No old output files to clean"
        fi
    fi
    
    # Check disk space
    DISK_USAGE=$(df "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 80 ]; then
        warning "Disk usage is high: ${DISK_USAGE}%"
    else
        success "Disk usage is acceptable: ${DISK_USAGE}%"
    fi
    
    success "Maintenance tasks completed"
}

# Test email configuration
test_email() {
    echo ""
    echo "=== TESTING EMAIL CONFIGURATION ==="
    
    cd "$PROJECT_DIR"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    log "Running email configuration test..."
    
    if python3 scheduler.py --test-email; then
        success "Email configuration test PASSED"
    else
        error "Email configuration test FAILED"
        echo "Please check your email settings in the configuration file"
    fi
}

# Run a test monitoring cycle
run_test_monitoring() {
    echo ""
    echo "=== RUNNING TEST MONITORING ==="
    
    cd "$PROJECT_DIR"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    log "Running test monitoring cycle..."
    
    if python3 scheduler.py --run-once; then
        success "Test monitoring cycle completed successfully"
        echo "Check the output directory for generated files"
    else
        error "Test monitoring cycle failed"
        echo "Check the logs for error details"
    fi
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Proposaland Status and Maintenance Script"
    echo ""
    echo "Commands:"
    echo "  status      Show system status (default)"
    echo "  logs        Show detailed log information"
    echo "  maintenance Run maintenance tasks"
    echo "  test-email  Test email configuration"
    echo "  test-run    Run a test monitoring cycle"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Show status"
    echo "  $0 logs              # Show log details"
    echo "  $0 maintenance       # Run maintenance"
    echo ""
}

# Main status display
show_status() {
    echo "=================================================="
    echo "    Proposaland Opportunity Monitoring System    "
    echo "                Status Report                     "
    echo "=================================================="
    
    check_running_status
    show_system_info
    show_config_summary
    show_output_summary
    show_recent_activity
    
    echo ""
    echo "=================================================="
    echo "For more details, run: $0 logs"
    echo "For maintenance, run: $0 maintenance"
    echo "=================================================="
}

# Main execution
case "${1:-status}" in
    status)
        show_status
        ;;
    logs)
        show_status
        show_log_summary
        ;;
    maintenance)
        run_maintenance
        ;;
    test-email)
        test_email
        ;;
    test-run)
        run_test_monitoring
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

