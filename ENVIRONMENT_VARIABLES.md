# Production Environment Variables

This document lists all environment variables required for production deployment.

## 🔐 Required (Critical - Must be Set)

### Email Configuration
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@domain.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAIL=notifications@domain.com
```

### Security Keys
```bash
SECRET_KEY=your-secret-key-32-chars-min
ENCRYPTION_KEY=your-encryption-key-32-chars
JWT_SECRET=your-jwt-secret-key
```

### Database Configuration
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### External API Credentials
```bash
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_SHEETS_ID=your-sheet-id
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
```

---

## ⚙️ Optional (With Defaults)

### Application Settings
```bash
APP_NAME="Proposaland Opportunity Monitoring System"
APP_VERSION="1.0.0"
TIMEZONE="UTC"
LOG_LEVEL="INFO"
```

### Performance Tuning
```bash
MAX_CONCURRENT_SCRAPERS=3
GLOBAL_TIMEOUT=60
RETRY_ATTEMPTS=3
RETRY_DELAY=5
```

### Scheduling
```bash
SCHEDULING_ENABLED=true
DAILY_RUN_TIME="06:00"
SCHEDULE_TIMEZONE="UTC"
MAX_EXECUTION_TIME=7200
```

### Database Pool Settings
```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### Logging Configuration
```bash
LOG_FORMAT="json"
LOG_FILE_ENABLED=true
LOG_FILE_PATH="/var/log/proposaland/app.log"
LOG_ROTATION_ENABLED=true
LOG_MAX_FILE_SIZE="10MB"
LOG_BACKUP_COUNT=5
LOG_CONSOLE_ENABLED=false
```

### Monitoring & Health Checks
```bash
MONITORING_ENABLED=true
HEALTH_CHECK_PORT=8080
METRICS_ENABLED=true
METRICS_PORT=9090
PERFORMANCE_TRACKING=true
```

### Cache Configuration (Redis)
```bash
CACHE_TYPE="redis"
REDIS_URL="redis://localhost:6379/0"
CACHE_DEFAULT_TTL=3600
CACHE_MAX_MEMORY="256MB"
CACHE_EVICTION_POLICY="allkeys-lru"
```

### Storage Configuration
```bash
STORAGE_TYPE="s3"
S3_BUCKET_NAME="your-bucket-name"
S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="your-access-key"
AWS_SECRET_ACCESS_KEY="your-secret-key"
LOCAL_STORAGE_PATH="/app/data"
STORAGE_RETENTION_DAYS=90
```

### Feature Flags
```bash
FEATURE_ADVANCED_SCRAPERS=true
FEATURE_AI_SCORING=false
FEATURE_REALTIME_NOTIFICATIONS=true
FEATURE_DATA_EXPORT=true
FEATURE_ADMIN_DASHBOARD=true
FEATURE_WEBHOOK_INTEGRATION=false
```

### Budget Filtering
```bash
BUDGET_FILTERS_ENABLED=true
MIN_BUDGET=5000
MAX_BUDGET=500000
EUR_RATE=1.1
GBP_RATE=1.25
CHF_RATE=1.05
CAD_RATE=0.75
AUD_RATE=0.65
```

### Scoring Weights
```bash
SCORE_KEYWORD_WEIGHT=0.4
SCORE_BUDGET_WEIGHT=0.2
SCORE_DEADLINE_WEIGHT=0.2
SCORE_ORGANIZATION_WEIGHT=0.1
SCORE_REFERENCE_WEIGHT=0.1
SCORE_CRITICAL_THRESHOLD=0.8
SCORE_HIGH_THRESHOLD=0.6
SCORE_MEDIUM_THRESHOLD=0.4
SCORE_LOW_THRESHOLD=0.2
```

### Scraper Configuration
```bash
# DevEx Scraper
SCRAPER_DEVEX_ENABLED=true
SCRAPER_DEVEX_PRIORITY=1
SCRAPER_DEVEX_DELAY=3
SCRAPER_DEVEX_MAX_JOBS=100
SCRAPER_DEVEX_MAX_NEWS=50
SCRAPER_DEVEX_TIMEOUT=45
SCRAPER_DEVEX_MAX_RETRIES=3

# UNDP Scraper
SCRAPER_UNDP_ENABLED=true
SCRAPER_UNDP_PRIORITY=1
SCRAPER_UNDP_DELAY=2
SCRAPER_UNDP_MAX_PAGES=10
SCRAPER_UNDP_TIMEOUT=30
SCRAPER_UNDP_MAX_RETRIES=3

# World Bank Scraper
SCRAPER_WB_ENABLED=true
SCRAPER_WB_PRIORITY=1
SCRAPER_WB_DELAY=2
SCRAPER_WB_MAX_PAGES=8
SCRAPER_WB_TIMEOUT=40
SCRAPER_WB_MAX_RETRIES=3
```

