# Setup Guide: Media Procurement Platform

This guide walks you through setting up the complete Media Procurement Platform from scratch.

## 📋 Prerequisites

### Required Accounts & Services

1. **Google Cloud Platform Account**
   - Billing account enabled
   - Project with unique ID

2. **Google Workspace or Gmail Account**
   - For Google Drive access
   - For receiving shared reports

### Required Software

1. **Google Cloud SDK**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Node.js** (v18 or higher)
   ```bash
   # Check version
   node --version
   npm --version
   ```

3. **Chrome Browser**
   - For extension installation
   - Developer mode enabled

## 🔧 Google Cloud Setup

### 1. Create Google Cloud Project

```bash
# Set project variables
export PROJECT_ID="media-procurement-$(date +%s)"
export REGION="us-central1"

# Create project
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable billing (replace BILLING_ACCOUNT_ID)
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### 2. Enable Required APIs

```bash
# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable drive.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create media-procurement-sa \
    --display-name="Media Procurement Service Account"

# Get service account email
export SA_EMAIL="media-procurement-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/drive.file"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/sheets.editor"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=$SA_EMAIL
```

### 4. Setup Google Drive

```bash
# Create base folder in Google Drive
# Note: This needs to be done manually in Google Drive UI
# 1. Go to drive.google.com
# 2. Create folder "Media Procurement Data"
# 3. Share with service account email (Editor access)
# 4. Copy folder ID from URL
```

## 🚀 Backend Deployment

### 1. Prepare Environment

```bash
# Navigate to backend directory
cd backend

# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file with your values:

```bash
# Server Configuration
PORT=8080
NODE_ENV=production

# Google Cloud Configuration
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_SERVICE_ACCOUNT_EMAIL=media-procurement-sa@your-project.iam.gserviceaccount.com
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
Your private key from service-account-key.json
-----END PRIVATE KEY-----"

# Google Drive Configuration (folder ID from step 4 above)
GOOGLE_DRIVE_FOLDER_ID=1ABC123DEF456GHI789JKL

# API Security (generate random keys)
API_KEYS=mp_key_$(openssl rand -hex 16),mp_key_$(openssl rand -hex 16)
```

### 3. Deploy to Cloud Run

```bash
# Make deploy script executable
chmod +x ../deployment/deploy.sh

# Run deployment
cd ../deployment
./deploy.sh
```

### 4. Configure Cloud Run Environment

```bash
# Set environment variables in Cloud Run
gcloud run services update media-procurement-backend \
    --region=$REGION \
    --set-env-vars="GOOGLE_PROJECT_ID=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_SERVICE_ACCOUNT_EMAIL=${SA_EMAIL}" \
    --set-env-vars="GOOGLE_DRIVE_FOLDER_ID=YOUR_FOLDER_ID" \
    --set-env-vars="API_KEYS=YOUR_API_KEYS"

# Set private key (use Secret Manager for production)
gcloud run services update media-procurement-backend \
    --region=$REGION \
    --set-env-vars="GOOGLE_PRIVATE_KEY=$(cat service-account-key.json | jq -r .private_key)"
```

## 🔌 Chrome Extension Setup

### 1. Load Extension

1. Open Chrome browser
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode" (top right toggle)
4. Click "Load unpacked"
5. Select the `chrome-extension` folder
6. Note the extension ID for configuration

### 2. Configure Extension

1. Click the extension icon in Chrome toolbar
2. Go to Configuration section
3. Enter your values:
   - **Server URL**: Your Cloud Run service URL
   - **API Key**: One of your generated API keys
   - **Your Email**: Email for receiving shared reports

### 3. Test Configuration

1. Click "Save Configuration"
2. Go to Collection Control section
3. Click "Start Collection" (test with one website first)
4. Monitor progress in popup
5. Check Google Drive for results

## 🔒 Security Configuration

### 1. API Key Management

```bash
# Generate secure API keys
API_KEY_1="mp_$(openssl rand -hex 32)"
API_KEY_2="mp_$(openssl rand -hex 32)"

echo "API Keys generated:"
echo "Key 1: $API_KEY_1"
echo "Key 2: $API_KEY_2"
```

