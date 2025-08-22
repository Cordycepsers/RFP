# Proposaland Installation Guide

This guide provides step-by-step instructions for installing and configuring the Proposaland Opportunity Monitoring System.

## System Requirements

### Minimum Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+ / Windows 10+
- **Python**: Version 3.11 or higher
- **RAM**: 4GB minimum
- **Storage**: 10GB free space
- **Network**: Stable internet connection

### Recommended Requirements
- **RAM**: 8GB or more
- **CPU**: 2+ cores
- **Storage**: 20GB+ for extended log retention
- **Network**: High-speed broadband connection

## Pre-Installation Checklist

### 1. Email Account Setup
- Gmail account with app-specific password enabled
- Two-factor authentication configured
- SMTP access enabled

### 2. System Preparation
- Administrative/sudo access to the system
- Internet connectivity verified
- Firewall configured to allow outbound SMTP (port 587)

## Installation Steps

### Step 1: System Preparation

#### Ubuntu/Debian
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3.11 python3.11-pip python3.11-venv git curl wget

# Install additional dependencies
sudo apt install -y build-essential libssl-dev libffi-dev python3.11-dev
```

#### CentOS/RHEL
```bash
# Update system packages
sudo yum update -y

# Install Python 3.11 and dependencies
sudo yum install -y python3.11 python3.11-pip python3.11-devel git curl wget

# Install build tools
sudo yum groupinstall -y "Development Tools"
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install additional tools
brew install git curl wget
```

#### Windows
1. Download Python 3.11 from https://python.org
2. Install Python with "Add to PATH" option enabled
3. Install Git from https://git-scm.com
4. Open Command Prompt or PowerShell as Administrator

### Step 2: Download Proposaland

```bash
# Create installation directory
mkdir -p ~/proposaland-system
cd ~/proposaland-system

# Extract the Proposaland package (provided separately)
# If you have a zip file:
unzip proposaland-v1.0.0.zip
cd proposaland/

# Or if you have the directory structure already:
cd proposaland/
```

### Step 3: Environment Setup

```bash
# Create Python virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Configuration

#### 4.1 Email Configuration

Edit the configuration file:
```bash
nano config/proposaland_config.json
```

Update the email section:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-specific-password",
    "recipient_email": "majalemaja@pm.me"
  }
}
```

#### 4.2 Gmail App Password Setup

1. Go to Google Account settings
2. Navigate to Security → 2-Step Verification
3. Generate an App Password for "Mail"
4. Use this 16-character password in the configuration

#### 4.3 Customize Keywords (Optional)

```json
{
  "keywords": {
    "primary": [
      "video", "photo", "film", "multimedia", "design", 
      "visual", "campaign", "podcasts", "virtual event", 
      "media", "animation", "promotion", "communication", 
      "audiovisual"
    ],
    "secondary": [
      "creative", "content", "digital", "marketing",
      "branding", "graphics", "illustration"
    ]
  }
}
```

#### 4.4 Geographic Preferences

```json
{
  "geographic_filters": {
    "excluded_countries": [
      "India", "Pakistan", "China", "Bangladesh", 
      "Sri Lanka", "Myanmar"
    ],
    "excluded_keywords": ["local company", "national only"],
    "preferred_regions": [
      "Africa", "Latin America", "Eastern Europe", 
      "Central Asia", "Nepal"
    ]
  }
}
```

### Step 5: Initial Testing

#### 5.1 Test Email Configuration
```bash
# Test email settings
python3 scheduler.py --test-email
```

Expected output:
```
Email configuration test PASSED
```

#### 5.2 Run System Test
```bash
# Run comprehensive system test
python3 test_system.py
```

Expected output:
```
================================================
System test completed successfully!
All components are working correctly.
================================================
```

#### 5.3 Test Single Monitoring Cycle
```bash
# Run one monitoring cycle
python3 scheduler.py --run-once
```

This will:
- Scrape target websites
- Extract opportunities
- Generate Excel and JSON files
- Send email notification

### Step 6: Start Automated Monitoring

#### 6.1 Using Startup Scripts (Recommended)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start the system
./scripts/start_proposaland.sh
```

#### 6.2 Manual Startup

```bash
# Start scheduler manually
python3 scheduler.py
```

#### 6.3 Verify System is Running

```bash
# Check system status
./scripts/proposaland_status.sh
```

Expected output:
```
Proposaland is RUNNING (PID: 12345)
```

## Post-Installation Configuration

### Directory Structure Verification

Ensure the following directory structure exists:
```
proposaland/
├── config/
│   └── proposaland_config.json
├── src/
│   ├── scrapers/
│   ├── filters/
│   ├── outputs/
│   └── notifications/
├── scripts/
│   ├── start_proposaland.sh
│   ├── stop_proposaland.sh
│   └── proposaland_status.sh
├── logs/
├── output/
├── data/
├── scheduler.py
├── requirements.txt
└── README.md
```

### Log File Locations

- **Scheduler logs**: `logs/scheduler_YYYY-MM-DD.log`
- **System logs**: `logs/proposaland_YYYY-MM-DD.log`
- **Execution summaries**: `logs/execution_summaries/`

### Output File Locations

- **Excel trackers**: `output/proposaland_tracker_YYYY-MM-DD.xlsx`
- **JSON data**: `output/proposaland_opportunities_YYYY-MM-DD.json`

## Scheduling Configuration

