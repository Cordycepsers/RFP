#!/usr/bin/env python3
"""
GGGI Advanced Scraper using MCP Playwright Browser
Uses the existing MCP Playwright server for reliable scraping
Portal: https://in-tendhost.co.uk/gggi
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import os
import sys

class GGGIMCPScraper:
    def __init__(self):
        self.base_url = "https://in-tendhost.co.uk/gggi"
        self.current_tenders_url = f"{self.base_url}/aspx/Tenders/Current"
        
        # Media-related keywords for filtering - FOCUSED on visual/audiovisual/communication work
        self.media_keywords = [
            'video', 'photo', 'film', 'multimedia', 'design', 'visual',
            'campaign', 'podcasts', 'virtual event', 'media', 'animation', 
            'animated video', 'promotion', 'communication', 'audiovisual',
            'photography', 'filming', 'documentary', 'broadcasting',
            'graphic design', 'content creation', 'creative', 'advertising',
            'marketing', 'publicity', 'brand', 'logo', 'illustration',
            'editing', 'production', 'post-production', 'motion graphics',
            'social media', 'digital content', 'web design', 'interactive',
            'presentation', 'conference materials', 'event production'
        ]
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'gggi_mcp_scraper.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def parse_tender_from_snapshot(self, snapshot_text: str) -> List[Dict]:
        """Parse tender information from browser snapshot"""
        tenders = []
        
        # Split snapshot into logical sections
        lines = snapshot_text.split('\n')
        current_tender = {}
        in_tender_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for tender titles (usually longer descriptive text)
            if len(line) > 30 and not line.startswith('-') and not line.startswith('*'):
                # Check if this looks like a tender title
                if any(keyword in line.lower() for keyword in ['consultancy', 'provision', 'development', 'assessment']):
                    if current_tender and current_tender.get('title'):
                        tenders.append(current_tender)
                    
                    current_tender = {
                        'title': line,
                        'scraped_at': datetime.now().isoformat(),
                        'source': 'GGGI'
                    }
                    in_tender_section = True
            
            # Look for deadline information
            if 'deadline for applications' in line.lower():
                # Look for the next line that contains a date
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if re.search(r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', next_line, re.IGNORECASE):
                        current_tender['deadline_raw'] = next_line
                        break
            
            # Look for procurement numbers
            if re.search(r'procurement no\.?:?\s*["\']?(\d{9,})["\']?', line, re.IGNORECASE):
                match = re.search(r'procurement no\.?:?\s*["\']?(\d{9,})["\']?', line, re.IGNORECASE)
                if match:
                    current_tender['procurement_number'] = match.group(1)
            
            # Look for process type
            if 'process' in line.lower() and ('rfp' in line.lower() or 'rfq' in line.lower()):
                if 'rfp' in line.lower():
                    current_tender['process_type'] = 'RFP'
                elif 'rfq' in line.lower():
                    current_tender['process_type'] = 'RFQ'
        
        # Add the last tender if it exists
        if current_tender and current_tender.get('title'):
            tenders.append(current_tender)
        
        return tenders

    def parse_detailed_info_from_snapshot(self, snapshot_text: str, tender_info: Dict) -> Dict:
        """Parse detailed information from tender detail page snapshot"""
        lines = snapshot_text.split('\n')
        
        # Look for description
        description_lines = []
        in_description = False
        
        for line in lines:
            line = line.strip()
            
            # Start of description section
            if 'description' in line.lower() and ':' in line:
                in_description = True
                # Check if description continues on same line
                desc_match = re.search(r'description\s*:\s*(.+)', line, re.IGNORECASE)
                if desc_match:
                    description_lines.append(desc_match.group(1))
                continue
            
            # If we're in description and line has substantial content
            if in_description and len(line) > 20:
                # Stop if we hit another field
                if any(field in line.lower() for field in ['procurement method', 'quality', 'number of bids']):
                    break
                description_lines.append(line)
            
            # Look for estimated value
            if 'usd' in line.lower() and '$' in line:
                value_match = re.search(r'\$\s*([\d,]+\.?\d*)', line)
                if value_match:
                    tender_info['estimated_value'] = f"${value_match.group(1)}"
        
        # Combine description lines
        if description_lines:
            tender_info['description'] = ' '.join(description_lines)
            tender_info['description_length'] = len(tender_info['description'])
        
        return tender_info

    def calculate_media_relevance(self, tender_info: Dict) -> Tuple[bool, float, List[str]]:
        """Calculate media relevance score and identify matching keywords"""
        text_to_analyze = " ".join([
            tender_info.get('title', ''),
            tender_info.get('description', '')
        ]).lower()
        
        found_keywords = []
        total_matches = 0
        
        import re
        for keyword in self.media_keywords:
            # Use word boundaries to avoid false positives like "ui" in "Guinea"
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_to_analyze):
                found_keywords.append(keyword)
                total_matches += len(re.findall(pattern, text_to_analyze))
        
        if not found_keywords:
            return False, 0.0, []
        
        # Calculate relevance score
        base_score = (len(found_keywords) / len(self.media_keywords)) * 60
        frequency_bonus = min(total_matches * 5, 40)
        
        high_value_keywords = [
            'video', 'photo', 'film', 'multimedia', 'design', 'visual',
            'campaign', 'podcasts', 'virtual event', 'media', 'animation', 
            'animated video', 'promotion', 'communication', 'audiovisual'
        ]
        
        high_value_bonus = sum(10 for kw in found_keywords if kw in high_value_keywords)
        high_value_bonus = min(high_value_bonus, 30)
        
        final_score = min(base_score + frequency_bonus + high_value_bonus, 100.0)
        is_relevant = final_score >= 15.0
        
        return is_relevant, final_score, found_keywords

    def scrape_using_mcp_browser(self) -> List[Dict]:
        """
        Main scraping function that uses MCP Playwright browser commands
        This function provides the structure - actual browser commands should be run separately
        """
        self.logger.info("GGGI MCP Scraper Instructions")
        self.logger.info("=" * 50)
        
        instructions = [
            "1. Use mcp_playwright_browser_navigate to go to: https://in-tendhost.co.uk/gggi/aspx/Tenders/Current",
            "2. Use mcp_playwright_browser_snapshot to capture the current tenders page",
            "3. For each tender found, use mcp_playwright_browser_click on 'View Details' button",
            "4. Use mcp_playwright_browser_snapshot to capture detailed tender information",
            "5. Use mcp_playwright_browser_navigate_back to return to main page",
            "6. If there's a 'Next' button, click it and repeat for additional pages"
        ]
        
        for instruction in instructions:
            print(instruction)
        
        print("\nThis scraper is designed to work with the MCP Playwright browser.")
        print("Please run the browser commands manually and then use process_scraped_data() method.")
        
        return []

    def process_scraped_data(self, snapshots: List[str], detail_snapshots: List[str] = None) -> List[Dict]:
        """
        Process the scraped data from browser snapshots
        
        Args:
            snapshots: List of snapshot texts from main tender pages
            detail_snapshots: List of snapshot texts from detail pages
        """
        all_tenders = []
        
        # Process main page snapshots
        for snapshot in snapshots:
            tenders = self.parse_tender_from_snapshot(snapshot)
            all_tenders.extend(tenders)
        
        # Enhance with detailed information if available
        if detail_snapshots:
            for i, detail_snapshot in enumerate(detail_snapshots):
                if i < len(all_tenders):
                    all_tenders[i] = self.parse_detailed_info_from_snapshot(
                        detail_snapshot, all_tenders[i]
                    )
        
        # Calculate media relevance for all tenders
        for tender in all_tenders:
            is_relevant, score, keywords = self.calculate_media_relevance(tender)
            tender['media_relevant'] = is_relevant
            tender['media_score'] = score
            tender['media_keywords'] = keywords
            tender['portal_url'] = self.current_tenders_url
        
        # Sort by media relevance score
        all_tenders.sort(key=lambda x: x.get('media_score', 0), reverse=True)
        
        return all_tenders

    def generate_report(self, tenders: List[Dict]) -> Dict:
        """Generate comprehensive report"""
        media_relevant = [t for t in tenders if t.get('media_score', 0) >= 15.0]
        
        report = {
            'summary': {
                'total_tenders': len(tenders),
                'media_relevant_count': len(media_relevant),
                'media_relevance_rate': f"{(len(media_relevant) / len(tenders) * 100):.1f}%" if tenders else "0%",
                'scraped_at': datetime.now().isoformat(),
                'portal': 'GGGI - Global Green Growth Institute',
                'portal_url': self.current_tenders_url,
                'scraper_type': 'MCP Playwright Browser'
            },
            'media_opportunities': media_relevant,
            'all_tenders': tenders,
            'keyword_analysis': self._analyze_keywords(media_relevant),
            'deadline_analysis': self._analyze_deadlines(media_relevant)
        }
        
        return report

    def _analyze_keywords(self, tenders: List[Dict]) -> Dict:
        """Analyze keyword frequency and patterns"""
        keyword_freq = {}
        
        for tender in tenders:
            for keyword in tender.get('media_keywords', []):
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        return {
            'frequency': dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)),
            'total_unique_keywords': len(keyword_freq),
            'most_common': list(dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)).keys())[:10]
        }

    def _analyze_deadlines(self, tenders: List[Dict]) -> Dict:
        """Analyze deadline patterns"""
        urgent_count = 0
        upcoming_count = 0
        
        for tender in tenders:
            deadline_text = tender.get('deadline_raw', '').lower()
            if deadline_text:
                if 'august' in deadline_text:
                    urgent_count += 1
                elif 'september' in deadline_text:
                    upcoming_count += 1
        
        return {
            'urgent_deadlines': urgent_count,
            'upcoming_deadlines': upcoming_count,
            'total_with_deadlines': len([t for t in tenders if t.get('deadline_raw')])
        }

    def save_results(self, report: Dict, output_dir: str = None) -> str:
        """Save results to JSON file"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gggi_mcp_opportunities_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Results saved to: {filepath}")
        return filepath

    def print_summary(self, report: Dict):
        """Print detailed summary"""
        summary = report['summary']
        media_ops = report['media_opportunities']
        
        print("\n" + "="*70)
        print("GGGI MCP PLAYWRIGHT SCRAPER RESULTS")
        print("="*70)
        print(f"Portal: {summary['portal']}")
        print(f"Scraper: {summary['scraper_type']}")
        print(f"Total Tenders: {summary['total_tenders']}")
        print(f"Media-Relevant: {summary['media_relevant_count']}")
        print(f"Relevance Rate: {summary['media_relevance_rate']}")
        print(f"Scraped At: {summary['scraped_at']}")
        
        if media_ops:
            print(f"\n🎯 TOP MEDIA OPPORTUNITIES:")
            print("-" * 50)
            
            for i, tender in enumerate(media_ops[:5], 1):
                print(f"\n{i}. {tender.get('title', 'N/A')[:60]}...")
                print(f"   📊 Score: {tender.get('media_score', 0):.1f}/100")
                print(f"   📅 Deadline: {tender.get('deadline_raw', 'N/A')}")
                print(f"   🔗 ID: {tender.get('procurement_number', 'N/A')}")
                print(f"   🏷️  Keywords: {', '.join(tender.get('media_keywords', [])[:5])}")
        
        print("\n" + "="*70)

    def create_browser_commands(self) -> List[str]:
        """Generate list of MCP browser commands to run"""
        commands = [
            f"mcp_playwright_browser_navigate(url='{self.current_tenders_url}')",
            "mcp_playwright_browser_snapshot()",
            "# For each tender, click View Details and capture snapshot:",
            "# mcp_playwright_browser_click(element='View Details button', ref='<button_ref>')",
            "# mcp_playwright_browser_snapshot()",
            "# mcp_playwright_browser_navigate_back()",
            "# Check for Next button and repeat if needed:",
            "# mcp_playwright_browser_click(element='Next button', ref='<next_button_ref>')"
        ]
        
        return commands


