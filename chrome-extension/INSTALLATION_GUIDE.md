# 🚀 Chrome Extension Installation Guide

## Quick Installation Steps

### 1. Download the Extension
```bash
# Clone or download the repository
git clone https://github.com/Cordycepsers/RFP.git
cd RFP/chrome-extension
```

### 2. Load Extension in Chrome

1. **Open Chrome Extensions Page**
   - Navigate to `chrome://extensions/`
   - OR click Chrome menu → More tools → Extensions

2. **Enable Developer Mode**
   - Toggle "Developer mode" switch in top-right corner

3. **Load Unpacked Extension**
   - Click "Load unpacked" button
   - Select the `chrome-extension` folder from your repository
   - Click "Select Folder"

4. **Verify Installation**
   - Extension should appear in the list with green "ON" toggle
   - Icon should appear in Chrome toolbar
   - No error messages should be displayed

### 3. Configure Extension

1. **Click Extension Icon** in Chrome toolbar
2. **Enter Configuration:**
   ```
   Server URL: http://localhost:8080
   API Key: your-api-key-here
   Collection Interval: 30
   ```
3. **Click "Save Configuration"**
4. **Verify Connection** - should show green "Connected" status

## 🔧 Troubleshooting

### Extension Won't Load

**Error: "Could not load manifest"**
```bash
# Check manifest.json syntax
cd chrome-extension
cat manifest.json | python3 -c "import sys, json; json.load(sys.stdin)"
```

**Error: "Could not load icon"**
```bash
# Verify icon files exist
ls -la icons/
# Should show: icon16.png, icon32.png, icon48.png, icon128.png
```

**Error: "Service worker registration failed"**
```bash
# Check background.js syntax
node -c background.js
```

### Extension Loads but Doesn't Work

**Check Console Errors:**
1. Right-click extension icon → "Inspect popup"
2. Check Console tab for JavaScript errors
3. Look for network request failures

**Verify Permissions:**
1. Go to `chrome://extensions/`
2. Click "Details" on your extension
3. Check "Site access" permissions
4. Should be "On all sites" or specific domains

**Test Backend Connection:**
```bash
# Verify backend is running
curl http://localhost:8080/health
# Should return: {"status": "healthy"}
```

## 📋 File Structure Verification

Your `chrome-extension` folder should contain:

```
chrome-extension/
├── manifest.json           ✅ Extension configuration
├── background.js           ✅ Service worker
├── content-script.js       ✅ Page interaction script
├── popup/
│   ├── popup.html         ✅ Extension popup interface
│   ├── popup.css          ✅ Popup styling
│   └── popup.js           ✅ Popup functionality
├── utils/
│   ├── human-behavior.js  ✅ Anti-detection utilities
│   └── scraper-utils.js   ✅ Data extraction utilities
├── config/
│   └── websites.json      ✅ 23 organization configuration
├── icons/
│   ├── icon16.png         ✅ 16x16 icon
│   ├── icon32.png         ✅ 32x32 icon
│   ├── icon48.png         ✅ 48x48 icon
│   └── icon128.png        ✅ 128x128 icon
├── test-helper.js         ✅ Testing utilities
├── test-dashboard.html    ✅ Interactive test interface
└── INSTALLATION_GUIDE.md  ✅ This guide
```

## 🧪 Testing Installation

### Quick Test
1. **Open Test Dashboard**
   ```bash
   # Open in browser
   open chrome-extension/test-dashboard.html
   ```

2. **Run Basic Test**
   - Click "Quick Test" button
   - Should show green success messages
   - Verify extension connectivity

### Manual Test
1. **Navigate to Target Website**
   - Go to https://procurement-notices.undp.org/
   
2. **Open Extension Popup**
   - Click extension icon in toolbar
   - Should detect UNDP website
   
3. **Start Collection**
   - Click "Start Collection"
   - Monitor progress in popup

## 🔒 Permissions Explained

The extension requests these permissions:

- **activeTab**: Access current tab for data extraction
- **storage**: Save configuration and collected data
- **downloads**: Save collected files locally
- **cookies**: Access login sessions for authenticated sites
- **host_permissions**: Access all websites for data collection

## 🌐 Supported Websites

The extension is configured for 23 organizations:

**High Priority (8 sites):**
- Devex Pro, UNDP, UNGM, DevelopmentAid.org
- ReliefWeb, African Development Bank
- World Bank, Asian Development Bank

**Medium Priority (14 sites):**
- Global Fund, IUCN, Norwegian Refugee Council
- BirdLife, Danish Refugee Council, Heifer International
- Save the Children, Mercy Corps, IRC
- Industrial Development Corp, DNDi, GGGI
- ACTED, Plan International

**Low Priority (1 site):**
- Inter-Parliamentary Union

## 🚀 Next Steps

After successful installation:

1. **Configure Backend Server**
   - Set up Google Cloud service account
   - Deploy backend or run locally
   - Configure API keys

2. **Test Data Collection**
   - Use test dashboard for validation
   - Start with high-priority websites
   - Monitor collection results

3. **Production Deployment**
   - Deploy backend to Google Cloud
   - Configure Google Drive integration
   - Set up automated scheduling

## 📞 Support

If you encounter issues:

1. **Check Browser Console**
   - F12 → Console tab
   - Look for error messages

2. **Verify File Integrity**
   - Ensure all files are present
   - Check file permissions

3. **Test Components Individually**
   - Backend connectivity
   - Website detection
   - Data extraction

4. **Review Documentation**
   - TESTING_GUIDE.md for comprehensive testing
   - TEST_DASHBOARD_README.md for dashboard usage

---

**Installation Complete!** 🎉

Your Media Procurement Platform Chrome extension is now ready for data collection across 23 international development organizations.