### Default Schedule
- **Daily monitoring**: 9:00 AM local time
- **Weekly maintenance**: Sundays at 2:00 AM
- **Monthly cleanup**: 1st of month at 3:00 AM

### Custom Schedule Modification

Edit `scheduler.py` to change timing:
```python
# Change daily execution time
schedule.every().day.at("08:00").do(self.run_with_retry)  # 8 AM instead of 9 AM

# Change weekly maintenance
schedule.every().sunday.at("01:00").do(self.run_weekly_maintenance)  # 1 AM instead of 2 AM
```

## Firewall Configuration

### Required Outbound Connections
- **SMTP**: Port 587 (Gmail)
- **HTTP/HTTPS**: Ports 80/443 (Website scraping)
- **DNS**: Port 53 (Domain resolution)

### Ubuntu UFW Configuration
```bash
# Allow outbound SMTP
sudo ufw allow out 587

# Allow outbound HTTP/HTTPS
sudo ufw allow out 80
sudo ufw allow out 443
```

### CentOS Firewall Configuration
```bash
# Allow outbound SMTP
sudo firewall-cmd --permanent --add-port=587/tcp
sudo firewall-cmd --reload
```

## Troubleshooting Installation Issues

### Python Version Issues
```bash
# Check Python version
python3.11 --version

# If python3.11 not found, try:
python3 --version
python --version

# Install specific Python version if needed
sudo apt install python3.11-full
```

### Permission Issues
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix directory permissions
chmod -R 755 proposaland/
```

### Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf venv/
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Email Authentication Issues

1. **Gmail 2FA Required**: Enable two-factor authentication
2. **App Password**: Generate app-specific password
3. **Less Secure Apps**: Not recommended, use app passwords instead
4. **SMTP Blocked**: Check firewall and ISP restrictions

### Network Connectivity Issues
```bash
# Test internet connectivity
ping google.com

# Test SMTP connectivity
telnet smtp.gmail.com 587

# Test website accessibility
curl -I https://www.devex.com
```

## System Service Setup (Optional)

### Ubuntu Systemd Service

Create service file:
```bash
sudo nano /etc/systemd/system/proposaland.service
```

Service configuration:
```ini
[Unit]
Description=Proposaland Opportunity Monitoring System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/proposaland
ExecStart=/home/ubuntu/proposaland/venv/bin/python /home/ubuntu/proposaland/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable proposaland
sudo systemctl start proposaland
sudo systemctl status proposaland
```

## Backup and Recovery

### Configuration Backup
```bash
# Backup configuration
cp config/proposaland_config.json config/proposaland_config.json.backup

# Backup entire system
tar -czf proposaland-backup-$(date +%Y%m%d).tar.gz proposaland/
```

### Recovery Procedure
```bash
# Restore from backup
tar -xzf proposaland-backup-YYYYMMDD.tar.gz

# Restore configuration
cp config/proposaland_config.json.backup config/proposaland_config.json

# Restart system
./scripts/stop_proposaland.sh
./scripts/start_proposaland.sh
```

## Performance Tuning

### Memory Optimization
```json
{
  "performance": {
    "max_concurrent_scrapers": 5,
    "request_timeout": 30,
    "retry_attempts": 3,
    "cache_size": 1000
  }
}
```

### Log Rotation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/proposaland
```

Logrotate configuration:
```
/home/ubuntu/proposaland/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
```

## Security Hardening

### File Permissions
```bash
# Secure configuration files
chmod 600 config/proposaland_config.json

# Secure log directory
chmod 750 logs/

# Secure scripts
chmod 750 scripts/*.sh
```

### User Security
```bash
# Create dedicated user (optional)
sudo useradd -m -s /bin/bash proposaland
sudo usermod -aG sudo proposaland

# Run system as dedicated user
sudo -u proposaland ./scripts/start_proposaland.sh
```

## Monitoring and Alerts

### System Health Monitoring
```bash
# Set up cron job for health checks
crontab -e

# Add health check every hour
0 * * * * /home/ubuntu/proposaland/scripts/proposaland_status.sh > /dev/null 2>&1
```

### Disk Space Monitoring
```bash
# Monitor disk usage
df -h /home/ubuntu/proposaland

# Set up alert for low disk space
# Add to crontab:
0 6 * * * df -h /home/ubuntu/proposaland | awk 'NR==2{if($5+0 > 80) print "Disk usage high: " $5}' | mail -s "Proposaland Disk Alert" admin@example.com
```

## Upgrade Procedures

### System Upgrade
```bash
# Stop system
./scripts/stop_proposaland.sh

# Backup current installation
tar -czf proposaland-backup-$(date +%Y%m%d).tar.gz proposaland/

# Install new version
# (Follow installation steps with new package)

# Migrate configuration
cp proposaland-backup/config/proposaland_config.json proposaland/config/

# Start upgraded system
./scripts/start_proposaland.sh
```

## Support and Maintenance

### Regular Maintenance Tasks
- **Daily**: Monitor system status and logs
- **Weekly**: Review email reports and system performance
- **Monthly**: Update system packages and clean old files
- **Quarterly**: Review and update configuration

### Support Resources
- System logs in `logs/` directory
- Configuration file: `config/proposaland_config.json`
- Status scripts: `scripts/proposaland_status.sh`
- Test scripts: `test_system.py`

---

**Installation Complete!**

Your Proposaland system should now be running and monitoring opportunities automatically. Check the logs and email notifications to confirm everything is working correctly.

