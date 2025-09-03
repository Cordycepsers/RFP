# Google Cloud Run Deployment Checklist
**MacBook Pro → Google Cloud Run**

## ✅ Pre-Deployment Validation (COMPLETED)
- [x] MacBook Pro environment tested and ready
- [x] Google authentication working
- [x] Service account file configured
- [x] Environment variables set
- [x] All dependencies installed
- [x] Server startup tested
- [x] Excel export capabilities verified

## 🚀 Deployment Steps

### 1. Verify Google Cloud CLI
```bash
# Check if gcloud is installed and authenticated
gcloud auth list
gcloud config get-value project
```

### 2. Build and Deploy
```bash
# Deploy to Google Cloud Run
npm run deploy
```

**Alternative manual deployment:**
```bash
gcloud run deploy media-procurement-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8081 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

### 3. Configure Environment Variables in Cloud Run
Set these environment variables in Google Cloud Console → Cloud Run:

```
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
GOOGLE_DRIVE_FOLDER_ID=0AHbM0SsjOuLRUk9PVA
API_KEYS=your-secure-api-keys
PORT=8080
NODE_ENV=production
```

### 4. Upload Service Account
- Upload `service-account.json` as a Cloud Run secret
- Mount it to `/app/service-account.json` in container

### 5. Test Deployment
```bash
# Get the deployed URL
gcloud run services describe media-procurement-backend --region=us-central1 --format='value(status.url)'

# Test health endpoint
curl "https://your-service-url/health"
```

## 🔍 Post-Deployment Testing

### API Endpoints to Test:
1. **Health Check**: `GET /health`
2. **Status Check**: `GET /api/status` (requires API key)
3. **Data Upload**: `POST /api/upload-data` (requires API key)

### Expected Responses:
```json
// GET /health
{
  "status": "healthy",
  "timestamp": "2025-09-03T15:17:00.000Z",
  "version": "1.0.0",
  "uptime": 123.45
}

// GET /api/status
{
  "status": "operational",
  "googleDrive": {
    "connected": true,
    "user": "google-drive@google-mpf-1050608566268.iam.gserviceaccount.com"
  }
}
```

## 📊 Monitoring & Logs

### View Logs:
```bash
gcloud run services logs read media-procurement-backend --region=us-central1
```

### Monitor Performance:
- Memory usage should be < 400MB
- Cold starts should be < 3 seconds
- Response times should be < 2 seconds

## 🔧 Troubleshooting

### Common Issues:
1. **Authentication Errors**: Check service account permissions
2. **Memory Issues**: Increase memory allocation in Cloud Run
3. **Timeout Issues**: Increase timeout settings
4. **Environment Variables**: Verify all variables are set

### Service Account Permissions Needed:
- `roles/drive.file` - Create and manage Drive files
- `roles/sheets.editor` - Create and edit spreadsheets (if needed)

## ✅ Success Criteria

Your deployment is successful when:
- [  ] Health endpoint returns 200 OK
- [  ] Status endpoint shows Google Drive connected
- [  ] Can create folders in Google Drive
- [  ] Can export existing spreadsheets
- [  ] Logs show no authentication errors
- [  ] Memory usage is stable
- [  ] Response times are acceptable

## 🚀 Next Steps After Deployment

1. **Configure Production API Keys**: Replace test keys with secure production keys
2. **Set Up Monitoring**: Configure alerts for errors and performance
3. **Scale Configuration**: Adjust min/max instances based on usage
4. **Backup Strategy**: Implement automated backups
5. **Documentation**: Update API documentation with live URLs

---

**Deployment Status**: Ready ✅  
**Last Tested**: 2025-09-03 15:17  
**Environment**: MacBook Pro → Google Cloud Run  
**Configuration**: Fully Validated  
