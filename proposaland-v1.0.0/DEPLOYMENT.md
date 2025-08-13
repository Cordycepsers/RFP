# Proposaland Deployment Guide

## Quick Deployment

### 1. Extract Package
```bash
tar -xzf proposaland-v1.0.0.tar.gz
cd proposaland-v1.0.0/
```

### 2. Run Installation
```bash
./install.sh
```

### 3. Configure Email
```bash
nano config/proposaland_config.json
```

Update email settings:
```json
{
  "email": {
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_email": "majalemaja@pm.me"
  }
}
```

### 4. Test System
```bash
python3 test_system.py
./scripts/proposaland_status.sh test-email
```

### 5. Start Monitoring
```bash
./scripts/start_proposaland.sh
```

## Verification

Check that the system is running:
```bash
./scripts/proposaland_status.sh
```

You should see:
- System status: RUNNING
- Email configuration: Working
- Recent activity logs

## Support

- **Installation Issues**: See INSTALLATION.md
- **Configuration Problems**: See docs/TROUBLESHOOTING.md
- **System Operation**: See README.md

## Files Included

- `scheduler.py` - Main scheduling system
- `proposaland_monitor.py` - Core monitoring logic
- `reference_number_extractor.py` - Reference extraction
- `test_system.py` - System testing
- `config/` - Configuration files
- `src/` - Source code modules
- `scripts/` - Management scripts
- `docs/` - Documentation

## System Requirements

- Python 3.11+
- 4GB RAM minimum
- 10GB disk space
- Internet connection
- Email account (Gmail recommended)

For detailed requirements and troubleshooting, see the documentation files.
