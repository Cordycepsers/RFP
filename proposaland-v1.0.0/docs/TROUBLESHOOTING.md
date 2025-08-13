# Proposaland Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Proposaland Opportunity Monitoring System.

## Quick Diagnostic Commands

```bash
# Check system status
./scripts/proposaland_status.sh

# View recent logs
tail -f logs/scheduler_$(date +%Y-%m-%d).log

# Test email configuration
./scripts/proposaland_status.sh test-email

# Run system test
python3 test_system.py

# Check system health
./scripts/proposaland_status.sh maintenance
```

## Common Issues and Solutions

### 1. System Won't Start

#### Symptoms
- `./scripts/start_proposaland.sh` fails
- No PID file created
- Error messages in startup

#### Diagnostic Steps
```bash
# Check if already running
./scripts/proposaland_status.sh

# Check Python environment
source venv/bin/activate
python3 --version

# Check dependencies
pip list | grep -E "(requests|beautifulsoup4|openpyxl|schedule)"

# Test configuration
python3 -c "import json; json.load(open('config/proposaland_config.json'))"
```

#### Solutions

**Missing Dependencies**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Invalid Configuration**
```bash
# Validate JSON syntax
python3 -c "import json; json.load(open('config/proposaland_config.json'))"

# Fix common JSON errors:
# - Missing commas
# - Trailing commas
# - Unescaped quotes
# - Missing brackets
```

**Permission Issues**
```bash
chmod +x scripts/*.sh
chmod 644 config/proposaland_config.json
```

**Port Already in Use**
```bash
# Check for existing processes
ps aux | grep python | grep scheduler
kill -9 <PID>  # If found
```

### 2. Email Notifications Not Working

#### Symptoms
- System runs but no emails received
- Email test fails
- SMTP authentication errors

#### Diagnostic Steps
```bash
# Test email configuration
./scripts/proposaland_status.sh test-email

# Check email settings
grep -A 10 '"email"' config/proposaland_config.json

# Test SMTP connectivity
telnet smtp.gmail.com 587
```

#### Solutions

**Gmail Authentication Issues**
1. Enable 2-Factor Authentication
2. Generate App-Specific Password:
   - Go to Google Account → Security
   - 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in configuration

**SMTP Configuration**
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-16-char-app-password",
    "recipient_email": "majalemaja@pm.me"
  }
}
```

**Firewall Issues**
```bash
# Allow SMTP port
sudo ufw allow out 587
# Or for CentOS:
sudo firewall-cmd --permanent --add-port=587/tcp
sudo firewall-cmd --reload
```

**Network Connectivity**
```bash
# Test SMTP server connectivity
nc -zv smtp.gmail.com 587
curl -v telnet://smtp.gmail.com:587
```

### 3. No Opportunities Found

#### Symptoms
- System runs successfully
- Email reports show 0 opportunities
- Empty Excel/JSON files

#### Diagnostic Steps
```bash
# Check website accessibility
curl -I https://www.devex.com
curl -I https://procurement-notices.undp.org

# Test individual scrapers
python3 -c "
from src.scrapers.devex_scraper import DevexScraper
scraper = DevexScraper({})
print('Devex accessible:', scraper.test_connection())
"

# Check filtering configuration
grep -A 20 '"keywords"' config/proposaland_config.json
```

#### Solutions

**Website Accessibility Issues**
```bash
# Check internet connection
ping google.com

# Test specific websites
curl -v https://www.devex.com
curl -v https://procurement-notices.undp.org

# Check for IP blocking
curl -H "User-Agent: Mozilla/5.0" https://www.devex.com
```

**Overly Restrictive Filters**
```json
{
  "keywords": {
    "primary": [
      "video", "photo", "multimedia", "design", "visual",
      "campaign", "media", "communication", "creative"
    ],
    "minimum_matches": 1  // Reduce from higher number
  },
  "budget_filters": {
    "min_budget": 1000,    // Reduce minimum
    "max_budget": 1000000  // Increase maximum
  }
}
```

**Geographic Filters Too Strict**
```json
{
  "geographic_filters": {
    "excluded_countries": ["India", "Pakistan"],  // Reduce exclusions
    "excluded_keywords": ["local company only"]   // Be more specific
  }
}
```

### 4. High Memory Usage

#### Symptoms
- System becomes slow
- Out of memory errors
- High CPU usage

#### Diagnostic Steps
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check Proposaland process
ps aux | grep python | grep scheduler

# Monitor system resources
top -p $(cat proposaland.pid)
```

#### Solutions

