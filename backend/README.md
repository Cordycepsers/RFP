# Media Procurement Backend

A simplified backend server for the Media Procurement Data Collection Platform, built with Node.js and Express, integrating with Google Drive and Google Sheets APIs for data storage and processing.

## 🚀 Features

- **Google Drive Integration**: Automated file storage and organization
- **Google Sheets API**: Data processing and spreadsheet generation
- **RESTful API**: Clean endpoints for data upload and file management  
- **Security**: API key authentication and input validation
- **Health Monitoring**: Built-in health checks and logging
- **Cloud Ready**: Optimized for Google Cloud Run deployment

## 📋 Prerequisites

- Node.js >= 18.0.0 (tested with v22.18.0)
- npm >= 8.0.0
- Google Cloud Platform project with:
  - Drive API enabled
  - Sheets API enabled
  - Service account with appropriate permissions

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd media-procurement-backend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up Google Cloud credentials**
   
   Download your service account JSON key file from the Google Cloud Console:
   - Go to IAM & Admin → Service Accounts
   - Select your service account
   - Click "Keys" → "Add Key" → "Create New Key"
   - Choose JSON format and download
   
   Place the downloaded file as `service-account.json` in the project root directory.

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Verify Google authentication**
   ```bash
   npm run verify-auth
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Server Configuration
PORT=8081
NODE_ENV=production

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Google Drive Configuration  
GOOGLE_DRIVE_FOLDER_ID=your-base-folder-id

# API Security
API_KEYS=key1,key2,key3

# Optional: Logging Configuration
LOG_LEVEL=info
```

### Service Account Permissions

Ensure your Google Cloud service account has the following permissions:
- **Google Drive API**: `https://www.googleapis.com/auth/drive`
- **Google Sheets API**: `https://www.googleapis.com/auth/spreadsheets`

## 🚦 Usage

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

### Testing Authentication
```bash
npm run verify-auth
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```
Returns server health status and uptime information.

### Upload Data
```http  
POST /api/upload-data
Authorization: Bearer <api-key>
Content-Type: application/json

{
  "website": "example.com",
  "data": { /* your data */ },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Upload Files
```http
POST /api/upload-files
Authorization: Bearer <api-key>
Content-Type: multipart/form-data

folderId: <google-drive-folder-id>
files: <file-uploads>
```

### Status Check
```http
GET /api/status
Authorization: Bearer <api-key>
```

## 🔧 Node.js v22 & OpenSSL 3 Compatibility

This application is fully compatible with Node.js v22 and OpenSSL 3. We've resolved the common `error:1E08010C:DECODER routines::unsupported` authentication issue by:

### ✅ What We Fixed

1. **Upgraded Dependencies**: Updated to latest versions of `google-auth-library` and `googleapis`
2. **Service Account File**: Switched from environment variable credentials to JSON file authentication
3. **Removed Legacy Flags**: No longer requires `--openssl-legacy-provider` flag

### 🚨 Previous Issues

If you encounter `error:1E08010C:DECODER routines::unsupported`, it typically indicates:
- Incompatible private key format with OpenSSL 3
- Issues parsing multi-line private keys from environment variables
- Outdated Google authentication libraries

### 🔍 Troubleshooting

1. **Verify Node.js and OpenSSL versions**:
   ```bash
   node --version  # Should be >= 18.0.0
   node -p "process.versions.openssl"  # OpenSSL version info
   ```

2. **Test authentication**:
   ```bash
   npm run verify-auth
   ```

3. **Check service account file**:
   - Ensure the file exists and is readable
   - Verify the JSON format is valid
   - Confirm the service account has proper permissions

## 🐳 Docker Deployment

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 8080
CMD ["npm", "start"]
```

## ☁️ Google Cloud Run Deployment

```bash
npm run deploy
```

Or manually:
```bash
gcloud run deploy media-procurement-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## 📊 Monitoring & Logging

The application includes:
- Health check endpoint at `/health`
- Request logging with winston
- Error tracking and reporting
- Performance monitoring

## 🔒 Security

- API key authentication for all endpoints
- Request validation with Joi
- Helmet.js security headers
- CORS configuration
- Input sanitization

## 🧪 Testing

Run the test suite:
```bash
npm test
```

Verify Google authentication:
```bash
npm run verify-auth
```

## 📈 Performance

- Compression middleware for response optimization
- Connection pooling for Google APIs
- Efficient file upload handling with multer
- Memory management for large files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues related to:
- **Google API Authentication**: Check the troubleshooting section above
- **Node.js v22 Compatibility**: Ensure you're using the service account JSON file method
- **OpenSSL 3 Issues**: Verify your dependencies are up to date

## 📝 Changelog

### v1.1.0 - Node.js v22 & OpenSSL 3 Compatibility
- ✅ Fixed Google authentication with OpenSSL 3
- ✅ Updated to latest Google API client libraries
- ✅ Switched to service account JSON file authentication  
- ✅ Removed dependency on legacy OpenSSL provider
- ✅ Added comprehensive authentication verification script
- ✅ Updated documentation and deployment instructions

### v1.0.0 - Initial Release
- 🚀 Basic server setup with Express
- 🔗 Google Drive and Sheets integration
- 📁 File upload and data processing
- 🔐 API key authentication
- ☁️ Google Cloud Run deployment support
