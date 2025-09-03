# Chrome Extension Testing Guide

## 🎯 Overview

This guide provides step-by-step instructions to test the Media Procurement Platform Chrome extension's data collection functionality across all 23 target organizations.

## 📋 Prerequisites

### Required Setup
- **Chrome Browser** (latest version)
- **Backend Server** running (local or deployed)
- **Google Service Account** configured
- **API Key** for extension authentication

### Test Environment Options

**Option A: Local Backend**
```bash
cd backend
npm install
npm start
# Server runs on http://localhost:8080
```

**Option B: Deployed Backend**
```bash
# Use your deployed Google Cloud Run URL
# Example: https://media-procurement-backend-xxx.run.app
```

## 🔧 Extension Installation

### Step 1: Load Extension in Chrome

1. **Open Chrome** and navigate to `chrome://extensions/`
2. **Enable Developer Mode** (toggle in top-right corner)
3. **Click "Load unpacked"**
4. **Select** the `chrome-extension` folder from your repository
5. **Verify** the extension appears with a green "ON" toggle

### Step 2: Configure Extension

1. **Click the extension icon** in Chrome toolbar
2. **Enter Configuration:**
   ```
   Server URL: http://localhost:8080 (or your deployed URL)
   API Key: your-api-key-here
   Collection Interval: 30 (seconds)
   ```
3. **Click "Save Configuration"**
4. **Verify** green "Connected" status appears

## 🧪 Testing Procedures

### Test 1: Basic Functionality Test

**Objective:** Verify extension loads and communicates with backend

**Steps:**
1. Open extension popup
2. Check connection status (should show green "Connected")
3. Verify website count shows "23 organizations configured"
4. Check that "Start Collection" button is enabled

**Expected Results:**
- ✅ Extension popup loads without errors
- ✅ Backend connection established
- ✅ Configuration displays correctly
- ✅ No console errors in DevTools

### Test 2: Single Website Collection Test

**Objective:** Test data collection from one organization

**Target:** UNDP Procurement Notices (no login required)

**Steps:**
1. **Navigate to:** https://procurement-notices.undp.org/
2. **Open extension popup**
3. **Click "Start Collection"**
4. **Select "UNDP Procurement Notices" only**
5. **Click "Begin Scraping"**
6. **Monitor progress** in popup

**Expected Results:**
- ✅ Extension detects UNDP website
- ✅ Progress bar shows collection activity
- ✅ Data items found and processed
- ✅ Success message with count of opportunities found
- ✅ Data sent to backend successfully

**Verification:**
```javascript
// Check browser console for logs
// Should see messages like:
"[Content Script] Starting data collection for UNDP..."
"[Content Script] Found 15 opportunities"
"[Background] Data sent to backend successfully"
```

### Test 3: Multiple Website Collection Test

**Objective:** Test collection from multiple organizations

**Targets:** 
- UNDP Procurement Notices
- UNGM UN Global Marketplace  
- ReliefWeb Jobs & Tenders

**Steps:**
1. **Open extension popup**
2. **Click "Start Collection"**
3. **Select multiple websites:**
   - ✅ UNDP Procurement Notices
   - ✅ UNGM UN Global Marketplace
   - ✅ ReliefWeb Jobs & Tenders
4. **Click "Begin Scraping"**
5. **Monitor progress** for each site

**Expected Results:**
- ✅ Extension processes each site sequentially
- ✅ Progress updates for each organization
- ✅ Different data counts from each source
- ✅ All data successfully sent to backend
- ✅ Final summary shows total opportunities collected

### Test 4: Media Keyword Filtering Test

**Objective:** Verify media-specific filtering works

**Target:** DevelopmentAid.org (pre-filtered for media)

**Steps:**
1. **Navigate to:** https://www.developmentaid.org/tenders/search?searchedText=video%20or%20photo%20or%20film%20or%20documentary%20or%20podcasts%20or%20animation%20or%20audiovisual&searchedFields=title
2. **Start collection** for DevelopmentAid.org only
3. **Review collected data** in backend logs

**Expected Results:**
- ✅ Only media-related opportunities collected
- ✅ Keywords detected: video, photo, film, multimedia, etc.
- ✅ Non-media opportunities filtered out
- ✅ Higher relevance score for media-specific content

### Test 5: Human Behavior Simulation Test

**Objective:** Verify anti-detection measures work

**Steps:**
1. **Open browser DevTools** → Network tab
2. **Start collection** on any website
3. **Monitor network requests** and timing
4. **Check console** for human behavior logs

**Expected Results:**
- ✅ Random delays between actions (1-3 seconds)
- ✅ Mouse movement simulation
- ✅ Scroll behavior mimics human patterns
- ✅ No rapid-fire requests that look automated
- ✅ Console shows: "Simulating human behavior: random delay 2.3s"

### Test 6: Error Handling Test

**Objective:** Test extension behavior with errors

**Test Cases:**

**A. Network Error Test:**
1. Disconnect internet
2. Try to start collection
3. Verify error handling

