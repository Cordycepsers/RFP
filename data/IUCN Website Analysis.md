# IUCN Website Analysis

**URL:** https://iucn.org/procurement/currently-running-tenders  
**Date:** 2025-08-14  
**Status:** ✅ ACCESSIBLE

## Website Structure

### Tender Display Format
- Well-structured table format with clear columns:
  - Submission Deadline
  - RfP Title and Link
  - IUCN Office (lead)
  - Country of Performance
  - Expected Contract Duration
  - Estimated Contract Value

### Current Opportunities (Sample)
1. **Communication and Graphic Design Services** - EUR 25,000 (Deadline: Aug 31, 2025)
2. **Website design and development** - USD 65,000 (Deadline: July 24, 2025)
3. **Congress photography and/or videography** - TBD (Under evaluation)
4. **Member Magazine** - CHF 150,000 (Extended to Sep 10, 2025)

### Key Multimedia/Creative Opportunities Found
- Communication and Graphic Design Services for Global Impact Report
- Website design and development projects
- Photography and videography services
- Member magazine production
- Documentation and reporting services

## Data Structure

### Reference Numbers
- Format: **IUCN-YY-MM-PNNNNN-N** (e.g., IUCN-25-07-P03812-1)
- Some tenders have specific RfP references
- Clear identification system for tracking

### Geographic Coverage
- Global reach: Africa (ESARO, PACO), Europe (ECARO), Americas (ORMACC), Asia
- Specific countries: Rwanda, Jordan, Thailand, Switzerland, Guatemala, etc.
- Regional and country-specific offices

### Contract Values
- Range from USD 7,000 to CHF 250,000
- Multiple currencies: USD, EUR, CHF, THB
- Clear budget information provided

## Scraping Considerations

### Advantages
- **Public access** (no login required)
- **Well-structured HTML table** format
- **Clear reference numbers** with consistent patterns
- **Complete information** including deadlines, budgets, locations
- **Multiple relevant opportunities** for multimedia/creative services

### Technical Details
- **Base URL**: https://iucn.org/procurement/currently-running-tenders
- **Data format**: HTML table with consistent structure
- **Reference extraction**: Clear IUCN-YY-MM-PNNNNN-N pattern
- **Pagination**: Single page with all current tenders
- **Update frequency**: Regular updates with new tenders

### Content Categories
- **Open tenders**: Currently accepting proposals
- **Tenders under evaluation**: Closed but not yet awarded
- **Contract award notices**: Completed tenders

## Relevant Opportunity Types for Multimedia/Creative Services

### High Priority
1. **Communication and Graphic Design Services** - Layout and production of reports
2. **Website design and development** - Digital platform creation
3. **Photography and videography** - Event documentation
4. **Member magazine** - Publication design and production

### Medium Priority
1. **Documentation services** - Report writing and formatting
2. **Training materials** - Educational content development
3. **Capacity building** - Workshop facilitation and materials
4. **Technical assistance** - Digital solutions and platforms

## Scraper Implementation Plan

1. **URL Pattern**: https://iucn.org/procurement/currently-running-tenders
2. **HTML Parsing**: Table rows with tender information
3. **Reference Extraction**: IUCN-YY-MM-PNNNNN-N pattern recognition
4. **Data Fields**: Deadline, title, office, country, duration, value
5. **Filtering**: Keyword matching for multimedia/creative services
6. **Rate Limiting**: Respectful request intervals
7. **Error Handling**: Robust parsing for different tender formats

## Expected Output Quality
- **High relevance**: IUCN frequently has communication and design needs
- **Clear reference numbers**: Easy tracking and identification
- **Complete information**: All necessary details for proposal preparation
- **Regular updates**: Fresh opportunities added frequently
- **Geographic diversity**: Global opportunities excluding restricted regions

