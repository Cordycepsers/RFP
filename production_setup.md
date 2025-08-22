# Proposaland Production Setup Guide

## 🚀 Production Configuration Overview

This guide provides step-by-step instructions for deploying Proposaland in a production environment with the comprehensive configuration file.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.8+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 20GB free space minimum
- **Network**: Stable internet connection

### Required Packages
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git cron
```

## 🔧 Installation Steps

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url> /opt/proposaland
cd /opt/proposaland

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Setup

#### Copy Production Configuration
```bash
# Use the production configuration
cp config/proposaland_production_config.json config/proposaland_config.json
```

#### Configure Email Settings
Edit `config/proposaland_config.json` and update the email section:

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "sender_email": "your-monitoring-email@gmail.com",
    "sender_password": "your-app-specific-password",
    "recipient_email": "majalemaja@pm.me"
  }
}
```

**Important**: Use App-Specific Passwords for Gmail:
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App-Specific Password: Google Account → Security → App passwords
3. Use this password in the configuration

### 3. Directory Structure Setup
```bash
# Create required directories
mkdir -p logs output data temp backups

# Set permissions
chmod 755 logs output data temp backups
chmod +x scripts/*.sh
```

### 4. Environment Variables (Optional)
Create `.env` file for sensitive data:
```bash
# .env file
PROPOSALAND_EMAIL_PASSWORD=your-app-specific-password
PROPOSALAND_SMTP_SERVER=smtp.gmail.com
PROPOSALAND_RECIPIENT=majalemaja@pm.me
```

## ⏰ Scheduling Setup

### 1. Cron Job Configuration
```bash
# Edit crontab
crontab -e

# Add daily execution at 6:00 AM UTC
0 6 * * * cd /opt/proposaland && /opt/proposaland/venv/bin/python proposaland_monitor.py >> logs/cron.log 2>&1

# Add weekly cleanup at 2:00 AM Sunday
0 2 * * 0 cd /opt/proposaland && /opt/proposaland/scripts/cleanup.sh >> logs/cleanup.log 2>&1
```

### 2. Systemd Service (Alternative)
Create `/etc/systemd/system/proposaland.service`:
```ini
[Unit]
Description=Proposaland Opportunity Monitor
After=network.target

[Service]
Type=oneshot
User=proposaland
WorkingDirectory=/opt/proposaland
Environment=PATH=/opt/proposaland/venv/bin
ExecStart=/opt/proposaland/venv/bin/python proposaland_monitor.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create timer `/etc/systemd/system/proposaland.timer`:
```ini
[Unit]
Description=Run Proposaland daily
Requires=proposaland.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the service:
```bash
sudo systemctl enable proposaland.timer
sudo systemctl start proposaland.timer
```

## 🔒 Security Configuration

### 1. User Setup
```bash
# Create dedicated user
sudo useradd -r -s /bin/bash -d /opt/proposaland proposaland
sudo chown -R proposaland:proposaland /opt/proposaland
```

### 2. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow out 80,443
```

### 3. Log Rotation
Create `/etc/logrotate.d/proposaland`:
```
/opt/proposaland/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 proposaland proposaland
    postrotate
        systemctl reload proposaland || true
    endscript
}
```

## 📊 Monitoring and Maintenance

### 1. Health Check Script
Create `scripts/health_check.sh`:
```bash
#!/bin/bash
cd /opt/proposaland

# Check if last run was successful
if [ -f "logs/last_run.log" ]; then
    last_run=$(stat -c %Y logs/last_run.log)
    current_time=$(date +%s)
    time_diff=$((current_time - last_run))
    
    # Alert if last run was more than 25 hours ago
    if [ $time_diff -gt 90000 ]; then
        echo "WARNING: Proposaland hasn't run in $((time_diff/3600)) hours"
        # Send alert email here
    fi
fi

# Check disk space
disk_usage=$(df /opt/proposaland | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -gt 85 ]; then
    echo "WARNING: Disk usage is ${disk_usage}%"
fi

# Check log file sizes
find logs/ -name "*.log" -size +100M -exec echo "WARNING: Large log file: {}" \;
```

### 2. Backup Script
Create `scripts/backup.sh`:
```bash
#!/bin/bash
cd /opt/proposaland