### 2. Service Account Security

```bash
# Limit service account permissions (principle of least privilege)
gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/editor"

# Only grant specific permissions needed
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/drive.file"
```

### 3. Network Security

```bash
# Configure Cloud Run to only accept HTTPS
gcloud run services update media-procurement-backend \
    --region=$REGION \
    --ingress=all \
    --cpu-throttling \
    --max-instances=10
```

## 📊 Monitoring Setup

### 1. Health Check Monitoring

```bash
# Create uptime check
gcloud alpha monitoring uptime create \
    --display-name="Media Procurement Health Check" \
    --http-check-path="/health" \
    --hostname="YOUR_CLOUD_RUN_URL"
```

### 2. Logging Configuration

```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=media-procurement-backend" \
    --limit=50 \
    --format="table(timestamp,textPayload)"
```

### 3. Error Alerting

```bash
# Create error alert policy
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring-policy.yaml
```

## 🧪 Testing

### 1. Backend Testing

```bash
# Test health endpoint
curl https://YOUR_CLOUD_RUN_URL/health

# Test API endpoint (replace with your API key)
curl -X POST https://YOUR_CLOUD_RUN_URL/api/upload-data \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Client-Email: your@email.com" \
  -d '{
    "website": "Test Website",
    "data": {
      "opportunities": [],
      "totalOpportunities": 0,
      "mediaOpportunities": 0
    },
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

### 2. Extension Testing

1. Open a target website (e.g., UNDP Procurement)
2. Click extension icon
3. Start collection for single website
4. Verify data appears in Google Drive
5. Check spreadsheet formatting and data

### 3. End-to-End Testing

1. Configure extension with all settings
2. Start full collection (all websites)
3. Monitor progress and logs
4. Verify all data is collected and organized
5. Test sharing functionality

## 🔧 Troubleshooting

### Common Issues

1. **"Authentication failed" errors**
   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:${SA_EMAIL}"
   ```

2. **"Folder not found" errors**
   - Verify folder ID in environment variables
   - Check service account has access to folder
   - Ensure folder exists and is shared

3. **Extension not loading**
   - Check Chrome developer console for errors
   - Verify manifest.json syntax
   - Ensure all required permissions are granted

4. **Collection timeouts**
   - Increase Cloud Run timeout settings
   - Check website selector configurations
   - Verify network connectivity

### Debug Mode

Enable detailed logging:

```bash
# Update Cloud Run with debug logging
gcloud run services update media-procurement-backend \
    --region=$REGION \
    --set-env-vars="LOG_LEVEL=debug"
```

## 📈 Production Optimization

### 1. Performance Tuning

```bash
# Optimize Cloud Run configuration
gcloud run services update media-procurement-backend \
    --region=$REGION \
    --memory=2Gi \
    --cpu=2 \
    --concurrency=100 \
    --max-instances=20
```

### 2. Cost Optimization

```bash
# Set minimum instances to 0 for cost savings
gcloud run services update media-procurement-backend \
    --region=$REGION \
    --min-instances=0
```

### 3. Backup Strategy

```bash
# Create automated backup of Google Drive folder
# (Implement using Google Apps Script or Cloud Functions)
```

## ✅ Verification Checklist

- [ ] Google Cloud project created and configured
- [ ] Service account created with proper permissions
- [ ] APIs enabled (Cloud Run, Drive, Sheets)
- [ ] Backend deployed to Cloud Run
- [ ] Environment variables configured
- [ ] Chrome extension loaded and configured
- [ ] Test collection completed successfully
- [ ] Data appears in Google Drive
- [ ] Sharing functionality works
- [ ] Monitoring and alerting configured

## 🎯 Next Steps

After successful setup:

1. **Customize website configurations** for your specific needs
2. **Add more target organizations** to the collection list
3. **Set up automated scheduling** for regular collections
4. **Configure email notifications** for completed collections
5. **Implement analytics dashboard** for tracking performance

---

**Setup complete!** 🎉 Your Media Procurement Platform is ready for production use.

