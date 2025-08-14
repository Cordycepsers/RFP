# Global Fund Website Analysis

**URL:** https://www.theglobalfund.org/en/business-opportunities/  
**Tender URL:** https://fa-enmo-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/NegotiationAbstracts  
**Date:** 2025-08-13  
**Status:** ✅ ACCESSIBLE

## Website Structure

### Main Page
- Business & Consultancy Opportunities landing page
- "VIEW OPEN TENDERS" button leads to Oracle-based system
- Related resources and procurement policy documents

### Tender Listing System
- Oracle Cloud-based procurement system
- Table format with columns:
  - Negotiation ID (Reference)
  - Title
  - Negotiation Type (RFP, RFQ, etc.)
  - Status (Active, Closed, Amended)
  - Posting Date
  - Open Date
  - Close Date
  - Details (clickable links)

### Sample Opportunities Found
1. **TGF-25-46** - SIGECA Rollout Angola (RFP, Active, Close: 29/Aug/2025)
2. **TGF-25-45** - End-term evaluation of GF's C19RM response mechanism (RFP, Active, Close: 12/Sep/2025)
3. **TGF-25-44** - TA for Strengthening Climate and Health Data Systems (RFP, Active, Close: 15/Aug/2025)
4. **TGF-25-37,1** - Field Security Services (RFP, Active, Close: 15/Aug/2025)

## Key Data Points
- **Reference pattern**: TGF-YY-NN (e.g., TGF-25-46)
- **Opportunity types**: Primarily RFP (Request for Proposal)
- **Status types**: Active, Closed, Amended
- **Geographic scope**: Global (Angola, DRC, Mauritania, Guinea Bissau, Togo mentioned)
- **Time zone**: Central European Time

## Scraping Considerations

### Advantages
- Public access (no login required for viewing)
- Structured Oracle table format
- Clear reference number pattern
- Comprehensive metadata (dates, status, type)
- Search functionality available

### Technical Details
- **Base URL**: https://www.theglobalfund.org/en/business-opportunities/
- **Tender URL**: Oracle Cloud system (complex URL with parameters)
- **Data format**: HTML table with consistent structure
- **Reference pattern**: TGF-YY-NN format
- **Search**: Title search available

### Challenges
- Oracle Cloud system may have session management
- Complex URL structure with parameters
- May require handling of dynamic content loading

### Relevant Opportunity Types
- Request for Proposal (RFP) - Primary type
- Technical Assistance (TA)
- Local Fund Agent (LFA) services
- Evaluation services
- Field security services

## Scraper Implementation Plan

1. **URL Pattern**: Start from main page, navigate to Oracle system
2. **Session Management**: May need to handle Oracle session cookies
3. **HTML Parsing**: Table rows with tender data
4. **Reference Extraction**: TGF-YY-NN pattern
5. **Date Parsing**: Handle Central European Time format
6. **Status Filtering**: Focus on "Active" opportunities
7. **Rate Limiting**: Implement delays for Oracle system

## Potential Multimedia/Creative Opportunities
- Communication and outreach services
- Evaluation and documentation services
- Training and capacity building
- Data visualization and reporting
- Campaign development

