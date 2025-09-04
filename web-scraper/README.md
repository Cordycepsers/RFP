# 🔍 UNDP Media Procurement Web Scraper

A comprehensive web scraping system designed to extract media-related procurement opportunities from UNDP and other international organizations' websites. Built for Ubuntu deployment with visibility to employees requiring webscraping reports.

## ✨ Features

### 🚀 Core Functionality
- **Infinite Scroll Handling**: Automatically loads all available projects from paginated sites
- **Intelligent Keyword Filtering**: Identifies media/communication-related opportunities
- **Multi-Site Support**: Configurable for 23+ international procurement websites
- **Document Download**: Automatically downloads project documentation
- **Google Services Integration**: Uploads data to Google Sheets and Google Drive
- **Async Processing**: High-performance concurrent processing

### 📊 Data Extraction
- Project titles, references, deadlines, offices
- Detailed project descriptions and requirements
- Contact information and application processes
- Budget information and procurement processes
- Document attachments and specifications

### 🎯 Media Keyword Targeting
The system targets projects containing keywords such as:
```
video, photo, film, multimedia, podcast, animation, audiovisual, 
media, communication, production, graphic, design, branding, 
creative, advertising, marketing, documentary, broadcasting, 
digital, content, visualization, photography, filming, editing, 
post-production, cinematography
```

## 📁 System Architecture

```
web-scraper/
├── scraper.py              # Main async web scraper
├── document_handler.py     # Document download & processing
├── google_services.py      # Google API integration
├── websites.json          # Multi-site configuration
├── test_selectors.py      # Configuration validation
└── test_scraper_undp.py   # UNDP-specific testing
```

## 🛠 Components

### 1. **WebScraper Class** (`scraper.py`)
- Async Playwright-based browser automation
- Infinite scroll handling for dynamic content
- Intelligent project filtering and extraction
- Error handling and retry logic

### 2. **DocumentHandler Class** (`document_handler.py`)
- Multi-step document download workflows
- File type detection and MIME type handling
- Structured filename generation
- Local storage with automatic cleanup

### 3. **GoogleServices Integration** (`google_services.py`)
- Google Sheets data export
- Google Drive document storage
- Service account authentication
- Batch upload operations

### 4. **Configuration System** (`websites.json`)
- 23 pre-configured international procurement sites
- Flexible CSS selector definitions
- Keyword filtering rules
- Document download workflows

## 🚦 Usage Examples

### Basic UNDP Scraping
```python
# Run UNDP-specific test
python test_scraper_undp.py
```

### Full Multi-Site Scraping
```python
# Run complete scraper
python scraper.py
```

### Configuration Validation
```python
# Test selectors before scraping
python test_selectors.py
```

## 📈 Recent Results

**UNDP Procurement Notices**: Successfully scraped **751 total projects**, identified **46 media-related opportunities** including:

- **Design Services**: Graphic design, branding, architectural design
- **Media Production**: Video production, documentary creation, audiovisual content
- **Communication**: Marketing strategies, media planning, communication consulting
- **Digital Services**: Website development, multimedia systems, digital platforms
- **Creative Services**: Motion graphics, animation, creative content development

## 🔧 Configuration

### Website Configuration Example
```json
{
  "name": "UNDP Procurement Notices - Media Projects",
  "url": "https://procurement-notices.undp.org/",
  "selectors": {
    "listItems": {
      "container": "a[href*='view_negotiation.cfm'], a[href*='view_notice.cfm']",
      "title": "div:nth-child(1)",
      "reference": "div:nth-child(2)",
      "deadline": "div:nth-child(5)"
    }
  },
  "keywordFiltering": {
    "enabled": true,
    "keywords": ["video", "photo", "design", "media"],
    "matchType": "any"
  }
}
```

### Document Download Workflow
```json
{
  "documentDownloadWorkflow": {
    "enabled": true,
    "steps": [
      {
        "action": "click_authentication_link",
        "selector": "a[href*='auth']",
        "description": "Authenticate for document access"
      },
      {
        "action": "download_all_documents", 
        "selector": "a[href*='.pdf']",
        "maxDocuments": 10
      }
    ]
  }
}
```

## 🌍 Supported Organizations

The system supports 23+ international procurement websites including:
- UNDP (UN Development Programme)
- UNGM (UN Global Marketplace)
- The Global Fund
- World Bank Projects & Operations
- Asian Development Bank
- African Development Bank
- Various NGOs and international organizations

## 🔄 Infinite Scroll Implementation

The scraper automatically detects and handles infinite scroll pagination:

```python
async def _handle_infinite_scroll(self, container_selector, max_scrolls=50):
    """Progressively loads all available content"""
    while scroll_count < max_scrolls and no_change_count < 3:
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_function(
            f"document.querySelectorAll('{container_selector}').length > {current_count}",
            timeout=5000
        )
```

## 📊 Output Formats

### JSON Export
```json
{
  "title": "RFP- Graphic Design and Branding Services",
  "reference": "UNDP-UGA-00462", 
  "office": "UNDP-UGA/UGANDA",
  "deadline": "16-Sep-25 04:59 PM (New York time)",
  "documents": [
    {
      "url": "https://drive.google.com/file/d/...",
      "name": "project_specifications.pdf",
      "type": "document"
    }
  ]
}
```

### Google Sheets Integration
Automatically exports data to spreadsheet with columns:
- Title, Reference, Organization, Deadline, Published Date
- Source Website, Scraped Timestamp  
- Document Links (Google Drive URLs)

## 🛡 Error Handling & Reliability

- **Graceful failure handling**: Continues processing even if individual projects fail
- **Rate limiting**: Respectful delays between requests
- **Retry logic**: Automatic retry for failed operations
- **Cleanup procedures**: Automatic temporary file cleanup
- **Logging**: Comprehensive progress and error logging

## 🔮 Future Enhancements

- **Email notifications** for new opportunities
- **Advanced filtering** by budget ranges and deadlines
- **Automated bidding assistant** integration
- **Multi-language support** for international sites
- **Real-time monitoring** with scheduled runs
- **Machine learning** for opportunity scoring

---

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install playwright asyncio google-api-python-client python-dotenv
   playwright install
   ```

2. **Configure Google API credentials** (`.env` file)

3. **Run the scraper**:
   ```bash
   python test_scraper_undp.py  # Test with UNDP
   python scraper.py            # Full multi-site scraping
   ```

## 📋 Requirements Compliance

✅ **Ubuntu Deployment Ready**: Designed for server deployment  
✅ **Employee Visibility**: Generates reports for team access  
✅ **Multi-Site Coverage**: 23+ international procurement sources  
✅ **Document Handling**: Automatic download and Google Drive storage  
✅ **Data Export**: Google Sheets integration for easy access  
✅ **Scalable Architecture**: Async processing for high performance

---

*Built for efficient procurement opportunity discovery and team collaboration.*
