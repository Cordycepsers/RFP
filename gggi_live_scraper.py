#!/usr/bin/env python3
"""
GGGI Live Scraper using MCP Playwright Browser
Executes the actual browser commands and processes results
"""

import json
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_scrapers.gggi_mcp_scraper import GGGIMCPScraper

def scrape_gggi_live():
    """
    Live scraping function that uses the MCP Playwright browser
    This function demonstrates how to integrate with browser commands
    """
    
    print("🚀 GGGI Live Scraper with MCP Playwright")
    print("=" * 50)
    
    # Initialize scraper
    scraper = GGGIMCPScraper()
    
    # Step 1: Instructions for browser commands
    print("\n📋 BROWSER COMMANDS TO RUN:")
    print("-" * 30)
    
    browser_steps = [
        {
            "step": 1,
            "command": "mcp_playwright_browser_navigate",
            "params": {"url": "https://in-tendhost.co.uk/gggi/aspx/Tenders/Current"},
            "description": "Navigate to GGGI current tenders page"
        },
        {
            "step": 2,
            "command": "mcp_playwright_browser_snapshot",
            "params": {},
            "description": "Capture snapshot of main tenders page"
        },
        {
            "step": 3,
            "command": "Check for tender View Details buttons",
            "params": {},
            "description": "Look for clickable 'View Details' buttons in the snapshot"
        },
        {
            "step": 4,
            "command": "mcp_playwright_browser_click",
            "params": {"element": "View Details button for first tender", "ref": "<button_ref>"},
            "description": "Click on View Details for detailed info"
        },
        {
            "step": 5,
            "command": "mcp_playwright_browser_snapshot",
            "params": {},
            "description": "Capture detailed tender information"
        },
        {
            "step": 6,
            "command": "mcp_playwright_browser_navigate_back",
            "params": {},
            "description": "Return to main page"
        },
        {
            "step": 7,
            "command": "Check for Next button",
            "params": {},
            "description": "Look for pagination Next button"
        }
    ]
    
    for step in browser_steps:
        print(f"Step {step['step']}: {step['description']}")
        print(f"  Command: {step['command']}")
        if step['params']:
            print(f"  Params: {step['params']}")
        print()
    
    print("🔍 WHAT TO LOOK FOR IN SNAPSHOTS:")
    print("-" * 35)
    print("• Tender titles (usually long descriptive text)")
    print("• 'Deadline For Applications: [date]'")
    print("• 'Procurement No.: [number]'")
    print("• 'Process: RFP/RFQ'")
    print("• 'View Details' buttons with references")
    print("• 'Next' button for pagination")
    print()
    
    print("📊 MEDIA KEYWORDS TO WATCH FOR:")
    print("-" * 32)
    media_keywords = scraper.media_keywords[:10]  # Show first 10
    for keyword in media_keywords:
        print(f"• {keyword}")
    print("• ... and more")
    print()
    
    return scraper

def process_captured_data(scraper, main_snapshots, detail_snapshots=None):
    """
    Process the data captured from browser snapshots
    
    Args:
        scraper: GGGIMCPScraper instance
        main_snapshots: List of snapshot texts from main pages
        detail_snapshots: Optional list of detailed page snapshots
    """
    
    print("🔄 Processing captured data...")
    print("-" * 30)
    
    # Process the scraped data
    tenders = scraper.process_scraped_data(main_snapshots, detail_snapshots)
    
    print(f"✅ Found {len(tenders)} tenders")
    
    # Generate comprehensive report
    report = scraper.generate_report(tenders)
    
    # Print summary
    scraper.print_summary(report)
    
    # Save results
    filepath = scraper.save_results(report)
    
    # Save to data directory as well
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_filepath = os.path.join(data_dir, f"gggi_live_scrape_{timestamp}.json")
    
    with open(data_filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Additional copy saved to: {data_filepath}")
    
    return report

def demo_with_existing_data():
    """
    Demo function using the existing GGGI data we captured earlier
    """
    
    print("🧪 DEMO: Processing with existing GGGI data")
    print("=" * 45)
    
    scraper = GGGIMCPScraper()
    
    # Load existing GGGI data
    data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'data', 'gggi_media_opportunities_links.json')
    
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            existing_data = json.load(f)
        
        # Convert existing data to tender format
        demo_tenders = []
        for opportunity in existing_data.get('media_opportunities', []):
            tender = {
                'title': opportunity.get('title', ''),
                'procurement_number': opportunity.get('procurement_number', ''),
                'deadline_raw': opportunity.get('deadline_formatted', ''),
                'process_type': opportunity.get('process_type', ''),
                'description': opportunity.get('description_summary', ''),
                'detail_url': opportunity.get('detailed_page_url', ''),
                'scraped_at': datetime.now().isoformat(),
                'source': 'GGGI'
            }
            demo_tenders.append(tender)
        
        # Calculate media relevance
        for tender in demo_tenders:
            is_relevant, score, keywords = scraper.calculate_media_relevance(tender)
            tender['media_relevant'] = is_relevant
            tender['media_score'] = score
            tender['media_keywords'] = keywords
        
        # Generate report
        report = scraper.generate_report(demo_tenders)
        
        # Print summary
        scraper.print_summary(report)
        
        print(f"\n✅ Demo completed with {len(demo_tenders)} existing opportunities")
        
        return report
    
    else:
        print("❌ No existing data found for demo")
        return None

def main():
    """Main function"""
    
    print("Choose an option:")
    print("1. Get instructions for live scraping")
    print("2. Run demo with existing data")
    print("3. Process captured snapshots (interactive)")
    
    # For automated execution, run demo
    print("\n🎬 Running demo with existing data...")
    demo_report = demo_with_existing_data()
    
    print("\n" + "="*50)
    print("NEXT STEPS FOR LIVE SCRAPING:")
    print("="*50)
    
    scraper = scrape_gggi_live()
    
    print("📝 TO USE LIVE SCRAPING:")
    print("1. Run the browser commands shown above")
    print("2. Copy the snapshot text output")
    print("3. Call: process_captured_data(scraper, [snapshot1, snapshot2, ...])")
    print("4. The scraper will analyze and generate a complete report")
    
    return scraper

if __name__ == "__main__":
    main()
