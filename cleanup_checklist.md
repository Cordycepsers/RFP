# Production Cleanup Checklist

## 🟢 PRODUCTION ARTIFACTS (KEEP)

### Core Application Files
- `scheduler.py` - Main scheduler application
- `proposaland_monitor.py` - Core monitoring script
- `practical-devex-scraper.py` - DevEx scraper
- `gggi_live_scraper.py` - GGGI scraper
- `reference_number_extractor.py` - Reference extraction utility
- `send_manual_report.py` - Manual reporting functionality
- `upload_to_gdrive.py` - Google Drive integration
- `download_from_gdrive.py` - Google Drive download functionality
- `UNGM_advanced.py` - Advanced UNGM scraper

### Source Code Modules (`src/`)
- `src/scrapers/` - All scraper modules (essential for functionality)
- `src/advanced_scrapers/` - Advanced scraper implementations
- `src/filters/` - Filtering and scoring engines
- `src/notifications/` - Email notification system
- `src/outputs/` - Output generation and formatting

### Production Configuration
- `config/proposaland_production.json` - Production configuration
- `requirements.txt` - Python dependencies

### Runtime Scripts (`scripts/`)
- `scripts/deploy_production.sh` - Production deployment
- `scripts/start_proposaland.sh` - Service startup
- `scripts/stop_proposaland.sh` - Service shutdown
- `scripts/proposaland_status.sh` - Status check
- `scripts/validate_config.py` - Configuration validation

---

## 🔴 NON-PRODUCTION ARTIFACTS (REMOVE)

### Development and Documentation Files
- `docs/` - Documentation directory
- `DEPLOYMENT.md` - Deployment documentation
- `DEPLOYMENT_STATUS_REPORT.md` - Status reports
- `EXCEPTION_HANDLING_FIXES.md` - Development notes
- `production_setup.md` - Setup documentation
- `MANIFEST.txt` - Project manifest
- `install.sh` - Installation script

### Test Files and Testing Infrastructure
- `test_*.py` - All test files in root directory
- `tests/` - Test directory
- `.pytest_cache/` - Pytest cache

### Development Configuration
- `config/development_config.json` - Development config
- `config/enhanced_config_template.json` - Config template
- `config/sample_config.json` - Sample config
- `config/staging_config.json` - Staging config
- `config/gggi_scraper_config.json` - Development scraper config

### Build and Development Tools
- `package.json` - Node.js dependencies (for build only)
- `pnpm-lock.yaml` - Package manager lockfile
- `node_modules/` - Node.js modules
- `.venv/` - Python virtual environment

### Runtime Artifacts and Logs
- `logs/` - Log files directory
- `output/` - Generated output files
- `data/snapshots/` - HTML snapshots
- `data/` - Test data and analysis files

### Development Environment Files
- `.env` - Environment variables (contains secrets!)
- `.env.example` - Environment template
- `.DS_Store` files - macOS system files
- `.vscode/` - VS Code settings
- `.github/` - GitHub workflows and CI/CD
- `.gitignore` - Git ignore rules

### Archives and Backups
- `Data Dashboard Application.zip` - Archive file
- Any `*.bak` files

### Credential Files (⚠️ SECURITY RISK)
- `google-credentials*.json` - Google API credentials
- `client_secret_*.json` - OAuth secrets

---

## 📋 CLEANUP ACTIONS

### Phase 1: Safety Backup
```bash
# Create backup branch and tag
git checkout -b cleanup-for-prod
git tag pre-cleanup-$(date +%Y%m%d)
```

### Phase 2: File Removal
```bash
# Remove development files
rm -rf docs/ tests/ logs/ output/ data/ node_modules/ .venv/ .vscode/ .github/

# Remove development configurations  
rm config/development_config.json config/enhanced_config_template.json config/sample_config.json config/staging_config.json config/gggi_scraper_config.json

# Remove documentation and notes
rm *.md install.sh MANIFEST.txt

# Remove test files
rm test_*.py 

# Remove build artifacts
rm package.json pnpm-lock.yaml

# Remove development environment and system files
rm .env .env.example
find . -name ".DS_Store" -delete

# Remove credentials (ensure they're in environment variables instead)
rm google-credentials*.json client_secret_*.json

# Remove archives
rm "Data Dashboard Application.zip"
```

### Phase 3: Staging and Review
```bash
git add -A
git commit -m "chore: remove dev-only files for production deployment"
git push --set-upstream origin cleanup-for-prod
```

---

## 🔍 POST-CLEANUP VALIDATION

After cleanup, ensure these core files remain:
- [ ] `scheduler.py` 
- [ ] `proposaland_monitor.py`
- [ ] `src/` directory with all modules
- [ ] `config/proposaland_production.json`
- [ ] `requirements.txt`
- [ ] Production scripts in `scripts/`

## 🚨 SECURITY NOTES

1. **Never commit credentials** - All `*.json` credential files must be environment variables
2. **Environment variables** - Set up proper secret management for production
3. **Configuration** - Ensure production config references environment variables only

---

**Generated on**: $(date)  
**Review required by**: Development Team  
**Estimated cleanup impact**: ~60% file reduction