# Create backup directory with timestamp
backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# Backup configuration and data
cp -r config/ "$backup_dir/"
cp -r output/ "$backup_dir/"
cp -r data/ "$backup_dir/"

# Compress backup
tar -czf "$backup_dir.tar.gz" "$backup_dir"
rm -rf "$backup_dir"

# Keep only last 7 days of backups
find backups/ -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $backup_dir.tar.gz"
```

## 🔍 Configuration Customization

### 1. Scraper Priority Adjustment
Modify scraper priorities based on your needs:
```json
{
  "scrapers": {
    "devex": {"priority": 1},      // Highest priority
    "undp": {"priority": 1},       // Highest priority
    "worldbank": {"priority": 1},  // Highest priority
    "ungm": {"priority": 2},       // Medium priority
    "reliefweb": {"priority": 2}   // Medium priority
  }
}
```

### 2. Keyword Customization
Add industry-specific keywords:
```json
{
  "keywords": {
    "primary": [
      "video", "multimedia", "design", "campaign",
      "your-specific-keywords-here"
    ]
  }
}
```

### 3. Geographic Filtering
Adjust geographic filters for your target regions:
```json
{
  "geographic_filters": {
    "excluded_countries": ["India", "Pakistan", "China"],
    "included_exceptions": ["Nepal", "Bhutan"],
    "focus_regions": ["Africa", "Latin America", "Eastern Europe"]
  }
}
```

## 📧 Email Configuration Examples

### Gmail Configuration
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true
  }
}
```

### Outlook/Hotmail Configuration
```json
{
  "email": {
    "smtp_server": "smtp-mail.outlook.com",
    "smtp_port": 587,
    "use_tls": true
  }
}
```

### Custom SMTP Configuration
```json
{
  "email": {
    "smtp_server": "your-smtp-server.com",
    "smtp_port": 587,
    "use_tls": true,
    "use_ssl": false
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Email Not Sending
- Check SMTP credentials
- Verify App-Specific Password for Gmail
- Check firewall settings for SMTP ports
- Test with: `python -c "import smtplib; print('SMTP available')"`

#### 2. Scrapers Failing
- Check internet connectivity
- Verify website accessibility
- Review rate limiting settings
- Check logs: `tail -f logs/proposaland.log`

#### 3. High Memory Usage
- Reduce `max_concurrent_scrapers` in config
- Lower `max_pages` for individual scrapers
- Enable `cache_enabled` for better performance

#### 4. Disk Space Issues
- Enable `auto_cleanup` in config
- Reduce `backup_retention_days`
- Set up log rotation properly

### Log Analysis
```bash
# View recent errors
grep -i error logs/proposaland.log | tail -20

# Check scraper performance
grep -i "scraping completed" logs/proposaland.log | tail -10

# Monitor email sending
grep -i "email sent" logs/proposaland.log | tail -5
```

## 📈 Performance Optimization

### 1. Resource Allocation
```json
{
  "performance": {
    "max_workers": 3,           // Adjust based on CPU cores
    "memory_limit": "2GB",      // Adjust based on available RAM
    "connection_pooling": true,
    "cache_duration": 3600      // 1 hour cache
  }
}
```

### 2. Scraper Optimization
```json
{
  "scrapers": {
    "high_priority_scraper": {
      "request_delay": 1,       // Faster for reliable sites
      "timeout": 30
    },
    "problematic_scraper": {
      "request_delay": 5,       // Slower for rate-limited sites
      "timeout": 60,
      "max_retries": 2
    }
  }
}
```

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Review logs for errors
2. **Monthly**: Update keywords and filters
3. **Quarterly**: Review scraper performance
4. **Annually**: Update dependencies and security patches

### Update Procedure
```bash
# Backup current configuration
cp config/proposaland_config.json config/proposaland_config.backup

# Pull updates
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Test configuration
python test_system.py

# Restart services
sudo systemctl restart proposaland.timer
```

## 📞 Support and Monitoring

### Health Monitoring URLs
- System status: Check log files in `/opt/proposaland/logs/`
- Last run status: `cat logs/last_run.log`
- Error summary: `grep -c ERROR logs/proposaland.log`

### Performance Metrics
- Opportunities found per day
- Scraper success rates
- Email delivery status
- System resource usage

This production configuration provides a robust, scalable, and maintainable setup for the Proposaland opportunity monitoring system.

