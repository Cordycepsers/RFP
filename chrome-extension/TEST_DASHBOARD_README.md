# 🧪 Media Procurement Test Dashboard

An interactive web interface for testing the Chrome extension's data collection functionality.

## 🚀 Quick Start

### 1. Open the Dashboard
```bash
# Navigate to the chrome-extension directory
cd chrome-extension

# Open the test dashboard in your browser
open test-dashboard.html
# OR double-click the file in your file manager
```

### 2. Load Test Helper
The dashboard automatically loads `test-helper.js` for testing functionality.

### 3. Configure Settings
- **Server URL**: Your backend server (e.g., `http://localhost:8080`)
- **API Key**: Your authentication key
- **Collection Interval**: Time between collections (seconds)

## 🎯 Features

### 📊 Real-time Status Monitoring
- **Extension Status**: Chrome extension connectivity
- **Backend Status**: Server connection health
- **Website Status**: Current website detection
- **Last Update**: Timestamp of latest activity

### 🧪 Interactive Test Suite
- **Quick Test**: Fast validation of core functionality
- **Full Test Suite**: Comprehensive testing across all components
- **Individual Tests**: Targeted testing of specific features

### 🌍 Website Management
- **23 Organizations**: Complete list of target websites
- **Priority Filtering**: High/Medium/Low priority selection
- **Bulk Operations**: Select all, none, or by priority
- **Collection Control**: Start data collection for selected sites

### 📈 Performance Monitoring
- **Test Statistics**: Pass/fail rates and execution counts
- **Data Collection**: Items collected across all tests
- **Progress Tracking**: Real-time progress bars
- **Resource Usage**: Performance metrics

## 🎮 Available Tests

### 🔌 Basic Functionality
Tests extension loading, configuration, and core connectivity.

### 🌐 Website Detection
Verifies current website recognition and selector validation.

### 📊 Data Collection
Tests data extraction from the current page.

### 🎯 CSS Selectors
Validates CSS selectors against current website structure.

### 🖱️ Human Behavior
Tests anti-detection human behavior simulation.

### 🔗 Backend Connection
Verifies backend API connectivity and authentication.

### 🔍 Media Filtering
Tests media keyword filtering functionality.

### ⚡ Performance
Monitors extension performance and resource usage.

## ⌨️ Keyboard Shortcuts

- **Ctrl+Shift+T**: Run Quick Test
- **Ctrl+Shift+F**: Run Full Test Suite
- **Ctrl+Shift+C**: Clear Results

## 📋 Test Results

### Real-time Logging
- **Info**: General information and status updates
- **Success**: Successful test completions
- **Warning**: Non-critical issues or alerts
- **Error**: Test failures and critical issues

### Export Options
- **Export Results**: Download test logs as text file
- **Auto-scroll**: Automatic scrolling to latest results
- **Clear Results**: Reset the results panel

## 🔧 Configuration

### Server Configuration
```javascript
// Default settings
{
  "serverUrl": "http://localhost:8080",
  "apiKey": "your-api-key-here",
  "collectionInterval": 30
}
```

### Website Selection
- **Select All**: Choose all 23 organizations
- **Select None**: Deselect all websites
- **High Priority Only**: Select only high-priority targets
- **Custom Selection**: Manual checkbox selection

## 📊 Statistics Dashboard

### Test Metrics
- **Tests Run**: Total number of tests executed
- **Tests Passed**: Successfully completed tests
- **Tests Failed**: Failed or error tests
- **Data Collected**: Total items collected across all tests

### Progress Tracking
- Real-time progress bars during collection
- Percentage completion for multi-site operations
- Time estimates for remaining operations

## 🌍 Target Organizations

The dashboard includes all 23 target organizations:

**High Priority (8):**
- Devex Pro Funding
- UNDP Procurement Notices
- UNGM UN Global Marketplace
- DevelopmentAid.org - Media Tenders
- ReliefWeb - Jobs & Tenders
- African Development Bank - Procurement
- World Bank - Projects & Operations
- Asian Development Bank - Procurement

**Medium Priority (14):**
- The Global Fund, IUCN, Norwegian Refugee Council
- BirdLife International, Danish Refugee Council
- Heifer International, Save the Children
- Mercy Corps, International Rescue Committee
- Industrial Development Corporation
- Drugs for Neglected Diseases Initiative
- GGGI Global Green Growth Institute
- ACTED, Plan International

**Low Priority (1):**
- Inter-Parliamentary Union - Vacancies

## 🔍 Troubleshooting

### Common Issues

**Dashboard not loading:**
```bash
# Ensure test-helper.js is in the same directory
ls -la test-helper.js test-dashboard.html
```

**Extension not detected:**
```bash
# Check Chrome extension is loaded
# Go to chrome://extensions/
# Verify extension is enabled
```

**Backend connection failed:**
```bash
# Verify backend is running
curl http://localhost:8080/health
# Should return: {"status": "healthy"}
```

**No data collected:**
```bash
# Check website selectors in browser console
# Look for CSS selector errors
# Verify target website structure
```

### Debug Mode

Enable verbose logging in the dashboard:
1. Open browser Developer Tools (F12)
2. Check Console tab for detailed logs
3. Look for MediaProcurementTester messages

### Browser Compatibility

**Supported Browsers:**
- ✅ Chrome (recommended)
- ✅ Edge (Chromium-based)
- ✅ Firefox (limited functionality)
- ❌ Safari (not supported)

## 📱 Mobile Support

The dashboard is responsive and works on mobile devices:
- Touch-friendly interface
- Responsive grid layout
- Mobile-optimized controls
- Swipe gestures for navigation

## 🔒 Security Notes

- **Local Testing**: Dashboard runs locally in browser
- **No Data Storage**: No sensitive data stored in dashboard
- **API Keys**: Stored only in browser localStorage
- **HTTPS**: Use HTTPS for production backend connections

## 🚀 Advanced Usage

### Custom Test Scripts
```javascript
// Add custom tests to the dashboard
function customTest() {
    logMessage('info', '🔧 Running custom test...');
    // Your test logic here
}
```

### Integration with CI/CD
```bash
# Headless testing (requires additional setup)
npm install puppeteer
node test-automation.js
```

### Performance Monitoring
```javascript
// Monitor extension performance
const startTime = performance.now();
// ... test operations ...
const duration = performance.now() - startTime;
console.log(`Test completed in ${duration}ms`);
```

## 📞 Support

For issues or questions:
1. Check the main TESTING_GUIDE.md
2. Review browser console for errors
3. Verify extension and backend status
4. Test with individual components first

---

**Happy Testing!** 🎉

