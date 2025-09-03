# Media Procurement Data Collection Platform

A simplified, production-ready platform for automatically collecting media-related procurement opportunities from international development organizations.

## 🎯 Overview

This platform consists of:
- **Chrome Extension**: Client-side data collection using existing browser sessions
- **Google Cloud Backend**: Simplified server with Google Drive/Sheets integration
- **Automated Processing**: Smart filtering for media-relevant opportunities

## 🏗️ Architecture

```
Chrome Extension → Google Cloud Run → Google Drive/Sheets
     ↓                    ↓                    ↓
- Data Collection    - API Processing     - Data Storage
- Human Behavior     - Authentication     - Report Generation
- Session Leverage   - File Management    - Client Sharing
```

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Service Account** with Drive and Sheets API access
3. **Chrome Browser** for extension installation

### 1. Backend Deployment

```bash
# Clone and navigate to project
cd media-procurement-platform

# Set your Google Cloud project
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Deploy to Google Cloud Run
cd deployment
chmod +x deploy.sh
./deploy.sh
```

### 2. Environment Configuration

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit with your values
nano backend/.env
```

Required environment variables:
- `GOOGLE_PROJECT_ID`: Your Google Cloud project ID
- `GOOGLE_SERVICE_ACCOUNT_EMAIL`: Service account email
- `GOOGLE_PRIVATE_KEY`: Service account private key
- `GOOGLE_DRIVE_FOLDER_ID`: Base folder for data storage
- `API_KEYS`: Comma-separated API keys for authentication

### 3. Chrome Extension Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `chrome-extension` folder
4. Configure the extension with your server URL and API key

## 📊 Target Organizations

The platform monitors 10 major organizations:

- **UN Agencies**: UNDP, UNGM, ReliefWeb
- **Development Banks**: World Bank, African Development Bank
- **Major NGOs**: Save the Children, Mercy Corps, IRC
- **Specialized Platforms**: DevelopmentAid.org (pre-filtered)

## 🔧 Configuration

### Website Configuration

Edit `chrome-extension/config/websites.json` to:
- Add new organizations
- Modify CSS selectors
- Adjust priority levels
- Update media keywords

### Media Keywords

The system filters for opportunities containing:
- video, photo, film, multimedia, podcast
- animation, audiovisual, media, communication
- production, graphic, design, branding
- creative, advertising, marketing, documentary

## 🛠️ Development

### Local Development

```bash
# Backend
cd backend
npm install
npm run dev

# Test endpoints
curl http://localhost:8080/health
```

### Chrome Extension Development

1. Make changes to extension files
2. Go to `chrome://extensions/`
3. Click "Reload" on the extension
4. Test functionality

## 📈 Usage

### Starting Collection

1. Click the extension icon
2. Configure server URL and credentials
3. Click "Start Collection"
4. Monitor progress in the popup

### Viewing Results

- Results are automatically uploaded to Google Drive
- Organized in dated folders with spreadsheets
- Shared with specified email addresses
- Downloadable reports available

## 🔒 Security

### API Authentication

- Bearer token authentication
- Configurable API keys
- IP-based restrictions (optional)

### Data Privacy

- No local data storage
- Direct Google Drive integration
- Encrypted credentials storage
- Automatic cleanup

## 📋 API Endpoints

### POST /api/upload-data
Upload collected opportunity data

```json
{
  "website": "UNDP Procurement Notices",
  "data": {
    "opportunities": [...],
    "totalOpportunities": 25,
    "mediaOpportunities": 8
  },
  "timestamp": "2025-09-03T10:00:00Z"
}
```

### POST /api/upload-files
Upload document files

### GET /api/status
Check system status

### GET /health
Health check endpoint

## 🚀 Deployment

### Google Cloud Run

The platform is designed for Google Cloud Run deployment:

- **Automatic scaling**: 0 to 10 instances
- **Memory**: 1GB per instance
- **CPU**: 1 vCPU per instance
- **Timeout**: 60 seconds per request

### Environment Variables

Set in Cloud Run console:
- `GOOGLE_PROJECT_ID`
- `GOOGLE_SERVICE_ACCOUNT_EMAIL`
- `GOOGLE_PRIVATE_KEY`
- `GOOGLE_DRIVE_FOLDER_ID`
- `API_KEYS`

## 📊 Monitoring

### Health Checks

- `/health` endpoint for status monitoring
- Google Cloud Run health checks
- Automatic restart on failures

### Logging

- Structured JSON logging
- Google Cloud Logging integration
- Error tracking and alerting

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify service account permissions
   - Check API key configuration
   - Ensure Drive/Sheets APIs are enabled

2. **Collection Failures**
   - Check website selector configurations
   - Verify network connectivity
   - Review Chrome extension permissions

3. **Upload Errors**
   - Confirm Google Drive folder permissions
   - Check file size limits (50MB max)
   - Verify service account access

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=debug
```

## 📈 Scaling

### Performance Optimization

- Implement request caching
- Add database for metadata
- Use Cloud Storage for large files
- Implement batch processing

### Geographic Expansion

- Add European development agencies
- Include regional development banks
- Support multiple languages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting guide
- Review the API documentation

## 🎯 Roadmap

- [ ] Add more organizations (50+ targets)
- [ ] Implement AI-powered relevance scoring
- [ ] Add email notifications
- [ ] Create analytics dashboard
- [ ] Support for multiple languages
- [ ] Mobile app companion

---

**Built for the international development community** 🌍

