#!/bin/bash

# Proposaland Production Deployment Script
# This script sets up Proposaland for production use

set -e  # Exit on any error

echo "🚀 Proposaland Production Deployment"
echo "===================================="

# Configuration
INSTALL_DIR="/opt/proposaland"
SERVICE_USER="proposaland"
PYTHON_VERSION="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user with sudo privileges."
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v $PYTHON_VERSION &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.8 or higher."
    fi
    
    python_version=$($PYTHON_VERSION --version 2>&1 | awk '{print $2}')
    log "Python version: $python_version"
    
    # Check available disk space (minimum 5GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ $available_space -lt 5242880 ]; then  # 5GB in KB
        warn "Less than 5GB disk space available. Consider freeing up space."
    fi
    
    # Check memory (minimum 2GB)
    total_mem=$(free -m | awk 'NR==2{print $2}')
    if [ $total_mem -lt 2048 ]; then
        warn "Less than 2GB RAM available. Performance may be affected."
    fi
    
    log "System requirements check completed"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        cron \
        logrotate \
        curl \
        wget \
        unzip \
        build-essential \
        python3-dev
    
    log "System dependencies installed"
}

# Create service user
create_user() {
    log "Creating service user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        log "User $SERVICE_USER already exists"
    else
        sudo useradd -r -s /bin/bash -d $INSTALL_DIR -m $SERVICE_USER
        log "Created user: $SERVICE_USER"
    fi
}

