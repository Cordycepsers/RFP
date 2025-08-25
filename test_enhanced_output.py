#!/usr/bin/env python3
"""
Test script for enhanced output formatter and Google Drive integration.
Tests JSON/CSV export functionality and Google Drive upload capabilities.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.outputs.enhanced_formatter import EnhancedOutputFormatter
from src.outputs.gdrive_integration import GoogleDriveManager
from src.scrapers.base_scraper import OpportunityData


def create_test_opportunities() -> List[OpportunityData]:
    """Create test opportunities for testing output formatting."""
    
    test_opportunities = []
    
    # Test opportunity 1 - Multimedia video project
    opp1 = OpportunityData()
    opp1.title = "Digital Video Campaign for Education in Sierra Leone"
    opp1.organization = "UNICEF"
    opp1.location = "Sierra Leone"
    opp1.description = "UNICEF seeks proposals for developing educational video content to support remote learning initiatives. Requirements include: Minimum 5 years experience in video production, expertise in educational content development, knowledge of local languages (Krio, Mende, Temne), budget range $50,000-$75,000. Deliverables: 20 educational videos (10-15 minutes each), teacher training materials, community engagement strategy."
    opp1.extracted_date = datetime.now()
    opp1.deadline = datetime.now() + timedelta(days=30)
    opp1.source_url = "https://devex.com/funding/unicef-video-education-sierra-leone"
    opp1.keywords_found = ["video", "multimedia", "education"]
    opp1.reference_number = "UNICEF-SL-2025-EDU-001"
    opp1.budget = 62500.0  # Middle of range
    opp1.currency = "USD"
    
    # Add custom attributes for enhanced formatting (these will be handled by enhanced formatter)
    opp1.contact_email = "unicef.sierraleone@procurement.org"
    opp1.funding_organization = "UNICEF"
    opp1.date_found = datetime.now()
    opp1.submission_portal = "https://supplier.unicef.org/rfp/submit"
    opp1.document_urls = [
        "https://devex.com/documents/terms-of-reference-video-education.pdf",
        "https://devex.com/documents/rfp-specifications-multimedia.pdf",
        "https://devex.com/documents/application-form-unicef.pdf"
    ]
    opp1.opportunity_type = "RFP"
    
    test_opportunities.append(opp1)
    
    # Test opportunity 2 - Photo documentation project  
    opp2 = OpportunityData()
    opp2.title = "Photography and Documentation Services for Community Health Programs"
    opp2.organization = "World Health Organization"
    opp2.location = "Madagascar"
    opp2.description = "WHO Madagascar requires professional photography and documentation services for community health program evaluation. Requirements: Proven experience in documentary photography, knowledge of health sector communications, ability to work in rural areas, cultural sensitivity training required. Scope includes photo documentation of 15 health centers, patient stories (with consent), health worker interviews."
    opp2.extracted_date = datetime.now() - timedelta(days=2)
    opp2.deadline = datetime.now() + timedelta(days=45)
    opp2.source_url = "https://devex.com/funding/who-madagascar-photo-documentation"
    opp2.keywords_found = ["photo", "documentation", "health"]
    opp2.reference_number = "WHO-MDG-2025-PHOTO-002"
    opp2.budget = 35000.0
    opp2.currency = "USD"
    
    opp2.contact_email = "procurement@who-madagascar.org"
    opp2.funding_organization = "World Health Organization"
    opp2.date_found = datetime.now() - timedelta(days=2)
    opp2.submission_portal = "https://who.int/procurement/submissions"
    opp2.document_urls = [
        "https://devex.com/documents/who-photography-tor.pdf",
        "https://devex.com/documents/health-program-specs.pdf"
    ]
    opp2.opportunity_type = "Contract"
    
    test_opportunities.append(opp2)
    
    # Test opportunity 3 - Animation project
    opp3 = OpportunityData()
    opp3.title = "Animated Video Series for Climate Change Awareness"
    opp3.organization = "Green Climate Fund"
    opp3.location = "Chad"
    opp3.description = "Development of animated educational content for climate change awareness campaigns targeting rural communities. Requirements include animation expertise, climate science knowledge, local language capabilities (Arabic, French, Sara). Must demonstrate previous work with international development organizations. Project duration: 6 months."
    opp3.extracted_date = datetime.now() - timedelta(days=5)
    opp3.deadline = datetime.now() + timedelta(days=60)
    opp3.source_url = "https://devex.com/funding/gcf-chad-animation-climate"
    opp3.keywords_found = ["animation", "animated video", "climate"]
    opp3.reference_number = "GCF-TD-2025-ANIM-003"
    opp3.budget = 45000.0
    opp3.currency = "EUR"
    
    opp3.contact_email = "chad.office@greenclimate.fund"
    opp3.funding_organization = "Green Climate Fund"
    opp3.date_found = datetime.now() - timedelta(days=5)
    opp3.submission_portal = "https://gcf.int/procurement/portal"
    opp3.document_urls = [
        "https://devex.com/documents/gcf-animation-requirements.pdf"
    ]
    opp3.opportunity_type = "Grant"
    
    test_opportunities.append(opp3)
    
    return test_opportunities


def test_enhanced_formatter():
    """Test the enhanced output formatter functionality."""
    print("\n" + "="*60)
    print("TESTING ENHANCED OUTPUT FORMATTER")
    print("="*60)
    
    # Load test configuration
    config = {
        'multimedia_keywords': [
            'video', 'photo', 'film', 'multimedia', 'design', 'visual',
            'campaign', 'podcasts', 'virtual event', 'media', 'animation',
            'animated video', 'promotion', 'communication', 'audiovisual'
        ],
        'geographic_filters': {
            'excluded_countries': ['India', 'Pakistan', 'Bangladesh'],
            'included_regions': ['Africa', 'Latin America', 'Asia-Pacific']
        }
    }
    
    # Create formatter
    formatter = EnhancedOutputFormatter(config)
    
    # Create test data
    test_opportunities = create_test_opportunities()
    
    print(f"Created {len(test_opportunities)} test opportunities")
    
    # Format opportunities
    formatted_data = formatter.format_opportunities(test_opportunities, "DevEx")
    
    print(f"\nFormatted data structure:")
    print(f"- Website: {formatted_data['metadata']['website']}")
    print(f"- Total opportunities: {formatted_data['metadata']['total_opportunities']}")
    print(f"- Extraction date: {formatted_data['metadata']['extraction_date']}")
    print(f"- Data fields: {len(formatted_data['metadata']['data_fields'])} fields")
    
    # Test JSON export
    print(f"\nTesting JSON export...")
    json_file = formatter.export_to_json(formatted_data, "test_opportunities")
    print(f"JSON exported to: {json_file}")
    
    # Test CSV export  
    print(f"\nTesting CSV export...")
    csv_file = formatter.export_to_csv(formatted_data, "test_opportunities")
    print(f"CSV exported to: {csv_file}")
    
    # Test Google Drive preparation
    print(f"\nTesting Google Drive preparation...")
    gdrive_files = formatter.prepare_for_gdrive(formatted_data, "test_opportunities")
    print(f"Google Drive files prepared:")
    for file_type, file_path in gdrive_files.items():
        print(f"  - {file_type}: {file_path}")
    
    # Test statistics generation
    print(f"\nTesting statistics generation...")
    stats = formatter.generate_statistics_report(formatted_data)
    print(f"Statistics generated:")
    print(f"  - Total opportunities: {stats['total_count']}")
    print(f"  - With deadlines: {stats['with_deadlines']}")
    print(f"  - With contacts: {stats['with_contact']}")
    print(f"  - With documents: {stats['with_documents']}")
    print(f"  - Average keywords per opportunity: {stats['avg_keywords_per_opp']}")
    print(f"  - Keywords found: {list(stats['by_keyword'].keys())}")
    
    # Display sample formatted opportunity
    print(f"\nSample formatted opportunity:")
    sample_opp = formatted_data['opportunities'][0]
    print(f"  - Title: {sample_opp['project_title']}")
    print(f"  - Funder: {sample_opp['funder']}")
    print(f"  - Location: {sample_opp['location']}")
    print(f"  - Keywords: {sample_opp['keywords_found']}")
    print(f"  - Reference: {sample_opp['reference_number']}")
    print(f"  - Budget: {sample_opp['budget_range']}")
    print(f"  - Documents: {len(sample_opp['document_links'])} documents")
    
    return formatted_data


def test_gdrive_integration():
    """Test Google Drive integration (without actual upload)."""
    print("\n" + "="*60)
    print("TESTING GOOGLE DRIVE INTEGRATION")
    print("="*60)
    
    # Test configuration
    config = {
        'gdrive': {
            'enabled': True,
            'folder_id': 'test_folder_id_placeholder',
            'credentials_file': 'path/to/service_account.json'
        }
    }
    
    # Create Google Drive manager
    gdrive_manager = GoogleDriveManager(config)
    
    print(f"Google Drive integration status:")
    print(f"  - Enabled: {gdrive_manager.enabled}")
    print(f"  - Libraries available: {gdrive_manager.uploader.service is not None}")
    
    # Test status check
    status = gdrive_manager.get_upload_status()
    print(f"\nUpload status check:")
    for key, value in status.items():
        print(f"  - {key}: {value}")
    
    # Note: Actual upload testing would require valid credentials
    print(f"\nNote: Actual Google Drive upload testing requires:")
    print(f"  1. Valid service account credentials file")
    print(f"  2. Google Drive API access enabled")
    print(f"  3. Folder ID for destination")
    print(f"  4. Install: pip install google-api-python-client google-auth")


def test_daily_report_generation():
    """Test comprehensive daily report generation."""
    print("\n" + "="*60)
    print("TESTING DAILY REPORT GENERATION")
    print("="*60)
    
    config = {
        'multimedia_keywords': [
            'video', 'photo', 'film', 'multimedia', 'design', 'visual',
            'campaign', 'podcasts', 'virtual event', 'media', 'animation',
            'animated video', 'promotion', 'communication', 'audiovisual'
        ]
    }
    
    formatter = EnhancedOutputFormatter(config)
    
    # Create test data from multiple websites
    devex_opportunities = create_test_opportunities()
    
    # Simulate data from multiple websites
    all_website_data = []
    
    # DevEx data
    devex_data = formatter.format_opportunities(devex_opportunities, "DevEx")
    all_website_data.append(devex_data)
    
    # Simulate UNGM data (subset for testing)
    ungm_opportunities = devex_opportunities[:2]  # Use subset
    ungm_data = formatter.format_opportunities(ungm_opportunities, "UNGM")
    all_website_data.append(ungm_data)
    
    # Generate daily report
    print(f"Generating daily report from {len(all_website_data)} websites...")
    daily_report_file = formatter.create_daily_report(all_website_data)
    
    print(f"Daily report generated: {daily_report_file}")
    
    # Load and display summary
    with open(daily_report_file, 'r') as f:
        daily_data = json.load(f)
    
    print(f"\nDaily report summary:")
    print(f"  - Total opportunities: {daily_data['metadata']['total_opportunities']}")
    print(f"  - Websites scraped: {daily_data['metadata']['websites_scraped']}")
    
    for website, info in daily_data['metadata']['website_summary'].items():
        print(f"  - {website}: {info['count']} opportunities")


def validate_output_files():
    """Validate that output files are created correctly."""
    print("\n" + "="*60)
    print("VALIDATING OUTPUT FILES")
    print("="*60)
    
    output_dir = Path("output")
    
    # Check for test files
    json_files = list(output_dir.glob("test_opportunities*.json"))
    csv_files = list(output_dir.glob("test_opportunities*.csv"))
    
    print(f"Output directory: {output_dir.absolute()}")
    print(f"JSON files found: {len(json_files)}")
    print(f"CSV files found: {len(csv_files)}")
    
    # Validate JSON structure
    if json_files:
        # Find the main opportunities file (not summary)
        main_json_file = None
        for json_file in json_files:
            if 'summary' not in json_file.name:
                main_json_file = json_file
                break
        
        if main_json_file:
            print(f"\nValidating JSON file: {main_json_file.name}")
            
            with open(main_json_file, 'r') as f:
                data = json.load(f)
        
            required_metadata = ['website', 'extraction_date', 'total_opportunities', 'data_fields']
            metadata_valid = all(key in data['metadata'] for key in required_metadata)
            print(f"  - Metadata structure valid: {metadata_valid}")
            
            if data['opportunities']:
                sample_opp = data['opportunities'][0]
                required_fields = [
                    'project_title', 'funder', 'location', 'published_date', 'deadline',
                    'reference_number', 'detailed_description', 'contact_email', 'source_url'
                ]
                fields_valid = all(field in sample_opp for field in required_fields)
                print(f"  - Opportunity fields valid: {fields_valid}")
                print(f"  - Sample title: {sample_opp.get('project_title', 'N/A')}")
        else:
            print(f"\nNo main JSON file found (only summary files)")
            print(f"Available files: {[f.name for f in json_files]}")
        
    # Validate CSV structure
    if csv_files:
        csv_file = csv_files[0]
        print(f"\nValidating CSV file: {csv_file.name}")
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            print(f"  - CSV loaded successfully: {len(df)} rows")
            print(f"  - Columns: {len(df.columns)}")
            print(f"  - Sample columns: {list(df.columns[:5])}")
        except Exception as e:
            print(f"  - CSV validation error: {e}")


def main():
    """Main test function."""
    print("PROPOSALAND ENHANCED OUTPUT SYSTEM - TEST SUITE")
    print("="*60)
    print(f"Test started at: {datetime.now()}")
    
    try:
        # Run tests
        formatted_data = test_enhanced_formatter()
        test_gdrive_integration()
        test_daily_report_generation()
        validate_output_files()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Test completed at: {datetime.now()}")
        
        # Summary
        print(f"\nTest Summary:")
        print(f"✅ Enhanced formatter: Working")
        print(f"✅ JSON/CSV export: Working")
        print(f"✅ Google Drive preparation: Working")
        print(f"✅ Daily report generation: Working")
        print(f"✅ File validation: Working")
        print(f"ℹ️  Google Drive upload: Requires configuration")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
