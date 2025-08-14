#!/bin/bash
# Proposaland System Packaging Script
# Creates a deployment-ready package of the complete system

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PACKAGE_NAME="proposaland-v1.0.0"
PACKAGE_DIR="/tmp/$PACKAGE_NAME"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Create package directory
create_package_structure() {
    log "Creating package structure..."
    
    rm -rf "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR"
    
    # Create directory structure
    mkdir -p "$PACKAGE_DIR"/{config,src,scripts,logs,output,data,docs}
    mkdir -p "$PACKAGE_DIR"/src/{scrapers,filters,outputs,notifications}
    
    success "Package structure created"
}

# Copy core files
copy_core_files() {
    log "Copying core system files..."
    
    # Main scripts
    cp "$PROJECT_DIR"/scheduler.py "$PACKAGE_DIR"/
    cp "$PROJECT_DIR"/proposaland_monitor.py "$PACKAGE_DIR"/
    cp "$PROJECT_DIR"/reference_number_extractor.py "$PACKAGE_DIR"/
    cp "$PROJECT_DIR"/test_system.py "$PACKAGE_DIR"/
    cp "$PROJECT_DIR"/requirements.txt "$PACKAGE_DIR"/
    
    # Configuration
    cp "$PROJECT_DIR"/config/proposaland_config.json "$PACKAGE_DIR"/config/
    
    # Source code
    cp -r "$PROJECT_DIR"/src/* "$PACKAGE_DIR"/src/
    
    # Scripts
    cp "$PROJECT_DIR"/scripts/*.sh "$PACKAGE_DIR"/scripts/
    chmod +x "$PACKAGE_DIR"/scripts/*.sh
    
    success "Core files copied"
}

# Copy documentation
copy_documentation() {
    log "Copying documentation..."
    
    cp "$PROJECT_DIR"/README.md "$PACKAGE_DIR"/
    cp "$PROJECT_DIR"/INSTALLATION.md "$PACKAGE_DIR"/docs/
    cp "$PROJECT_DIR"/TROUBLESHOOTING.md "$PACKAGE_DIR"/docs/
    cp "$PROJECT_DIR"/ARCHITECTURE.md "$PACKAGE_DIR"/docs/
    
    # Copy analysis files
    if [ -d "$PROJECT_DIR/data" ]; then
        cp "$PROJECT_DIR"/data/*.md "$PACKAGE_DIR"/data/ 2>/dev/null || true
    fi
    
    success "Documentation copied"
}

# Create sample configuration
create_sample_config() {
    log "Creating sample configuration..."
    
    # Create a sanitized sample configuration
    cat > "$PACKAGE_DIR"/config/sample_config.json << 'EOF'
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-specific-password",
    "recipient_email": "majalemaja@pm.me"
  },
  "scheduler": {
    "daily_time": "09:00",
    "timezone": "UTC",
    "max_retries": 3,
    "retry_delay_minutes": 30
  },
  "keywords": {
    "primary": [
      "video", "photo", "film", "multimedia", "design", "visual",
      "campaign", "podcasts", "virtual event", "media", "animation",
      "promotion", "communication", "audiovisual"
    ],
    "secondary": [
      "creative", "content", "digital", "marketing", "branding",
      "graphics", "illustration", "documentary", "photography"
    ],
    "weights": {
      "primary": 1.0,
      "secondary": 0.7
    },
    "minimum_matches": 1
  },
  "geographic_filters": {
    "excluded_countries": [
      "India", "Pakistan", "China", "Bangladesh", "Sri Lanka", "Myanmar"
    ],
    "excluded_keywords": [
      "local company", "national only", "domestic only"
    ],
    "preferred_regions": [
      "Africa", "Latin America", "Eastern Europe", "Central Asia", "Nepal"
    ]
  },
  "budget_filters": {
    "min_budget": 5000,
    "max_budget": 500000,
    "currency": "USD"
  },
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
  },
  "target_websites": {
    "high_priority": [
      {
        "name": "Devex",
        "url": "https://www.devex.com/funding-search",
        "scraper_type": "devex",
        "update_frequency": "daily"
      },
      {
        "name": "UNDP",
        "url": "https://procurement-notices.undp.org/search.cfm",
        "scraper_type": "undp",
        "update_frequency": "daily"
      },
      {
        "name": "World Bank",
        "url": "https://projects.worldbank.org/en/projects-operations/procurement",
        "scraper_type": "worldbank",
        "update_frequency": "daily"
      }
    ],
    "medium_priority": [
      {
        "name": "UNGM",
        "url": "https://www.ungm.org/Account/Inbox",
        "scraper_type": "ungm",
        "update_frequency": "daily"
      },
      {
        "name": "Global Fund",
        "url": "https://www.theglobalfund.org/en/business-opportunities/",
        "scraper_type": "globalfund",
        "update_frequency": "daily"
      }
    ]
  },
  "performance": {
    "max_concurrent_scrapers": 5,
    "request_timeout": 30,
    "retry_attempts": 3,
    "delay_between_requests": 1.0
  }
}
EOF
    
    success "Sample configuration created"
}

# Create installation script
create_installation_script() {
    log "Creating installation script..."
    
    cat > "$PACKAGE_DIR"/install.sh << 'EOF'
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
EOF
    
    chmod +x "$PACKAGE_DIR"/install.sh
    
    success "Installation script created"
}

# Create deployment guide
create_deployment_guide() {
    log "Creating deployment guide..."
    
    cat > "$PACKAGE_DIR"/DEPLOYMENT.md << 'EOF'
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
EOF
    
    success "Deployment guide created"
}

# Create package archive
create_archive() {
    log "Creating deployment archive..."
    
    cd /tmp
    tar -czf "$PACKAGE_NAME-$TIMESTAMP.tar.gz" "$PACKAGE_NAME"
    
    # Move to project directory
    mv "$PACKAGE_NAME-$TIMESTAMP.tar.gz" "$PROJECT_DIR"/
    
    # Create latest symlink
    cd "$PROJECT_DIR"
    ln -sf "$PACKAGE_NAME-$TIMESTAMP.tar.gz" "proposaland-latest.tar.gz"
    
    success "Archive created: $PACKAGE_NAME-$TIMESTAMP.tar.gz"
}

# Generate package manifest
create_manifest() {
    log "Creating package manifest..."
    
    cat > "$PACKAGE_DIR"/MANIFEST.txt << EOF
Proposaland Opportunity Monitoring System v1.0.0
Package created: $(date)
Package ID: $PACKAGE_NAME-$TIMESTAMP

CONTENTS:
========

Core System:
- scheduler.py                    # Main scheduling system
- proposaland_monitor.py         # Core monitoring logic  
- reference_number_extractor.py  # Reference number extraction
- test_system.py                 # System testing suite
- requirements.txt               # Python dependencies
- install.sh                     # Installation script

Configuration:
- config/proposaland_config.json # Main configuration
- config/sample_config.json      # Sample configuration

Source Code:
- src/scrapers/                  # Website scrapers
- src/filters/                   # Filtering and scoring
- src/outputs/                   # Excel and JSON generation
- src/notifications/             # Email notifications

Management Scripts:
- scripts/start_proposaland.sh   # Start system
- scripts/stop_proposaland.sh    # Stop system
- scripts/proposaland_status.sh  # Status and maintenance

Documentation:
- README.md                      # Main documentation
- DEPLOYMENT.md                  # Quick deployment guide
- docs/INSTALLATION.md           # Detailed installation
- docs/TROUBLESHOOTING.md        # Troubleshooting guide
- docs/ARCHITECTURE.md           # System architecture

Directories:
- logs/                          # Log files (empty)
- output/                        # Generated files (empty)
- data/                          # Analysis data

FEATURES:
=========
- Automated daily monitoring of 23 development organizations
- Reference number extraction with pattern recognition
- Intelligent filtering and scoring (keywords, geography, budget)
- Excel tracker and JSON output generation
- Email notifications with attachments
- Comprehensive logging and monitoring
- Automated scheduling and maintenance

REQUIREMENTS:
=============
- Python 3.11+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space
- Internet connection
- Email account for notifications

INSTALLATION:
=============
1. Extract package: tar -xzf $PACKAGE_NAME-$TIMESTAMP.tar.gz
2. Run installer: ./install.sh
3. Configure email: edit config/proposaland_config.json
4. Test system: python3 test_system.py
5. Start monitoring: ./scripts/start_proposaland.sh

For detailed instructions, see DEPLOYMENT.md and docs/INSTALLATION.md

SUPPORT:
========
- System logs: logs/ directory
- Status check: ./scripts/proposaland_status.sh
- Test system: python3 test_system.py
- Documentation: README.md and docs/ directory

Package integrity: $(find "$PACKAGE_DIR" -type f | wc -l) files included
EOF
    
    success "Package manifest created"
}

# Validate package
validate_package() {
    log "Validating package..."
    
    # Check required files
    required_files=(
        "scheduler.py"
        "proposaland_monitor.py"
        "reference_number_extractor.py"
        "test_system.py"
        "requirements.txt"
        "install.sh"
        "README.md"
        "DEPLOYMENT.md"
        "config/proposaland_config.json"
        "config/sample_config.json"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PACKAGE_DIR/$file" ]; then
            error "Missing required file: $file"
            exit 1
        fi
    done
    
    # Check directory structure
    required_dirs=(
        "src/scrapers"
        "src/filters"
        "src/outputs"
        "src/notifications"
        "scripts"
        "docs"
        "config"
        "logs"
        "output"
        "data"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$PACKAGE_DIR/$dir" ]; then
            error "Missing required directory: $dir"
            exit 1
        fi
    done
    
    # Check script permissions
    for script in "$PACKAGE_DIR"/scripts/*.sh; do
        if [ ! -x "$script" ]; then
            error "Script not executable: $script"
            exit 1
        fi
    done
    
    success "Package validation passed"
}

# Main execution
main() {
    echo "=================================================="
    echo "    Proposaland System Packaging Tool            "
    echo "=================================================="
    echo ""
    
    cd "$PROJECT_DIR"
    
    create_package_structure
    copy_core_files
    copy_documentation
    create_sample_config
    create_installation_script
    create_deployment_guide
    create_manifest
    validate_package
    create_archive
    
    # Cleanup
    rm -rf "$PACKAGE_DIR"
    
    echo ""
    echo "=================================================="
    echo "Package created successfully!"
    echo ""
    echo "Archive: $PACKAGE_NAME-$TIMESTAMP.tar.gz"
    echo "Latest: proposaland-latest.tar.gz"
    echo ""
    echo "To deploy:"
    echo "1. Transfer the archive to target system"
    echo "2. Extract: tar -xzf $PACKAGE_NAME-$TIMESTAMP.tar.gz"
    echo "3. Install: cd $PACKAGE_NAME && ./install.sh"
    echo "4. Configure: edit config/proposaland_config.json"
    echo "5. Start: ./scripts/start_proposaland.sh"
    echo "=================================================="
}

# Run main function
main "$@"

