#!/usr/bin/env python3
"""
Test script for GGGI Advanced Scrapers
Tests both requests-based and Playwright-based implementations
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the scrapers
from advanced_scrapers.gggi_advanced_scraper import GGGIAdvancedScraper
from advanced_scrapers.gggi_playwright_scraper import GGGIPlaywrightScraper

def test_requests_scraper():
    """Test the requests-based scraper"""
    print("\n🧪 Testing Requests-Based GGGI Scraper")
    print("="*50)
    
    try:
        scraper = GGGIAdvancedScraper()
        report = scraper.run_full_scrape()
        
        print("✅ Requests-based scraper completed successfully!")
        print(f"   - Total tenders: {report['summary']['total_tenders']}")
        print(f"   - Media relevant: {report['summary']['media_relevant_count']}")
        print(f"   - Relevance rate: {report['summary']['media_relevance_rate']}")
        
        return report
        
    except Exception as e:
        print(f"❌ Requests-based scraper failed: {e}")
        return None

async def test_playwright_scraper():
    """Test the Playwright-based scraper"""
    print("\n🎭 Testing Playwright-Based GGGI Scraper")
    print("="*50)
    
    try:
        scraper = GGGIPlaywrightScraper()
        report = await scraper.run_full_analysis()
        
        print("✅ Playwright-based scraper completed successfully!")
        print(f"   - Total tenders: {report['summary']['total_tenders']}")
        print(f"   - Media relevant: {report['summary']['media_relevant_count']}")
        print(f"   - Relevance rate: {report['summary']['media_relevance_rate']}")
        
        return report
        
    except Exception as e:
        print(f"❌ Playwright-based scraper failed: {e}")
        return None

def compare_results(requests_report, playwright_report):
    """Compare results from both scrapers"""
    print("\n📊 Comparing Scraper Results")
    print("="*40)
    
    if not requests_report or not playwright_report:
        print("⚠️  Cannot compare - one or both scrapers failed")
        return
    
    req_summary = requests_report['summary']
    pw_summary = playwright_report['summary']
    
    print(f"Requests Scraper:")
    print(f"  - Total: {req_summary['total_tenders']}")
    print(f"  - Media relevant: {req_summary['media_relevant_count']}")
    print(f"  - Rate: {req_summary['media_relevance_rate']}")
    
    print(f"\nPlaywright Scraper:")
    print(f"  - Total: {pw_summary['total_tenders']}")
    print(f"  - Media relevant: {pw_summary['media_relevant_count']}")
    print(f"  - Rate: {pw_summary['media_relevance_rate']}")
    
    # Compare media opportunities
    req_media = requests_report.get('media_opportunities', [])
    pw_media = playwright_report.get('media_opportunities', [])
    
    print(f"\n🎯 Media Opportunities Comparison:")
    print(f"  - Requests found: {len(req_media)}")
    print(f"  - Playwright found: {len(pw_media)}")
    
    # Find common opportunities
    req_titles = {tender.get('title', '').lower() for tender in req_media}
    pw_titles = {tender.get('title', '').lower() for tender in pw_media}
    
    common_titles = req_titles.intersection(pw_titles)
    print(f"  - Common opportunities: {len(common_titles)}")
    
    if common_titles:
        print(f"  - Common titles:")
        for title in list(common_titles)[:3]:
            print(f"    • {title[:50]}...")

def save_comparison_report(requests_report, playwright_report):
    """Save comparison report"""
    comparison = {
        'comparison_date': datetime.now().isoformat(),
        'requests_scraper_results': requests_report,
        'playwright_scraper_results': playwright_report,
        'comparison_summary': {
            'requests_total': requests_report['summary']['total_tenders'] if requests_report else 0,
            'playwright_total': playwright_report['summary']['total_tenders'] if playwright_report else 0,
            'requests_media': requests_report['summary']['media_relevant_count'] if requests_report else 0,
            'playwright_media': playwright_report['summary']['media_relevant_count'] if playwright_report else 0,
        }
    }
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gggi_scrapers_comparison_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Comparison report saved to: {filepath}")

async def main():
    """Main test function"""
    print("🚀 GGGI Advanced Scrapers Test Suite")
    print("="*60)
    
    # Test both scrapers
    requests_report = test_requests_scraper()
    playwright_report = await test_playwright_scraper()
    
    # Compare results
    compare_results(requests_report, playwright_report)
    
    # Save comparison
    save_comparison_report(requests_report, playwright_report)
    
    print("\n🏁 Test suite completed!")
    
    # Return the better result
    if playwright_report and playwright_report['summary']['total_tenders'] > 0:
        print("🏆 Playwright scraper recommended for production use")
        return playwright_report
    elif requests_report:
        print("🏆 Requests scraper available as fallback")
        return requests_report
    else:
        print("⚠️  No successful results")
        return None

if __name__ == "__main__":
    asyncio.run(main())
