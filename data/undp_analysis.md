# UNDP Procurement Website Analysis

## URL Structure
- Main site: https://procurement-notices.undp.org/
- Search page: https://procurement-notices.undp.org/search.cfm

## Key Findings
1. Clear search interface with filters:
   - Date range (FROM/TO)
   - Procurement process type
   - Category
   - Title search
   - Reference number search
   - Country office filter

2. Opportunity structure includes:
   - Title (clear and descriptive)
   - Reference number (e.g., UNDP-SLE-00167)
   - UNDP Office/Country
   - Deadline (with timezone)
   - Process type (RFP, ITB, IC, etc.)

3. Relevant opportunities found:
   - "Motion Graphic Designer/Editor" (UNDP-PHL/PHILIPPINES)
   - Various multimedia and communication opportunities

## Scraping Strategy
- Use search.cfm endpoint with parameters
- Extract opportunity data from search results
- Follow individual opportunity links for detailed information
- Reference numbers follow pattern: UNDP-[COUNTRY]-[NUMBER]
- Deadlines are clearly formatted with timezone

## Data Extraction Points
- Title: Clear text in opportunity listings
- Reference: Follows UNDP-XXX-XXXXX pattern
- Country: Listed as UNDP-[CODE]/[COUNTRY NAME]
- Deadline: Formatted date with timezone
- Process: RFP, ITB, IC, EOI, etc.
- Description: Available in individual opportunity pages

