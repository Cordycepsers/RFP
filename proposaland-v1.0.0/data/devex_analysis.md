# Devex Website Analysis

## URL Structure
- Main site: https://www.devex.com/
- Funding section: https://www.devex.com/funding-overview
- Funding search appears to require authentication or different URL

## Key Findings
1. Devex has a funding opportunities section but may require login/subscription
2. The site has a search interface for funding opportunities
3. Structure includes:
   - Funding insights
   - Focus on funders
   - Top implementers
   - Search filters for keywords, regions, funders

## Scraping Strategy
- May need to handle authentication
- Search interface suggests API or form-based queries
- Keywords can be searched in the main search box
- Filters available for: Funding Activity, Programs, Tenders & Grants, Contract Awards

## Next Steps
- Implement generic scraper that can handle authentication
- Focus on extracting opportunity data from search results
- Handle pagination and filtering
- Extract reference numbers from opportunity details

