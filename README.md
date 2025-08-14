# Proposaland Opportunity Monitoring System

**Version:** 1.0.0  
**Author:** Manus AI  
**Date:** August 2025

## Overview

Proposaland is an automated opportunity monitoring system designed to search 23 development organization websites daily for multimedia and creative opportunities. The system extracts reference numbers, filters relevant opportunities, generates Excel trackers, and sends email notifications with comprehensive scoring and prioritization.

## Key Features

### 🎯 **Automated Monitoring**
- Daily monitoring of 23 development organization websites
- Scheduled execution at 9:00 AM daily
- Automatic retry mechanisms with exponential backoff
- Comprehensive error handling and logging

### 🔍 **Intelligent Filtering**
- **Keyword Filtering**: Targets multimedia, video, photo, design, communication opportunities
- **Geographic Filtering**: Excludes India, Pakistan, most of Asia (except Nepal), and China
- **Budget Filtering**: Focuses on opportunities between $5,000 - $500,000
- **Reference Number Extraction**: Advanced pattern recognition with confidence scoring

### 📊 **Smart Scoring & Prioritization**
- **Relevance Scoring**: 0.0-1.0 scale based on multiple criteria
- **Priority Classification**: Critical, High, Medium, Low
- **Weighted Scoring**: Keywords (40%), Budget (25%), Deadline (20%), Geographic (15%)

### 📈 **Professional Reporting**
- **Excel Trackers**: Formatted spreadsheets with reference number columns
- **JSON Outputs**: Structured data for integration
- **Email Notifications**: HTML emails with attachments
- **Summary Analytics**: Statistics and insights

### 🚨 **Alert System**
- **Daily Reports**: Comprehensive opportunity summaries
- **Urgent Alerts**: Immediate notifications for critical opportunities
- **Email Attachments**: Excel and JSON files included

## Target Organizations

The system monitors the following 23 development organizations:

### High Priority Sources
- **Devex** - Development funding and opportunities
- **UNDP** - United Nations Development Programme
- **World Bank** - Global development projects
- **UNGM** - UN Global Marketplace

### Medium Priority Sources
- **Global Fund** - Health and development funding
- **IUCN** - Environmental conservation projects
- **Development Aid** - International development tenders
- **NRC** - Norwegian Refugee Council
- **BirdLife International** - Conservation projects
- **DRC** - Danish Refugee Council

### Additional Sources
- **ReliefWeb** - Humanitarian opportunities
- **Heifer International** - Agricultural development
- **Save the Children** - Child welfare projects
- **Mercy Corps** - Emergency response and development
- **International Rescue Committee** - Refugee assistance
- **African Development Bank** - African development projects
- **And 7 more specialized organizations**

## System Architecture

```
Proposaland System
├── Core Components
│   ├── Web Scrapers (23 organization-specific)
│   ├── Reference Number Extractor
│   ├── Filtering Engine
│   └── Scoring Algorithm
├── Output Generation
│   ├── Excel Generator
│   ├── JSON Generator
│   └── Email Notifier
├── Automation
│   ├── Daily Scheduler
│   ├── Monitoring Scripts
│   └── Maintenance Tools
└── Configuration
    ├── Target Websites
    ├── Keywords & Filters
    └── Email Settings
```

## Quick Start

### Prerequisites
- Python 3.11+
- Internet connection
- Email account for notifications

### Installation
```bash
# 1. Extract the Proposaland system
cd proposaland/

# 2. Start the system
./scripts/start_proposaland.sh
```

### Configuration
1. Edit `config/proposaland_config.json`
2. Configure email settings
3. Customize keywords and filters
4. Set geographic preferences

### Usage
```bash
# Start monitoring
./scripts/start_proposaland.sh

# Check status
./scripts/proposaland_status.sh

# Stop monitoring
./scripts/stop_proposaland.sh

# Run maintenance
./scripts/proposaland_status.sh maintenance
```

## Configuration Guide