**Reduce Concurrent Operations**
```json
{
  "performance": {
    "max_concurrent_scrapers": 3,  // Reduce from 5
    "request_timeout": 20,         // Reduce timeout
    "max_retries": 2               // Reduce retries
  }
}
```

**Implement Memory Limits**
```bash
# Limit memory usage with systemd
sudo systemctl edit proposaland

# Add:
[Service]
MemoryLimit=1G
```

**Clear Cache Regularly**
```bash
# Add to weekly maintenance
find logs/ -name "*.log" -mtime +7 -delete
find output/ -name "*.xlsx" -mtime +30 -delete
```

### 5. Website Scraping Failures

#### Symptoms
- Specific websites not being scraped
- Timeout errors in logs
- Partial data extraction

#### Diagnostic Steps
```bash
# Check specific website
curl -v https://www.devex.com/funding-search

# Test with different user agents
curl -H "User-Agent: Mozilla/5.0 (compatible; ProposalandBot/1.0)" https://www.devex.com

# Check for rate limiting
grep -i "rate\|limit\|block" logs/scheduler_*.log
```

#### Solutions

**Rate Limiting Issues**
```json
{
  "scraping": {
    "delay_between_requests": 2.0,  // Increase delay
    "max_requests_per_minute": 30,  // Reduce rate
    "user_agent": "Mozilla/5.0 (compatible; ProposalandBot/1.0)"
  }
}
```

**Website Structure Changes**
```bash
# Update scrapers for changed websites
# Check logs for specific parsing errors
grep -i "parse\|extract\|element" logs/scheduler_*.log

# Test individual scrapers
python3 -c "
from src.scrapers.undp_scraper import UNDPScraper
scraper = UNDPScraper({})
opportunities = scraper.scrape_opportunities()
print(f'Found {len(opportunities)} opportunities')
"
```

**Timeout Issues**
```json
{
  "scraping": {
    "request_timeout": 60,     // Increase timeout
    "read_timeout": 120,       // Increase read timeout
    "connection_timeout": 30   // Increase connection timeout
  }
}
```

### 6. Reference Number Extraction Issues

#### Symptoms
- Low confidence scores
- Missing reference numbers
- Incorrect reference extraction

#### Diagnostic Steps
```bash
# Test reference extraction
python3 reference_number_extractor.py

# Check extraction patterns
grep -A 5 "reference_patterns" config/proposaland_config.json

# Test with sample text
python3 -c "
from reference_number_extractor import ReferenceNumberExtractor
extractor = ReferenceNumberExtractor()
text = 'RFP/2024/001 for multimedia services'
matches = extractor.extract_reference_numbers(text)
print(matches)
"
```

#### Solutions

**Add New Patterns**
```json
{
  "reference_patterns": {
    "undp": [
      "UNDP-[A-Z]{3}-\\d{6}",
      "UNDP/[A-Z]{3}/\\d{4}/\\d{3}"
    ],
    "world_bank": [
      "P\\d{6}",
      "WB-\\d{4}-\\d{3}"
    ],
    "custom": [
      "RFP[/-]\\d{4}[/-]\\d{3}",
      "[A-Z]{2,4}[/-]\\d{4}[/-][A-Z]{2,6}[/-]\\d{3}"
    ]
  }
}
```

**Improve Confidence Scoring**
```json
{
  "reference_extraction": {
    "min_confidence": 0.7,     // Lower threshold
    "context_weight": 0.3,     // Adjust context importance
    "pattern_weight": 0.7      // Adjust pattern importance
  }
}
```

### 7. Excel/JSON Generation Errors

#### Symptoms
- Empty output files
- Corrupted Excel files
- JSON parsing errors

#### Diagnostic Steps
```bash
# Check output directory permissions
ls -la output/

# Test Excel generation
python3 -c "
from src.outputs.excel_generator import ExcelGenerator
generator = ExcelGenerator({})
print('Excel generator initialized successfully')
"

# Validate JSON output
python3 -c "
import json
with open('output/proposaland_opportunities_$(date +%Y-%m-%d).json') as f:
    data = json.load(f)
print('JSON is valid')
"
```

#### Solutions

**Permission Issues**
```bash
chmod 755 output/
chmod 644 output/*.xlsx
chmod 644 output/*.json
```

**Missing Dependencies**
```bash
pip install openpyxl xlsxwriter
```

**Data Encoding Issues**
```python
# In Excel generator, ensure UTF-8 encoding
workbook = openpyxl.Workbook()
# Save with explicit encoding
workbook.save(filename)
```

### 8. Scheduler Not Running Daily

#### Symptoms
- Manual runs work but automatic scheduling fails
- Missing daily reports
- Scheduler stops unexpectedly