# Setup directory structure
setup_directories() {
    log "Setting up directory structure..."
    
    # Create main directory
    sudo mkdir -p $INSTALL_DIR
    
    # Copy files to installation directory
    if [ -d "$(pwd)/src" ]; then
        sudo cp -r . $INSTALL_DIR/
    else
        error "Source files not found. Please run this script from the Proposaland directory."
    fi
    
    # Create required subdirectories
    sudo mkdir -p $INSTALL_DIR/{logs,output,data,temp,backups,config}
    
    # Set ownership
    sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    # Set permissions
    sudo chmod 755 $INSTALL_DIR
    sudo chmod -R 755 $INSTALL_DIR/scripts
    sudo chmod +x $INSTALL_DIR/scripts/*.sh
    
    log "Directory structure created"
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER $PYTHON_VERSION -m venv venv
    
    # Install Python dependencies
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt
    
    log "Python virtual environment setup completed"
}

# Configure production settings
configure_production() {
    log "Configuring production settings..."
    
    # Copy production configuration
    sudo -u $SERVICE_USER cp $INSTALL_DIR/config/proposaland_production_config.json $INSTALL_DIR/config/proposaland_config.json
    
    # Prompt for email configuration
    echo ""
    echo -e "${BLUE}Email Configuration${NC}"
    echo "Please provide your email settings for notifications:"
    
    read -p "SMTP Server (default: smtp.gmail.com): " smtp_server
    smtp_server=${smtp_server:-smtp.gmail.com}
    
    read -p "SMTP Port (default: 587): " smtp_port
    smtp_port=${smtp_port:-587}
    
    read -p "Sender Email: " sender_email
    if [ -z "$sender_email" ]; then
        error "Sender email is required"
    fi
    
    read -s -p "Email Password (App-Specific Password for Gmail): " email_password
    echo ""
    if [ -z "$email_password" ]; then
        error "Email password is required"
    fi
    
    read -p "Recipient Email (default: majalemaja@pm.me): " recipient_email
    recipient_email=${recipient_email:-majalemaja@pm.me}
    
    # Update configuration file
    sudo -u $SERVICE_USER python3 << EOF
import json

config_file = '$INSTALL_DIR/config/proposaland_config.json'
with open(config_file, 'r') as f:
    config = json.load(f)

config['email']['smtp_server'] = '$smtp_server'
config['email']['smtp_port'] = $smtp_port
config['email']['sender_email'] = '$sender_email'
config['email']['sender_password'] = '$email_password'
config['email']['recipient_email'] = '$recipient_email'

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("Configuration updated successfully")
EOF
    
    log "Production configuration completed"
}

# Setup systemd service
setup_systemd() {
    log "Setting up systemd service..."
    
    # Create service file
    sudo tee /etc/systemd/system/proposaland.service > /dev/null << EOF
[Unit]
Description=Proposaland Opportunity Monitor
After=network.target

[Service]
Type=oneshot
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python proposaland_monitor.py
StandardOutput=journal
StandardError=journal
TimeoutSec=7200

[Install]
WantedBy=multi-user.target
EOF
    
    # Create timer file
    sudo tee /etc/systemd/system/proposaland.timer > /dev/null << EOF
[Unit]
Description=Run Proposaland daily at 6:00 AM UTC
Requires=proposaland.service

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
    
    # Reload systemd and enable timer
    sudo systemctl daemon-reload
    sudo systemctl enable proposaland.timer
    
    log "Systemd service and timer created"
}

# Setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/proposaland > /dev/null << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload proposaland || true
    endscript
}
EOF
    
    log "Log rotation configured"
}

# Setup monitoring scripts
setup_monitoring() {
    log "Setting up monitoring scripts..."
    
    # Create health check script
    sudo -u $SERVICE_USER tee $INSTALL_DIR/scripts/health_check.sh > /dev/null << 'EOF'
#!/bin/bash
cd /opt/proposaland

echo "=== Proposaland Health Check ==="
echo "Date: $(date)"
echo ""

# Check if last run was successful
if [ -f "logs/proposaland.log" ]; then
    last_run=$(grep "Monitoring cycle completed" logs/proposaland.log | tail -1)
    if [ -n "$last_run" ]; then
        echo "✓ Last successful run: $last_run"
    else
        echo "⚠ No successful runs found in logs"
    fi
else
    echo "⚠ No log file found"
fi

# Check disk space
disk_usage=$(df $PWD | awk 'NR==2 {print $5}' | sed 's/%//')
echo "Disk usage: ${disk_usage}%"
if [ $disk_usage -gt 85 ]; then
    echo "⚠ WARNING: High disk usage"
fi

# Check recent errors
error_count=$(grep -c "ERROR" logs/proposaland.log 2>/dev/null || echo "0")
echo "Recent errors: $error_count"

# Check service status
if systemctl is-active --quiet proposaland.timer; then
    echo "✓ Timer service is active"
else
    echo "⚠ Timer service is not active"
fi

echo ""
echo "=== End Health Check ==="
EOF
    
    sudo chmod +x $INSTALL_DIR/scripts/health_check.sh
    
    # Create backup script
    sudo -u $SERVICE_USER tee $INSTALL_DIR/scripts/backup.sh > /dev/null << 'EOF'
#!/bin/bash
cd /opt/proposaland

# Create backup directory with timestamp
backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# Backup configuration and data
cp -r config/ "$backup_dir/" 2>/dev/null || true
cp -r output/ "$backup_dir/" 2>/dev/null || true
cp -r data/ "$backup_dir/" 2>/dev/null || true

# Compress backup
tar -czf "$backup_dir.tar.gz" "$backup_dir"
rm -rf "$backup_dir"

# Keep only last 7 days of backups
find backups/ -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "Backup completed: $backup_dir.tar.gz"
EOF
    
    sudo chmod +x $INSTALL_DIR/scripts/backup.sh
    
    log "Monitoring scripts created"
}

# Run initial test
run_test() {
    log "Running initial system test..."
    
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python test_system.py
    
    if [ $? -eq 0 ]; then
        log "✓ System test passed"
    else
        warn "System test failed. Please check the configuration."
    fi
}

# Display final instructions
show_final_instructions() {
    echo ""
    echo -e "${GREEN}🎉 Proposaland Production Deployment Completed!${NC}"
    echo "=================================================="
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Start the timer service:"
    echo "   sudo systemctl start proposaland.timer"
    echo ""
    echo "2. Check service status:"
    echo "   sudo systemctl status proposaland.timer"
    echo ""
    echo "3. View logs:"
    echo "   sudo journalctl -u proposaland.service -f"
    echo "   tail -f $INSTALL_DIR/logs/proposaland.log"
    echo ""
    echo "4. Run manual test:"
    echo "   cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python proposaland_monitor.py"
    echo ""
    echo "5. Health check:"
    echo "   sudo -u $SERVICE_USER $INSTALL_DIR/scripts/health_check.sh"
    echo ""
    echo -e "${BLUE}Configuration Files:${NC}"
    echo "- Main config: $INSTALL_DIR/config/proposaland_config.json"
    echo "- Service file: /etc/systemd/system/proposaland.service"
    echo "- Timer file: /etc/systemd/system/proposaland.timer"
    echo "- Log rotation: /etc/logrotate.d/proposaland"
    echo ""
    echo -e "${BLUE}Important Notes:${NC}"
    echo "- The system will run daily at 6:00 AM UTC"
    echo "- Logs are rotated daily and kept for 30 days"
    echo "- Backups are created automatically"
    echo "- Email notifications will be sent to: $recipient_email"
    echo ""
    echo -e "${YELLOW}Security Reminder:${NC}"
    echo "- Review firewall settings"
    echo "- Ensure email credentials are secure"
    echo "- Monitor system logs regularly"
    echo ""
    echo "For detailed documentation, see: $INSTALL_DIR/PRODUCTION_SETUP.md"
}

# Main execution
main() {
    echo "Starting Proposaland production deployment..."
    echo ""
    
    check_root
    check_requirements
    install_dependencies
    create_user
    setup_directories
    setup_venv
    configure_production
    setup_systemd
    setup_logrotate
    setup_monitoring
    run_test
    show_final_instructions
}

# Run main function
main "$@"

