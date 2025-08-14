# UNGM Website Analysis

**URL:** https://www.ungm.org/Public/Notice  
**Date:** 2025-08-13  
**Status:** ✅ ACCESSIBLE

## Website Structure

### Search Interface
- Advanced search filters available
- Title, Description, Reference search fields
- Date range filters (Published between, Deadline between)
- Organization filter
- Beneficiary country filter
- Type of opportunity filters (RFP, RFQ, ITB, etc.)
- Goods and services code search

### Results Display
- Table format with columns:
  - Title
  - Deadline
  - Published date
  - Organization
  - Type of opportunity
  - Reference number
  - Beneficiary country/territory

### Sample Opportunities Found
1. **RFP/2025/ACNUR/MEX/047** - Sistema de Registro (UNHCR, Mexico)
2. **UNDP-FJI-00666** - Financial Inclusion in Kiribati (UNDP, Kiribati)
3. **UNW-FJI-2025-00021-2** - Customer Services Training (UN-Women, Samoa)
4. **UNDP-FJI-00669** - IT Tech Firm Support (UNDP, Vanuatu)

## Key Data Points
- **Total opportunities**: 1,746 currently available
- **Results per page**: 15
- **Pagination**: Available for browsing all results
- **Reference number patterns**: 
  - RFP/YYYY/ORG/COUNTRY/NNN
  - ORG-COUNTRY-NNNNN
  - Various formats per organization

## Scraping Considerations

### Advantages
- Public access (no login required)
- Well-structured HTML table
- Clear reference number formats
- Comprehensive metadata (deadline, organization, country)
- Search filters for targeting relevant opportunities

### Technical Details
- **Base URL**: https://www.ungm.org/Public/Notice
- **Search endpoint**: Same URL with POST parameters
- **Pagination**: Available for accessing all 1,746+ opportunities
- **Data format**: HTML table with consistent structure
- **Reference extraction**: Multiple patterns per organization

### Filtering Opportunities
- Can filter by keywords in title/description
- Geographic filtering by beneficiary country
- Organization filtering available
- Type of opportunity filtering (RFP, RFQ, etc.)

### Relevant Opportunity Types
- Request for proposal (RFP)
- Request for quotation (RFQ)
- Invitation to bid (ITB)
- Call for individual consultants
- Grant support-call for proposal

## Scraper Implementation Plan

1. **URL Pattern**: https://www.ungm.org/Public/Notice
2. **Search Parameters**: POST request with filters
3. **HTML Parsing**: Table rows with opportunity data
4. **Reference Extraction**: Multiple patterns per UN organization
5. **Pagination**: Handle multiple pages of results
6. **Rate Limiting**: Implement delays between requests

