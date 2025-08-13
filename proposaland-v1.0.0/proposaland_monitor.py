#!/usr/bin/env python3
"""
Proposaland Opportunity Monitoring System
Main script for automated daily monitoring of development organization opportunities.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.base_scraper import OpportunityData
from scrapers.devex_scraper import DevexScraper
from scrapers.undp_scraper import UNDPScraper


class ProposalandMonitor:
    """Main monitoring system for opportunity discovery."""
    
    def __init__(self, config_path: str = "config/proposaland_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.scrapers = {}
        self.opportunities = []
        self.setup_logging()
        self.initialize_scrapers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"proposaland_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logger.add(
            log_file,
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        logger.info("Proposaland monitoring system started")
    
    def initialize_scrapers(self):
        """Initialize all website scrapers."""
        logger.info("Initializing scrapers for all target websites")
        
        # Get all website configurations
        all_websites = []
        for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
            websites = self.config.get('target_websites', {}).get(priority_group, [])
            all_websites.extend(websites)
        
        # Initialize scrapers for each website
        for website in all_websites:
            website_type = website.get('type', 'generic')
            
            try:
                if website_type == 'devex':
                    scraper = DevexScraper(self.config, website)
                elif website_type == 'undp':
                    scraper = UNDPScraper(self.config, website)
                else:
                    # For now, use generic scraper for other types
                    scraper = self._create_generic_scraper(website)
                
                self.scrapers[website['name']] = scraper
                logger.info(f"Initialized scraper for {website['name']}")
                
            except Exception as e:
                logger.error(f"Failed to initialize scraper for {website['name']}: {e}")
    
    def _create_generic_scraper(self, website_config):
        """Create a generic scraper for websites without specific implementations."""
        # For now, return a basic scraper that can handle simple cases
        from scrapers.base_scraper import BaseScraper
        
        class GenericScraper(BaseScraper):
            def scrape_opportunities(self) -> List[OpportunityData]:
                opportunities = []
                try:
                    soup = self.get_page(self.website_config['url'])
                    if soup:
                        # Basic extraction logic
                        text_content = soup.get_text()
                        keywords_found = self.extract_keywords(text_content)
                        
                        if keywords_found:
                            opportunity = OpportunityData()
                            opportunity.title = f"Opportunity from {self.website_config['name']}"
                            opportunity.organization = self.website_config['name']
                            opportunity.source_url = self.website_config['url']
                            opportunity.keywords_found = keywords_found
                            opportunity.description = "Generic opportunity detected"
                            opportunities.append(opportunity)
                            
                except Exception as e:
                    logger.warning(f"Generic scraper error for {self.website_config['name']}: {e}")
                
                return opportunities
        
        return GenericScraper(self.config, website_config)
    
    def run_monitoring(self) -> List[OpportunityData]:
        """Run the complete monitoring process."""
        logger.info("Starting opportunity monitoring process")
        all_opportunities = []
        
        # Run all scrapers
        for name, scraper in self.scrapers.items():
            try:
                logger.info(f"Running scraper for {name}")
                opportunities = scraper.scrape_opportunities()
                all_opportunities.extend(opportunities)
                logger.info(f"Found {len(opportunities)} opportunities from {name}")
                
            except Exception as e:
                logger.error(f"Error running scraper for {name}: {e}")
                continue
        
        logger.info(f"Total opportunities found: {len(all_opportunities)}")
        self.opportunities = all_opportunities
        return all_opportunities
    
    def filter_opportunities(self, opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Apply additional filtering to opportunities."""
        filtered = []
        
        for opp in opportunities:
            # Check geographic exclusions
            excluded_countries = self.config.get('geographic_filters', {}).get('excluded_countries', [])
            if any(country.lower() in opp.location.lower() for country in excluded_countries):
                continue
            
            # Check for exclusion keywords
            all_text = f"{opp.title} {opp.description}".lower()
            exclusions = self.config.get('keywords', {}).get('exclusions', [])
            if any(exclusion.lower() in all_text for exclusion in exclusions):
                continue
            
            # Check budget range if available
            if opp.budget:
                min_budget = self.config.get('budget_filters', {}).get('min_budget', 0)
                max_budget = self.config.get('budget_filters', {}).get('max_budget', float('inf'))
                if not (min_budget <= opp.budget <= max_budget):
                    continue
            
            # Check deadline if available
            if opp.deadline:
                min_days = self.config.get('deadline_filters', {}).get('minimum_days', 0)
                days_until_deadline = (opp.deadline - datetime.now()).days
                if days_until_deadline < min_days:
                    continue
            
            filtered.append(opp)
        
        logger.info(f"Filtered to {len(filtered)} relevant opportunities")
        return filtered
    
    def score_opportunities(self, opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Score opportunities based on relevance criteria."""
        weights = self.config.get('scoring_weights', {})
        
        for opp in opportunities:
            score = 0.0
            
            # Keyword match score
            keyword_score = len(opp.keywords_found) / len(self.config.get('keywords', {}).get('primary', []))
            score += keyword_score * weights.get('keyword_match', 0.25)
            
            # Budget range score
            if opp.budget:
                min_budget = self.config.get('budget_filters', {}).get('min_budget', 5000)
                max_budget = self.config.get('budget_filters', {}).get('max_budget', 500000)
                if min_budget <= opp.budget <= max_budget:
                    budget_score = 1.0 - abs(opp.budget - (min_budget + max_budget) / 2) / (max_budget - min_budget)
                    score += budget_score * weights.get('budget_range', 0.20)
            
            # Deadline urgency score
            if opp.deadline:
                days_until = (opp.deadline - datetime.now()).days
                if days_until > 0:
                    urgency_score = max(0, 1.0 - days_until / 365)  # More urgent = higher score
                    score += urgency_score * weights.get('deadline_urgency', 0.15)
            
            # Source priority score
            source_priority = 0.5  # Default
            for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
                websites = self.config.get('target_websites', {}).get(priority_group, [])
                for website in websites:
                    if website['name'] == opp.organization:
                        source_priority = website.get('priority', 0.5)
                        break
            score += source_priority * weights.get('source_priority', 0.15)
            
            # Reference number bonus
            if opp.reference_number:
                score += weights.get('reference_number_bonus', 0.05)
            
            # Store score in opportunity
            opp.raw_data['relevance_score'] = min(1.0, score)
        
        # Sort by score
        opportunities.sort(key=lambda x: x.raw_data.get('relevance_score', 0), reverse=True)
        
        return opportunities
    
    def classify_priorities(self, opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Classify opportunities into priority levels."""
        thresholds = self.config.get('priority_thresholds', {})
        
        for opp in opportunities:
            score = opp.raw_data.get('relevance_score', 0)
            
            if score >= thresholds.get('critical', 0.8):
                opp.raw_data['priority'] = 'Critical'
            elif score >= thresholds.get('high', 0.6):
                opp.raw_data['priority'] = 'High'
            elif score >= thresholds.get('medium', 0.4):
                opp.raw_data['priority'] = 'Medium'
            else:
                opp.raw_data['priority'] = 'Low'
        
        return opportunities
    
    def save_results(self, opportunities: List[OpportunityData]):
        """Save results to JSON and prepare for Excel generation."""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON results
        date_str = datetime.now().strftime('%Y-%m-%d')
        json_filename = self.config.get('output_settings', {}).get('json_filename', 'proposaland_opportunities_{date}.json')
        json_filename = json_filename.format(date=date_str)
        json_path = output_dir / json_filename
        
        # Convert opportunities to dictionaries
        opportunities_data = [opp.to_dict() for opp in opportunities]
        
        with open(json_path, 'w') as f:
            json.dump({
                'generated_date': datetime.now().isoformat(),
                'total_opportunities': len(opportunities),
                'opportunities': opportunities_data
            }, f, indent=2, default=str)
        
        logger.info(f"Saved {len(opportunities)} opportunities to {json_path}")
        
        return json_path
    
    def generate_summary_report(self, opportunities: List[OpportunityData]) -> Dict[str, Any]:
        """Generate summary report for email notification."""
        priority_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        source_counts = {}
        keyword_counts = {}
        
        for opp in opportunities:
            # Count by priority
            priority = opp.raw_data.get('priority', 'Low')
            priority_counts[priority] += 1
            
            # Count by source
            source = opp.organization
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # Count keywords
            for keyword in opp.keywords_found:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Get top opportunities
        top_count = self.config.get('output_settings', {}).get('top_opportunities_count', 5)
        top_opportunities = opportunities[:top_count]
        
        summary = {
            'total_opportunities': len(opportunities),
            'priority_breakdown': priority_counts,
            'source_performance': source_counts,
            'top_keywords': dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'top_opportunities': [
                {
                    'title': opp.title,
                    'organization': opp.organization,
                    'priority': opp.raw_data.get('priority', 'Low'),
                    'score': opp.raw_data.get('relevance_score', 0),
                    'reference_number': opp.reference_number,
                    'deadline': opp.deadline.strftime('%Y-%m-%d') if opp.deadline else 'Not specified',
                    'source_url': opp.source_url
                }
                for opp in top_opportunities
            ]
        }
        
        return summary


def main():
    """Main entry point for the monitoring system."""
    try:
        # Initialize monitor
        monitor = ProposalandMonitor()
        
        # Run monitoring
        opportunities = monitor.run_monitoring()
        
        if not opportunities:
            logger.warning("No opportunities found")
            return
        
        # Filter opportunities
        filtered_opportunities = monitor.filter_opportunities(opportunities)
        
        # Score and classify opportunities
        scored_opportunities = monitor.score_opportunities(filtered_opportunities)
        classified_opportunities = monitor.classify_priorities(scored_opportunities)
        
        # Save results
        json_path = monitor.save_results(classified_opportunities)
        
        # Generate summary
        summary = monitor.generate_summary_report(classified_opportunities)
        
        logger.info("Monitoring process completed successfully")
        logger.info(f"Summary: {summary['total_opportunities']} total, "
                   f"{summary['priority_breakdown']['Critical']} critical, "
                   f"{summary['priority_breakdown']['High']} high priority")
        
        return classified_opportunities, summary
        
    except Exception as e:
        logger.error(f"Fatal error in monitoring process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