**B. Invalid Website Test:**
1. Navigate to non-target website
2. Try to collect data
3. Check error messages

**C. Backend Offline Test:**
1. Stop backend server
2. Try to collect data
3. Verify retry mechanism

**Expected Results:**
- ✅ Graceful error messages displayed
- ✅ No extension crashes
- ✅ Retry mechanisms activate
- ✅ User informed of issues clearly

### Test 7: Data Quality Verification

**Objective:** Verify collected data accuracy and completeness

**Steps:**
1. **Collect data** from UNDP Procurement
2. **Manually check** first 3 opportunities on website
3. **Compare** with collected data
4. **Verify fields:**
   - Title accuracy
   - Organization name
   - Deadline dates
   - Reference numbers
   - Document links

**Expected Results:**
- ✅ 95%+ accuracy in data extraction
- ✅ All required fields populated
- ✅ Dates in correct format
- ✅ Links are valid and accessible
- ✅ No duplicate entries

## 🔍 Advanced Testing

### Test 8: Performance Test

**Objective:** Test extension performance under load

**Steps:**
1. **Select all 23 organizations**
2. **Start full collection**
3. **Monitor system resources:**
   - CPU usage
   - Memory consumption
   - Network bandwidth
4. **Time the complete process**

**Expected Results:**
- ✅ CPU usage < 50% during collection
- ✅ Memory usage < 500MB
- ✅ Complete collection in < 10 minutes
- ✅ No browser freezing or crashes

### Test 9: Login-Required Website Test

**Objective:** Test Devex Pro (requires login)

**Prerequisites:** Valid Devex Pro account

**Steps:**
1. **Login to Devex Pro** manually in browser
2. **Navigate to funding opportunities**
3. **Start collection** for Devex Pro only
4. **Verify** extension uses existing session

**Expected Results:**
- ✅ Extension detects existing login session
- ✅ No additional login prompts
- ✅ Premium content accessible
- ✅ Data collection successful

### Test 10: Data Persistence Test

**Objective:** Verify data reaches Google Drive/Sheets

**Steps:**
1. **Complete data collection**
2. **Check Google Drive** for new files
3. **Verify Google Sheets** updates
4. **Confirm data organization** by date/source

**Expected Results:**
- ✅ New folder created with current date
- ✅ Separate files for each organization
- ✅ Google Sheets updated with summary
- ✅ Data properly formatted and readable

## 🐛 Troubleshooting

### Common Issues & Solutions

**Issue: Extension not loading**
```bash
# Solution: Check manifest.json syntax
cd chrome-extension
cat manifest.json | python -m json.tool
```

**Issue: Backend connection failed**
```bash
# Solution: Verify backend is running
curl http://localhost:8080/health
# Should return: {"status": "healthy"}
```

**Issue: No data collected**
```bash
# Solution: Check website selectors
# Open DevTools → Console
# Look for selector errors
```

**Issue: Data not reaching Google Drive**
```bash
# Solution: Check service account permissions
# Verify API keys in backend/.env
```

### Debug Mode

**Enable Debug Logging:**
1. Open extension popup
2. Click "Settings" → "Debug Mode"
3. Enable "Verbose Logging"
4. Check browser console for detailed logs

**Debug Console Commands:**
```javascript
// Check extension status
chrome.runtime.sendMessage({action: "getStatus"})

// View collected data
chrome.runtime.sendMessage({action: "getLastCollection"})

// Test website detection
chrome.runtime.sendMessage({action: "detectWebsite"})
```

## ✅ Test Completion Checklist

### Basic Tests
- [ ] Extension installation successful
- [ ] Backend connection established
- [ ] Single website collection works
- [ ] Multiple website collection works
- [ ] Media keyword filtering active

### Advanced Tests
- [ ] Human behavior simulation working
- [ ] Error handling graceful
- [ ] Data quality verified (95%+ accuracy)
- [ ] Performance acceptable (< 10 min for all sites)
- [ ] Login-required sites work (Devex Pro)

### Data Verification
- [ ] Google Drive files created
- [ ] Google Sheets updated
- [ ] Data properly organized
- [ ] No duplicate entries
- [ ] All 23 organizations accessible

### Production Readiness
- [ ] No console errors
- [ ] Memory usage acceptable
- [ ] Network requests reasonable
- [ ] User experience smooth
- [ ] Documentation complete

## 📊 Expected Test Results

**Successful Test Run Should Show:**
- **Organizations Processed:** 23/23
- **Total Opportunities Found:** 50-200 (varies by day)
- **Media-Relevant Opportunities:** 10-30
- **Processing Time:** 5-10 minutes
- **Success Rate:** 95%+ per organization
- **Data Quality Score:** 95%+ accuracy

## 🚀 Next Steps After Testing

1. **Document any issues** found during testing
2. **Optimize selectors** for better data extraction
3. **Adjust timing** if anti-detection needed
4. **Scale testing** to production environment
5. **Set up monitoring** for ongoing collection

---

**Note:** This testing guide ensures comprehensive validation of the Media Procurement Platform's data collection capabilities across all 23 target organizations.