#### Diagnostic Steps
```bash
# Check if scheduler is running
ps aux | grep scheduler

# Check scheduler logs
tail -f logs/scheduler_*.log

# Check system time and timezone
date
timedatectl status
```

#### Solutions

**Timezone Issues**
```bash
# Set correct timezone
sudo timedatectl set-timezone America/New_York

# Update scheduler configuration
# Edit scheduler.py to use specific timezone
```

**Process Management**
```bash
# Use systemd service for better process management
sudo systemctl enable proposaland
sudo systemctl start proposaland

# Or use screen/tmux for persistent sessions
screen -S proposaland
./scripts/start_proposaland.sh
# Ctrl+A, D to detach
```

**Cron Job Alternative**
```bash
# Add to crontab as backup
crontab -e

# Add daily execution at 9 AM
0 9 * * * cd /home/ubuntu/proposaland && python3 scheduler.py --run-once
```

## Log Analysis

### Understanding Log Levels

**INFO**: Normal operation messages
```
2025-08-12 09:00:01 | INFO | Starting daily monitoring workflow
2025-08-12 09:00:15 | INFO | Found 25 opportunities from Devex
```

**WARNING**: Non-critical issues
```
2025-08-12 09:01:30 | WARNING | Website timeout, retrying...
2025-08-12 09:02:00 | WARNING | Low confidence reference number: ABC123
```

**ERROR**: Critical issues requiring attention
```
2025-08-12 09:05:00 | ERROR | Failed to send email notification
2025-08-12 09:05:01 | ERROR | SMTP authentication failed
```

### Log File Locations

```bash
# Current day logs
tail -f logs/scheduler_$(date +%Y-%m-%d).log

# Error logs only
grep ERROR logs/scheduler_*.log

# Recent activity
find logs/ -name "*.log" -mtime -1 -exec tail -20 {} \;
```

### Performance Monitoring

```bash
# Monitor system performance
./scripts/proposaland_status.sh

# Check execution times
grep "completed in" logs/scheduler_*.log

# Monitor memory usage
grep -i memory logs/scheduler_*.log
```

## Emergency Procedures

### System Recovery

**Complete System Failure**
```bash
# Stop all processes
./scripts/stop_proposaland.sh --force

# Check system integrity
python3 test_system.py

# Restart with clean state
rm -f proposaland.pid
./scripts/start_proposaland.sh
```

**Data Corruption**
```bash
# Backup current state
tar -czf emergency-backup-$(date +%Y%m%d-%H%M).tar.gz proposaland/

# Restore from known good backup
tar -xzf proposaland-backup-YYYYMMDD.tar.gz

# Restart system
./scripts/start_proposaland.sh
```

### Contact Information

For critical issues that cannot be resolved:

1. **Check system logs**: `logs/scheduler_*.log`
2. **Run diagnostics**: `./scripts/proposaland_status.sh`
3. **Test components**: `python3 test_system.py`
4. **Document error messages** and system state
5. **Contact technical support** with diagnostic information

## Preventive Maintenance

### Daily Checks
```bash
# Automated health check
./scripts/proposaland_status.sh > daily_health_$(date +%Y%m%d).log
```

### Weekly Maintenance
```bash
# Run comprehensive maintenance
./scripts/proposaland_status.sh maintenance

# Check disk space
df -h

# Review error logs
grep ERROR logs/scheduler_*.log | tail -20
```

### Monthly Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Clean old files
find logs/ -name "*.log" -mtime +30 -delete
find output/ -name "*.xlsx" -mtime +60 -delete

# Backup configuration
cp config/proposaland_config.json config/backup_$(date +%Y%m%d).json
```

## Performance Optimization

### Memory Optimization
```json
{
  "performance": {
    "max_concurrent_scrapers": 3,
    "cache_size": 500,
    "batch_size": 50,
    "memory_limit_mb": 1024
  }
}
```

### Network Optimization
```json
{
  "network": {
    "connection_pool_size": 10,
    "keep_alive": true,
    "compression": true,
    "timeout": 30
  }
}
```

### Storage Optimization
```bash
# Compress old logs
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# Archive old outputs
tar -czf archive_$(date +%Y%m).tar.gz output/*.xlsx output/*.json
rm output/*.xlsx output/*.json
```

---

**Need More Help?**

If this troubleshooting guide doesn't resolve your issue:

1. Gather diagnostic information using the commands above
2. Check the system logs for specific error messages
3. Document the exact steps that led to the problem
4. Note your system configuration and environment details
5. Contact technical support with this information

The Proposaland system is designed to be robust and self-healing, but complex systems can encounter unexpected issues. Most problems can be resolved by following the procedures in this guide.