### Email Configuration
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_email": "majalemaja@pm.me"
  }
}
```

### Keyword Customization
```json
{
  "keywords": {
    "primary": ["video", "photo", "multimedia", "design"],
    "secondary": ["campaign", "communication", "media"],
    "weights": {
      "primary": 1.0,
      "secondary": 0.7
    }
  }
}
```

### Geographic Filters
```json
{
  "geographic_filters": {
    "excluded_countries": ["India", "Pakistan", "China"],
    "excluded_regions": ["South Asia"],
    "preferred_regions": ["Africa", "Latin America", "Eastern Europe"]
  }
}
```

## Output Files

### Excel Tracker Format
- **Reference Number** - Extracted procurement reference
- **Title** - Opportunity title
- **Organization** - Source organization
- **Location** - Geographic location
- **Budget** - Estimated budget range
- **Deadline** - Submission deadline
- **Priority** - Critical/High/Medium/Low
- **Score** - Relevance score (0.0-1.0)
- **Keywords** - Matched keywords
- **URL** - Source link

### JSON Data Structure
```json
{
  "metadata": {
    "generated_timestamp": "2025-08-12T09:00:00",
    "total_opportunities": 25,
    "system_version": "1.0.0"
  },
  "summary": {
    "priority_breakdown": {
      "Critical": 3,
      "High": 8,
      "Medium": 12,
      "Low": 2
    },
    "average_score": 0.67
  },
  "opportunities": [...]
}
```

## Monitoring & Maintenance

### Daily Operations
- System runs automatically at 9:00 AM daily
- Email reports sent to majalemaja@pm.me
- Logs stored in `logs/` directory
- Output files saved in `output/` directory

### Weekly Maintenance
- Automatic log cleanup (30-day retention)
- System health checks
- Email configuration testing
- Performance monitoring

### Monthly Tasks
- Data archiving
- Analytics generation
- System optimization
- Configuration review

## Troubleshooting

### Common Issues

#### System Not Starting
```bash
# Check system status
./scripts/proposaland_status.sh

# View recent logs
tail -f logs/scheduler_*.log

# Test email configuration
./scripts/proposaland_status.sh test-email
```

#### No Opportunities Found
1. Check internet connection
2. Verify website accessibility
3. Review keyword configuration
4. Check geographic filters

#### Email Not Sending
1. Verify SMTP settings
2. Check email credentials
3. Test email configuration
4. Review firewall settings

### Log Files
- **Scheduler Logs**: `logs/scheduler_YYYY-MM-DD.log`
- **System Logs**: `logs/proposaland_YYYY-MM-DD.log`
- **Error Logs**: `logs/errors_YYYY-MM-DD.log`
- **Execution Summaries**: `logs/execution_summaries/`

### Support Commands
```bash
# System status and health
./scripts/proposaland_status.sh

# Detailed log analysis
./scripts/proposaland_status.sh logs

# Run maintenance tasks
./scripts/proposaland_status.sh maintenance

# Test single monitoring cycle
./scripts/proposaland_status.sh test-run
```

## Advanced Configuration

### Custom Website Sources
Add new organizations to monitor by editing the configuration:

```json
{
  "target_websites": {
    "high_priority": [
      {
        "name": "New Organization",
        "url": "https://example.org/tenders",
        "scraper_type": "generic",
        "update_frequency": "daily"
      }
    ]
  }
}
```

### Scoring Algorithm Tuning
Adjust scoring weights for different criteria:

```json
{
  "scoring": {
    "weights": {
      "keyword_relevance": 0.40,
      "budget_range": 0.25,
      "deadline_urgency": 0.20,
      "geographic_preference": 0.15
    },
    "thresholds": {
      "critical": 0.80,
      "high": 0.65,
      "medium": 0.45,
      "low": 0.25
    }
  }
}
```

### Email Template Customization
Modify email templates in `src/notifications/templates/` to customize the appearance and content of notification emails.

## Security Considerations

### Email Security
- Use app-specific passwords for Gmail
- Store credentials securely
- Enable two-factor authentication
- Regular password rotation

### System Security
- Run with minimal privileges
- Regular system updates
- Monitor log files for anomalies
- Secure configuration files

### Data Privacy
- Opportunity data is processed locally
- No data sent to external services
- Automatic cleanup of old files
- Secure email transmission

## Performance Optimization

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for logs and outputs
- **Network**: Stable internet connection

### Optimization Tips
- Adjust scraping intervals based on website update frequency
- Implement caching for frequently accessed data
- Use parallel processing for multiple websites
- Regular cleanup of old files and logs

## API Integration

The system generates JSON outputs that can be integrated with other tools:

```python
import json

# Load opportunity data
with open('output/proposaland_opportunities_2025-08-12.json', 'r') as f:
    data = json.load(f)

# Access opportunities
opportunities = data['opportunities']
for opp in opportunities:
    if opp['priority'] == 'Critical':
        print(f"Critical: {opp['title']}")
```

## Version History

### Version 1.0.0 (August 2025)
- Initial release
- 23 organization monitoring
- Reference number extraction
- Excel and JSON output generation
- Email notification system
- Automated scheduling
- Comprehensive filtering and scoring

## License

This system is proprietary software developed for specific organizational use. All rights reserved.

## Support

For technical support, configuration assistance, or feature requests, please contact the development team or refer to the troubleshooting section above.

---

**Proposaland Opportunity Monitoring System**  
*Automated Intelligence for Development Opportunities*

