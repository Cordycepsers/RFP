# Proposaland System Architecture

## Overview
The Proposaland Opportunity Monitoring System is a comprehensive automated solution for discovering multimedia and creative service opportunities from 23 development organizations and NGOs. The system operates on a daily schedule, extracting, filtering, scoring, and reporting relevant opportunities.

## System Components

### 1. Core Monitoring Engine (`proposaland_monitor.py`)
- **Purpose**: Main orchestrator that coordinates all system components
- **Responsibilities**: 
  - Load configuration settings
  - Initialize web scrapers for all target websites
  - Coordinate data extraction and processing
  - Trigger email notifications
  - Handle logging and error management

### 2. Web Scraping Modules (`src/scrapers/`)
- **Purpose**: Extract opportunity data from target websites
- **Components**:
  - `base_scraper.py`: Abstract base class for all scrapers
  - `devex_scraper.py`: Devex-specific scraping logic
  - `undp_scraper.py`: UNDP procurement scraping
  - `ungm_scraper.py`: UN Global Marketplace scraping
  - `generic_scraper.py`: Fallback scraper for standard formats
- **Features**:
  - Handles different website structures
  - Implements retry mechanisms
  - Manages rate limiting and respectful crawling

### 3. Reference Number Extraction (`reference_number_extractor.py`)
- **Purpose**: Identify and extract project reference numbers using pattern recognition
- **Features**:
  - Organization-specific pattern matching
  - Confidence scoring (0.0-1.0)
  - Support for UN agencies, World Bank, NGO formats
  - Validation and quality assurance

### 4. Filtering and Scoring Engine (`src/filters/`)
- **Components**:
  - `keyword_filter.py`: Multimedia/creative keyword matching
  - `geographic_filter.py`: Regional exclusion logic
  - `budget_filter.py`: Budget range validation
  - `deadline_filter.py`: Minimum response time requirements
  - `scoring_engine.py`: Multi-criteria opportunity scoring

### 5. Data Processing Pipeline (`src/processors/`)
- **Components**:
  - `opportunity_processor.py`: Clean and standardize opportunity data
  - `deduplication.py`: Remove duplicate opportunities
  - `priority_classifier.py`: Assign priority levels (Critical/High/Medium/Low)

### 6. Output Generation (`src/outputs/`)
- **Components**:
  - `json_generator.py`: Create structured JSON output files
  - `excel_generator.py`: Generate professional Excel trackers
  - `report_generator.py`: Create summary reports and statistics

### 7. Email Notification System (`scheduler.py`)
- **Purpose**: Send daily digest emails with attachments
- **Features**:
  - SMTP configuration management
  - Email template processing
  - Attachment handling for Excel files
  - Delivery confirmation and retry logic

### 8. Scheduling and Automation (`src/scheduler/`)
- **Components**:
  - `daily_scheduler.py`: 9 AM daily execution
  - `task_manager.py`: Manage execution queue
  - `monitoring.py`: System health checks

## Data Flow

```
1. Configuration Loading
   ↓
2. Website Monitoring (23 sites in parallel)
   ↓
3. Data Extraction & Reference Number Detection
   ↓
4. Filtering (Keywords, Geography, Budget, Deadlines)
   ↓
5. Scoring & Prioritization
   ↓
6. Output Generation (JSON + Excel)
   ↓
7. Email Notification with Attachments
   ↓
8. Logging & Cleanup
```

## File Structure

```
proposaland/
├── config/
│   └── proposaland_config.json
├── src/
│   ├── scrapers/
│   │   ├── base_scraper.py
│   │   ├── devex_scraper.py
│   │   ├── undp_scraper.py
│   │   └── ...
│   ├── filters/
│   │   ├── keyword_filter.py
│   │   ├── geographic_filter.py
│   │   └── ...
│   ├── processors/
│   │   ├── opportunity_processor.py
│   │   └── ...
│   └── outputs/
│       ├── json_generator.py
│       ├── excel_generator.py
│       └── ...
├── data/
│   └── (temporary data storage)
├── output/
│   ├── proposaland_opportunities_YYYY-MM-DD.json
│   └── proposaland_tracker_YYYY-MM-DD.xlsx
├── logs/
│   └── proposaland_YYYY-MM-DD.log
├── proposaland_monitor.py
├── reference_number_extractor.py
├── scheduler.py
└── requirements.txt
```

## Key Features

### Reference Number Extraction
- **UN Agencies**: RFP/2024/001, ITB/2024/002, etc.
- **World Bank**: P123456, TF123456, etc.
- **NGOs**: SC/2024/MEDIA/001, IRC-2024-001, etc.
- **Generic**: 2024-001, ABC123456, etc.

### Scoring Algorithm
Weighted scoring based on:
- Keyword match (25%)
- Budget range (20%)
- Deadline urgency (15%)
- Source priority (15%)
- Geographic fit (10%)
- Sector relevance (10%)
- Reference number found (5% bonus)

### Priority Classification
- **Critical**: Score ≥ 0.8
- **High**: Score ≥ 0.6
- **Medium**: Score ≥ 0.4
- **Low**: Score < 0.4

## Security and Reliability

### Error Handling
- Comprehensive exception handling for network issues
- Graceful degradation when websites are unavailable
- Retry mechanisms with exponential backoff

### Data Quality
- Duplicate detection and removal
- Data validation and sanitization
- Reference number confidence scoring

### Monitoring
- Detailed logging for all operations
- Performance metrics tracking
- Email delivery confirmation

## Deployment Considerations

### Dependencies
- Python 3.8+ required
- Chrome/Chromium for Selenium-based scraping
- SMTP server access for email notifications

### Configuration
- Environment variables for sensitive data (email credentials)
- Configurable execution schedule
- Adjustable filtering and scoring parameters

### Maintenance
- Regular pattern updates for reference number extraction
- Website structure monitoring for scraper updates
- Performance optimization based on usage patterns