### Output Configuration
```bash
OUTPUT_EXCEL_ENABLED=true
OUTPUT_EXCEL_TEMPLATE="proposaland_opportunities_{date}.xlsx"
OUTPUT_EXCEL_INCLUDE_REF=true
OUTPUT_EXCEL_INCLUDE_KEYWORDS=true
OUTPUT_EXCEL_INCLUDE_SCORE=true
OUTPUT_EXCEL_MAX_DESC_LENGTH=500
OUTPUT_EXCEL_SORT_BY="relevance_score"
OUTPUT_EXCEL_SORT_ORDER="desc"

OUTPUT_JSON_ENABLED=true
OUTPUT_JSON_TEMPLATE="proposaland_data_{date}.json"
OUTPUT_JSON_PRETTY=false
OUTPUT_JSON_INCLUDE_RAW=false

OUTPUT_DIRECTORY="/app/output"
OUTPUT_BACKUP_ENABLED=true
OUTPUT_BACKUP_RETENTION=30
OUTPUT_ARCHIVE_OLD_FILES=true
```

### Security & CORS
```bash
API_RATE_LIMIT=1000
CORS_ORIGINS="https://yourdomain.com"
CSRF_PROTECTION=true
SSL_REQUIRED=true
```

### Performance Settings
```bash
PERFORMANCE_CACHE_ENABLED=true
PERFORMANCE_CACHE_DURATION=3600
PERFORMANCE_PARALLEL_ENABLED=true
PERFORMANCE_MAX_WORKERS=3
PERFORMANCE_MEMORY_LIMIT="1GB"
PERFORMANCE_CONNECTION_POOLING=true
PERFORMANCE_REQUEST_TIMEOUT=30
```

### Data Quality
```bash
DATA_QUALITY_DUPLICATE_DETECTION=true
DATA_QUALITY_DUPLICATE_THRESHOLD=0.85
DATA_QUALITY_VALIDATION=true
DATA_QUALITY_TITLE_LENGTH=200
DATA_QUALITY_DESC_LENGTH=2000
DATA_QUALITY_ORG_LENGTH=100
DATA_QUALITY_LOCATION_LENGTH=100
DATA_QUALITY_REF_VALIDATION=true
DATA_QUALITY_DEADLINE_VALIDATION=true
```

---

## 🐳 Docker Environment File Example

Create a `.env` file for Docker deployment:

```bash
# Copy this template and fill in your values
# DO NOT commit this file to version control

# Required
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=
SENDER_PASSWORD=
RECIPIENT_EMAIL=
SECRET_KEY=
ENCRYPTION_KEY=
JWT_SECRET=
DATABASE_URL=
GOOGLE_CREDENTIALS_JSON=
GOOGLE_SHEETS_ID=
GOOGLE_DRIVE_FOLDER_ID=

# Optional (uncomment to override defaults)
# APP_NAME="Proposaland Monitor"
# LOG_LEVEL=INFO
# MAX_CONCURRENT_SCRAPERS=3
# DAILY_RUN_TIME="06:00"
```

---

## 🔒 Security Notes

1. **Never commit secrets** to version control
2. **Use strong encryption keys** (32+ characters, random)
3. **Rotate credentials** regularly
4. **Use environment-specific values** for each deployment stage
5. **Consider using a secrets management service** (AWS Secrets Manager, HashiCorp Vault, etc.)

---

## 🚀 Deployment Commands

### Local Testing
```bash
# Export environment variables
export SMTP_SERVER="smtp.gmail.com"
export SENDER_EMAIL="your-email@domain.com"
# ... set other required variables

# Run the application
python scheduler.py
```

### Docker Deployment
```bash
# Using environment file
docker run --env-file .env your-app:latest

# Or passing individual variables
docker run \
  -e SMTP_SERVER="smtp.gmail.com" \
  -e SENDER_EMAIL="your-email@domain.com" \
  your-app:latest
```

### Kubernetes Deployment
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: proposaland-secrets
type: Opaque
stringData:
  SMTP_SERVER: "smtp.gmail.com"
  SENDER_EMAIL: "your-email@domain.com"
  SENDER_PASSWORD: "your-app-password"
  SECRET_KEY: "your-secret-key"
  # ... other secrets
```