def create_interactive_scraper():
    """Create an interactive scraper that guides through the process"""
    scraper = GGGIMCPScraper()
    
    print("🚀 GGGI MCP Playwright Scraper")
    print("=" * 40)
    print("This scraper works with the MCP Playwright browser.")
    print("Follow these steps:")
    print()
    
    commands = scraper.create_browser_commands()
    for i, command in enumerate(commands, 1):
        print(f"{i}. {command}")
    
    print()
    print("After running the browser commands, use:")
    print("scraper.process_scraped_data(snapshots=[...]) to process the data")
    
    return scraper


def example_usage():
    """Example of how to use the scraper with captured snapshots"""
    scraper = GGGIMCPScraper()
    
    # Example snapshots (these would come from actual browser captures)
    example_snapshots = [
        """
        Example snapshot content with tender information:
        - Consultancy for Scoping and Feasibility Study of Papua New Guinea's Green Catalogue
        - Deadline For Applications: 18 September 2025
        - Procurement No.: 100013575
        - Process: RFP
        """
    ]
    
    # Process the data
    tenders = scraper.process_scraped_data(example_snapshots)
    
    # Generate report
    report = scraper.generate_report(tenders)
    
    # Print summary
    scraper.print_summary(report)
    
    # Save results
    scraper.save_results(report)
    
    return report


if __name__ == "__main__":
    # Create interactive scraper
    scraper = create_interactive_scraper()
    
    # Show example usage
    print("\n" + "="*40)
    print("EXAMPLE USAGE:")
    print("="*40)
    example_usage()
