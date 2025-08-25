"""
Enhanced output formatter for Proposaland opportunities.
Handles JSON/CSV export with structured data fields as specified by user.
Prepares data for Google Drive integration.
"""

import json
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger

from src.scrapers.base_scraper import OpportunityData


class EnhancedOutputFormatter:
    """
    Enhanced output formatter implementing user specifications:
    - Project (title), Funder, Location, Timeline (Published date, Deadline)
    - Reference number, Detailed description with requirements
    - Contact, Resources (submission portals & document links)
    - Structured JSON/CSV export ready for Google Drive
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # User-specified output fields
        self.output_fields = [
            'project_title',           # Project (title)
            'funder',                  # Funder
            'location',                # Location
            'published_date',          # Timeline - Published date
            'deadline',                # Timeline - Deadline
            'reference_number',        # Reference number
            'detailed_description',    # Detailed description with requirements
            'requirements',            # Specific requirements extracted
            'contact_email',           # Contact
            'submission_portal',       # Resources - submission portals
            'document_links',          # Resources - links to download files
            'keywords_found',          # Keywords that matched
            'opportunity_type',        # Type (Tender/Grant)
            'budget_range',            # Budget if available
            'source_url',              # Original source URL
            'extraction_date'          # When data was scraped
        ]
        
    def format_opportunities(self, opportunities: List[OpportunityData], website_name: str) -> Dict[str, Any]:
        """
        Format opportunities according to user specifications.
        """
        logger.info(f"Formatting {len(opportunities)} opportunities from {website_name}")
        
        formatted_data = {
            'metadata': {
                'website': website_name,
                'extraction_date': datetime.now().isoformat(),
                'total_opportunities': len(opportunities),
                'format_version': '1.0',
                'data_fields': self.output_fields
            },
            'opportunities': []
        }
        
        for opp in opportunities:
            formatted_opp = self._format_single_opportunity(opp)
            formatted_data['opportunities'].append(formatted_opp)
        
        return formatted_data
    
    def _format_single_opportunity(self, opp: OpportunityData) -> Dict[str, Any]:
        """Format single opportunity according to user specifications."""
        
        # Format dates properly
        published_date = getattr(opp, 'date_found', opp.extracted_date)
        if published_date:
            published_date = published_date.isoformat() if hasattr(published_date, 'isoformat') else published_date
        
        deadline = opp.deadline.isoformat() if opp.deadline else None
        
        # Process document links for Google Drive preparation
        document_links = self._process_document_links(opp)
        
        # Extract requirements from description
        requirements = self._extract_requirements(opp.description)
        
        formatted_opp = {
            'project_title': opp.title or '',
            'funder': getattr(opp, 'funding_organization', opp.organization) or opp.organization or '',
            'location': opp.location or '',
            'published_date': published_date,
            'deadline': deadline,
            'reference_number': opp.reference_number or '',
            'detailed_description': opp.description or '',
            'requirements': requirements,
            'contact_email': getattr(opp, 'contact_email', '') or '',
            'submission_portal': getattr(opp, 'submission_portal', '') or '',
            'document_links': document_links,
            'keywords_found': opp.keywords_found or [],
            'opportunity_type': getattr(opp, 'opportunity_type', '') or '',
            'budget_range': self._format_budget(opp.budget),
            'source_url': opp.source_url or '',
            'extraction_date': datetime.now().isoformat()
        }
        
        return formatted_opp
    
    def _process_document_links(self, opp: OpportunityData) -> List[Dict[str, str]]:
        """Process document links for structured output."""
        document_links = []
        
        if hasattr(opp, 'document_urls') and opp.document_urls:
            for i, url in enumerate(opp.document_urls):
                doc_info = {
                    'url': url,
                    'type': self._identify_document_type(url),
                    'filename': self._extract_filename_from_url(url),
                    'order': i + 1
                }
                document_links.append(doc_info)
        
        return document_links
    
    def _identify_document_type(self, url: str) -> str:
        """Identify document type from URL."""
        url_lower = url.lower()
        
        if 'terms' in url_lower or 'tor' in url_lower:
            return 'Terms of Reference'
        elif 'rfp' in url_lower:
            return 'Request for Proposal'
        elif 'rfq' in url_lower:
            return 'Request for Quotation'
        elif 'specification' in url_lower:
            return 'Technical Specifications'
        elif 'form' in url_lower:
            return 'Application Form'
        else:
            return 'Supporting Document'
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = parsed.path.split('/')[-1]
            return filename if filename else 'document.pdf'
        except:
            return 'document.pdf'
    
    def _extract_requirements(self, description: str) -> str:
        """Extract specific requirements from description."""
        if not description:
            return ''
        
        # Look for requirement indicators
        requirement_keywords = [
            'requirements', 'required', 'must have', 'minimum', 'qualifications',
            'experience', 'expertise', 'skills', 'criteria', 'specifications'
        ]
        
        sentences = description.split('.')
        requirement_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in requirement_keywords):
                requirement_sentences.append(sentence.strip())
        
        return '. '.join(requirement_sentences[:3])  # Top 3 requirement sentences
    
    def _format_budget(self, budget: Any) -> str:
        """Format budget information."""
        if not budget:
            return ''
        
        if isinstance(budget, (int, float)):
            return f"${budget:,.2f}"
        elif isinstance(budget, str):
            return budget
        else:
            return str(budget)
    
    def export_to_json(self, formatted_data: Dict, filename: str) -> str:
        """Export formatted data to JSON file."""
        json_file = self.output_dir / f"{filename}.json"
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON export completed: {json_file}")
            return str(json_file)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise
    
    def export_to_csv(self, formatted_data: Dict, filename: str) -> str:
        """Export formatted data to CSV file for Google Sheets compatibility."""
        csv_file = self.output_dir / f"{filename}.csv"
        
        try:
            opportunities = formatted_data['opportunities']
            if not opportunities:
                logger.warning("No opportunities to export to CSV")
                return str(csv_file)
            
            # Flatten the data for CSV
            flattened_data = []
            for opp in opportunities:
                flattened_opp = opp.copy()
                
                # Convert lists to strings for CSV compatibility
                flattened_opp['keywords_found'] = ', '.join(opp['keywords_found'])
                
                # Flatten document links
                doc_links_text = []
                for doc in opp['document_links']:
                    doc_links_text.append(f"{doc['type']}: {doc['url']}")
                flattened_opp['document_links'] = ' | '.join(doc_links_text)
                
                flattened_data.append(flattened_opp)
            
            # Create DataFrame and export
            df = pd.DataFrame(flattened_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            logger.info(f"CSV export completed: {csv_file}")
            return str(csv_file)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def prepare_for_gdrive(self, formatted_data: Dict, filename: str) -> Dict[str, str]:
        """
        Prepare files for Google Drive upload.
        Returns dict with file paths for JSON and CSV exports.
        """
        logger.info(f"Preparing files for Google Drive upload: {filename}")
        
        try:
            # Export both formats
            json_file = self.export_to_json(formatted_data, filename)
            csv_file = self.export_to_csv(formatted_data, filename)
            
            # Create summary info for upload
            summary = {
                'websites_scraped': formatted_data['metadata'].get('websites_scraped', ['Multiple']),
                'total_opportunities': formatted_data['metadata']['total_opportunities'],
                'extraction_date': formatted_data['metadata']['extraction_date'],
                'json_file': json_file,
                'csv_file': csv_file
            }
            
            # Save summary
            summary_file = self.output_dir / f"{filename}_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            return {
                'json_file': json_file,
                'csv_file': csv_file,
                'summary_file': str(summary_file)
            }
            
        except Exception as e:
            logger.error(f"Error preparing files for Google Drive: {e}")
            raise
    
    def create_daily_report(self, all_website_data: List[Dict]) -> str:
        """Create consolidated daily report across all websites."""
        report_date = datetime.now().strftime('%Y%m%d')
        report_filename = f"proposaland_daily_report_{report_date}"
        
        # Consolidate all opportunities
        all_opportunities = []
        website_summary = {}
        
        for website_data in all_website_data:
            website_name = website_data['metadata']['website']
            opportunities = website_data['opportunities']
            
            all_opportunities.extend(opportunities)
            website_summary[website_name] = {
                'count': len(opportunities),
                'extraction_date': website_data['metadata']['extraction_date']
            }
        
        # Create consolidated report
        consolidated_report = {
            'metadata': {
                'report_date': datetime.now().isoformat(),
                'extraction_date': datetime.now().isoformat(),
                'total_opportunities': len(all_opportunities),
                'websites_scraped': list(website_summary.keys()),
                'website_summary': website_summary,
                'format_version': '1.0'
            },
            'opportunities': all_opportunities
        }
        
        # Export consolidated report
        files = self.prepare_for_gdrive(consolidated_report, report_filename)
        
        logger.info(f"Daily report created with {len(all_opportunities)} opportunities from {len(website_summary)} websites")
        
        return files['json_file']
    
    def generate_statistics_report(self, formatted_data: Dict) -> Dict[str, Any]:
        """Generate statistics report for monitoring."""
        opportunities = formatted_data['opportunities']
        
        stats = {
            'total_count': len(opportunities),
            'by_funder': {},
            'by_location': {},
            'by_type': {},
            'by_keyword': {},
            'with_deadlines': 0,
            'with_contact': 0,
            'with_documents': 0,
            'avg_keywords_per_opp': 0
        }
        
        total_keywords = 0
        
        for opp in opportunities:
            # Count by funder
            funder = opp['funder']
            stats['by_funder'][funder] = stats['by_funder'].get(funder, 0) + 1
            
            # Count by location
            location = opp['location']
            stats['by_location'][location] = stats['by_location'].get(location, 0) + 1
            
            # Count by type
            opp_type = opp['opportunity_type']
            stats['by_type'][opp_type] = stats['by_type'].get(opp_type, 0) + 1
            
            # Count keywords
            keywords = opp['keywords_found']
            total_keywords += len(keywords)
            for keyword in keywords:
                stats['by_keyword'][keyword] = stats['by_keyword'].get(keyword, 0) + 1
            
            # Count features
            if opp['deadline']:
                stats['with_deadlines'] += 1
            if opp['contact_email']:
                stats['with_contact'] += 1
            if opp['document_links']:
                stats['with_documents'] += 1
        
        # Calculate averages
        if len(opportunities) > 0:
            stats['avg_keywords_per_opp'] = round(total_keywords / len(opportunities), 2)
        
        return stats
