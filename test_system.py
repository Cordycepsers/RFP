#!/usr/bin/env python3
"""
Proposaland System Test Script
Tests all components of the system with sample data.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.filters.keyword_filter import KeywordFilter
from src.filters.geographic_filter import GeographicFilter
from src.filters.scoring_engine import ScoringEngine
from src.outputs.excel_generator import ExcelGenerator
from src.outputs.json_generator import JSONGenerator
from reference_number_extractor import ReferenceNumberExtractor


def create_sample_opportunities():
    """Create sample opportunities for testing."""
    sample_opportunities = [
        {
            'title': 'Video Production Services for Health Campaign',
            'description': 'We are seeking a multimedia production company to create educational videos about maternal health. The project includes scriptwriting, filming, animation, and post-production services.',
            'organization': 'UNICEF',
            'source_url': 'https://www.unicef.org/procurement/notices',
            'location': 'Kenya',
            'budget': 75000,
            'currency': 'USD',
            'deadline': datetime.now() + timedelta(days=21),
            'reference_number': 'UNICEF/2024/MEDIA/001',
            'reference_confidence': 0.95,
            'keywords_found': ['video', 'multimedia', 'animation'],
            'extracted_date': datetime.now(),
            'raw_data': {}
        },
        {
            'title': 'Photography and Design Services for Annual Report',
            'description': 'Save the Children requires professional photography and graphic design services for our 2024 annual report. Services include photo shoots, image editing, and layout design.',
            'organization': 'Save the Children',
            'source_url': 'https://www.savethechildren.net/tenders',
            'location': 'Nepal',
            'budget': 25000,
            'currency': 'USD',
            'deadline': datetime.now() + timedelta(days=14),
            'reference_number': 'SC/2024/DESIGN/003',
            'reference_confidence': 0.88,
            'keywords_found': ['photography', 'design', 'visual'],
            'extracted_date': datetime.now(),
            'raw_data': {}
        },
        {
            'title': 'Digital Communication Strategy Development',
            'description': 'World Bank seeks consultancy services for developing a comprehensive digital communication strategy including social media campaigns, website redesign, and multimedia content creation.',
            'organization': 'World Bank',
            'source_url': 'https://projects.worldbank.org/procurement',
            'location': 'Global',
            'budget': 150000,
            'currency': 'USD',
            'deadline': datetime.now() + timedelta(days=45),
            'reference_number': 'WB/2024/COMM/012',
            'reference_confidence': 0.92,
            'keywords_found': ['communication', 'multimedia', 'campaign'],
            'extracted_date': datetime.now(),
            'raw_data': {}
        },
        {
            'title': 'Podcast Production for Development Stories',
            'description': 'UNDP requires podcast production services to create a series about sustainable development success stories. Includes recording, editing, and distribution support.',
            'organization': 'UNDP',
            'source_url': 'https://procurement-notices.undp.org/',
            'location': 'Tanzania',
            'budget': 40000,
            'currency': 'USD',
            'deadline': datetime.now() + timedelta(days=30),
            'reference_number': 'UNDP-TZA-2024-001',
            'reference_confidence': 0.98,
            'keywords_found': ['podcasts', 'media', 'communication'],
            'extracted_date': datetime.now(),
            'raw_data': {}
        },
        {
            'title': 'Infrastructure Development Project - Local Contractors Only',
            'description': 'Road construction project in Mumbai requiring local Indian contractors with specific certifications. International companies not eligible.',
            'organization': 'Government of India',
            'source_url': 'https://example.gov.in/tenders',
            'location': 'Mumbai, India',
            'budget': 500000,
            'currency': 'USD',
            'deadline': datetime.now() + timedelta(days=60),
            'reference_number': 'GOI/2024/INFRA/045',
            'reference_confidence': 0.85,
            'keywords_found': [],  # Should be filtered out
            'extracted_date': datetime.now(),
            'raw_data': {}
        }
    ]
    
    return sample_opportunities


def test_reference_extraction():
    """Test reference number extraction."""
    print("=== Testing Reference Number Extraction ===")
    
    extractor = ReferenceNumberExtractor()
    
    test_texts = [
        "Please submit proposals for RFP/2024/001 by the deadline",
        "UNDP-PAK-001234 is the reference for this procurement",
        "World Bank project P123456 requires multimedia services",
        "Save the Children tender SC/2024/MEDIA/001 for video production"
    ]
    
    for text in test_texts:
        matches = extractor.extract_reference_numbers(text)
        print(f"Text: {text}")
        if matches:
            best_match = matches[0]
            print(f"  Best match: {best_match.reference_number} (confidence: {best_match.confidence:.2f})")
        else:
            print("  No matches found")
        print()


def test_filtering_and_scoring():
    """Test filtering and scoring systems."""
    print("=== Testing Filtering and Scoring ===")
    
    # Load configuration
    with open('config/proposaland_config.json', 'r') as f:
        config = json.load(f)
    
    # Create sample opportunities
    opportunities = create_sample_opportunities()
    
    # Test keyword filtering
    keyword_filter = KeywordFilter(config)
    print("Keyword Filtering Results:")
    for opp in opportunities:
        is_relevant, result = keyword_filter.is_relevant_opportunity(opp['title'], opp['description'])
        print(f"  {opp['title'][:50]}... -> Relevant: {is_relevant}, Score: {result['keyword_score']:.2f}")
    print()
    
    # Test geographic filtering
    geo_filter = GeographicFilter(config)
    print("Geographic Filtering Results:")
    for opp in opportunities:
        is_accepted, result = geo_filter.filter_opportunity(opp['title'], opp['description'], opp['location'])
        print(f"  {opp['location']} -> Accepted: {is_accepted}, Score: {result['geographic_score']:.2f}")
    print()
    
    # Test scoring engine
    scoring_engine = ScoringEngine(config)
    print("Scoring Results:")
    scored_opportunities = scoring_engine.score_opportunities(opportunities)
    for opp in scored_opportunities:
        print(f"  {opp['title'][:50]}... -> Score: {opp['relevance_score']:.2f}, Priority: {opp['priority']}")
    print()
    
    return scored_opportunities


def test_output_generation(opportunities):
    """Test Excel and JSON output generation."""
    print("=== Testing Output Generation ===")
    
    # Load configuration
    with open('config/proposaland_config.json', 'r') as f:
        config = json.load(f)
    
    # Test Excel generation
    excel_generator = ExcelGenerator(config)
    excel_path = excel_generator.generate_tracker(opportunities, "test_tracker.xlsx")
    print(f"Excel tracker generated: {excel_path}")
    
    # Test JSON generation
    json_generator = JSONGenerator(config)
    json_path = json_generator.generate_json_output(opportunities, "test_opportunities.json")
    print(f"JSON output generated: {json_path}")
    
    return excel_path, json_path


def test_email_configuration():
    """Test email configuration (without sending)."""
    print("=== Testing Email Configuration ===")
    
    # Load configuration
    with open('config/proposaland_config.json', 'r') as f:
        config = json.load(f)
    
    # Check email configuration
    email_config = config.get('email', {})
    
    print("Email Configuration:")
    print(f"  SMTP Server: {email_config.get('smtp_server', 'Not configured')}")
    print(f"  SMTP Port: {email_config.get('smtp_port', 'Not configured')}")
    print(f"  Sender Email: {email_config.get('sender_email', 'Not configured')}")
    print(f"  Recipient Email: {email_config.get('recipient_email', 'Not configured')}")
    
    # Check if all required fields are present
    required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'recipient_email']
    missing_fields = [field for field in required_fields if not email_config.get(field)]
    
    if missing_fields:
        print(f"  Missing fields: {', '.join(missing_fields)}")
        print("  Email functionality will not work until these are configured")
    else:
        print("  All required email fields are configured")
    
    print()


def generate_test_report(opportunities, excel_path, json_path):
    """Generate a test report summary."""
    print("=== Test Report Summary ===")
    
    total_opportunities = len(opportunities)
    critical_count = len([opp for opp in opportunities if opp.get('priority') == 'Critical'])
    high_count = len([opp for opp in opportunities if opp.get('priority') == 'High'])
    
    print(f"Total Opportunities Processed: {total_opportunities}")
    print(f"Critical Priority: {critical_count}")
    print(f"High Priority: {high_count}")
    print(f"Average Score: {sum(opp.get('relevance_score', 0) for opp in opportunities) / total_opportunities:.2f}")
    print()
    
    print("Generated Files:")
    print(f"  Excel Tracker: {excel_path}")
    print(f"  JSON Data: {json_path}")
    print()
    
    print("Top Opportunities:")
    sorted_opps = sorted(opportunities, key=lambda x: x.get('relevance_score', 0), reverse=True)
    for i, opp in enumerate(sorted_opps[:3], 1):
        print(f"  {i}. {opp['title'][:60]}...")
        print(f"     Score: {opp.get('relevance_score', 0):.2f}, Priority: {opp.get('priority', 'Unknown')}")
        print(f"     Organization: {opp['organization']}")
        print()


def main():
    """Run complete system test."""
    print("================================================")
    print("    Proposaland System Test")
    print("================================================")
    print()
    
    try:
        # Test 1: Reference number extraction
        test_reference_extraction()
        
        # Test 2: Filtering and scoring
        opportunities = test_filtering_and_scoring()
        
        # Test 3: Output generation
        excel_path, json_path = test_output_generation(opportunities)
        
        # Test 4: Email configuration
        test_email_configuration()
        
        # Test 5: Generate summary report
        generate_test_report(opportunities, excel_path, json_path)
        
        print("================================================")
        print("System test completed successfully!")
        print("All components are working correctly.")
        print("================================================")
        
    except Exception as e:
        print(f"System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

