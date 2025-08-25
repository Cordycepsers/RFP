# Google Sheets API Setup Guide

## 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API and Google Drive API

## 2. Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Enter name: `devex-scraper`
4. Click **Create and Continue**
5. Skip role assignment (click **Continue**)
6. Click **Done**

## 3. Generate Credentials

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Select **JSON** format
5. Download the JSON file
6. Rename it to `google-credentials.json`

## 4. Share Spreadsheet with Service Account

1. Open the downloaded JSON file
2. Copy the `client_email` value
3. In Google Sheets, share your spreadsheet with this email
4. Give **Editor** permissions

## 5. Update Script Configuration

```python
# In the main() function, update this path:
GOOGLE_CREDENTIALS_PATH = "path/to/your/google-credentials.json"
```

## 6. Install Dependencies

```bash
pip install -r requirements_devex_scraper.txt
```

## 7. Install Chrome WebDriver

### Option A: Manual Download
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver from [here](https://chromedriver.chromium.org/)
3. Add to PATH or place in script directory

### Option B: Automatic (Recommended)
```bash
pip install webdriver-manager
```

Then update the script to use WebDriverManager:
```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# In setup_driver method:
service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
```

## 8. Run the Scraper

```bash
python3 devex_selenium_scraper.py
```

## Troubleshooting

### Common Issues:

1. **403 Forbidden Error**: Service account email not shared with spreadsheet
2. **ChromeDriver not found**: Install ChromeDriver or use WebDriverManager
3. **Timeout errors**: Increase wait times or check internet connection
4. **No opportunities found**: Check if Devex page structure changed

### Debug Mode:
- Comment out `--headless` option to see browser actions
- Add more `time.sleep()` calls if pages load slowly
- Check console output for detailed error messages

Google API: AIzaSyD4nayg6uC31z9R92H9I1By_DYBxwxQ0tU

"@playwright/mcp@latest"
"--extension"

