#!/usr/bin/env python3

"""
🚀 PROCUREMENT MONITORING SYSTEM - PRODUCTION DEPLOYMENT
=========================================================

This script runs the production procurement monitoring system.
It scrapes 3 working sites and generates comprehensive reports.

Usage:
    python deploy_production.py                    # Full production run
    python deploy_production.py --test-only        # Test run (no file output)
    python deploy_production.py --media-only       # Only media-related opportunities
    python deploy_production.py --days-back 7     # Filter last 7 days instead of 2
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
import csv
from scraper import WebScraper

class ProductionMonitor:
    def __init__(self, config_path="websites.json", days_back=2, media_only=False, test_only=False):
        self.config_path = config_path
        self.days_back = days_back
        self.media_only = media_only
        self.test_only = test_only
        self.results = {}
        self.start_time = datetime.now()
        
        # Production-ready websites (verified working)
        self.production_sites = [
            "UNDP Procurement Notices - Media Projects",
            "ReliefWeb - Jobs & Tenders", 
            "UNGM UN Global Marketplace"
        ]
        
        print(f"🚀 PROCUREMENT MONITORING SYSTEM - PRODUCTION DEPLOYMENT")
        print(f"=" * 65)
        print(f"📅 Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Monitoring period: Last {days_back} days")
        print(f"🎯 Mode: {'Media opportunities only' if media_only else 'All opportunities'}")
        print(f"🔧 Test mode: {'Yes (no files saved)' if test_only else 'No (production run)'}")
        print(f"📊 Sites to monitor: {len(self.production_sites)}")
        
    async def run_production_monitoring(self):
        """Run the complete production monitoring cycle"""
        
        print(f"\n🔍 LOADING CONFIGURATION...")
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False
        
        print(f"✅ Configuration loaded: {len(config['websites'])} websites configured")
        
        # Filter to production-ready sites
        production_configs = []
        for site_name in self.production_sites:
            for website in config['websites']:
                if site_name in website.get('name', ''):
                    production_configs.append(website)
                    break
        
        print(f"✅ Found {len(production_configs)} production-ready configurations")
        
        if len(production_configs) != len(self.production_sites):
            print(f"⚠️ Warning: Expected {len(self.production_sites)} sites, found {len(production_configs)}")
        
        print(f"\n🌐 INITIALIZING SCRAPER...")
        scraper = WebScraper(headless=True)
        
        try:
            await scraper.initialize()
            print(f"✅ Browser initialized successfully")
            
            all_opportunities = []
            
            # Process each production site
            for i, site_config in enumerate(production_configs, 1):
                site_name = site_config['name']
                print(f"\n📍 PROCESSING SITE {i}/{len(production_configs)}: {site_name}")
                print(f"-" * 60)
                
                try:
                    # Run the scraper for this site
                    opportunities = await scraper.scrape_website(site_config)
                    
                    if opportunities:
                        # Filter for recent items if specified
                        if self.days_back:
                            recent_opportunities = []
                            for opp in opportunities:
                                if scraper._is_recently_published(opp, days_back=self.days_back):
                                    recent_opportunities.append(opp)
                            opportunities = recent_opportunities
                        
                        # Filter for media-only if specified
                        if self.media_only:
                            media_opportunities = []
                            for opp in opportunities:
                                if scraper._should_process_project(opp, site_config):
                                    media_opportunities.append(opp)
                            opportunities = media_opportunities
                        
                        all_opportunities.extend(opportunities)
                        
                        print(f"✅ Found {len(opportunities)} relevant opportunities")
                        self.results[site_name] = {
                            'status': 'success',
                            'opportunities': len(opportunities),
                            'sample': opportunities[0]['title'][:50] + "..." if opportunities else "No opportunities"
                        }
                    else:
                        print(f"⚠️ No opportunities found")
                        self.results[site_name] = {
                            'status': 'no_results',
                            'opportunities': 0,
                            'sample': 'No opportunities found'
                        }
                        
                    # Add delay between sites to be respectful
                    if i < len(production_configs):
                        print(f"⏳ Waiting 5 seconds before next site...")
                        await asyncio.sleep(5)
                        
                except Exception as e:
                    print(f"❌ Error processing {site_name}: {str(e)}")
                    self.results[site_name] = {
                        'status': 'error',
                        'opportunities': 0,
                        'sample': f'Error: {str(e)[:50]}...'
                    }
            
            # Generate reports
            await self._generate_reports(all_opportunities)
            
            return True
            
        except Exception as e:
            print(f"❌ Critical error in production monitoring: {e}")
            return False
        finally:
            await scraper.close()
            print(f"\n🔒 Browser closed successfully")
    
    async def _generate_reports(self, opportunities):
        """Generate comprehensive reports of findings"""
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print(f"\n📊 GENERATING PRODUCTION REPORTS...")
        print(f"=" * 50)
        
        # Console summary
        total_opportunities = len(opportunities)
        working_sites = sum(1 for r in self.results.values() if r['status'] == 'success')
        
        print(f"⏱️  Total runtime: {duration.total_seconds():.1f} seconds")
        print(f"🌐 Sites processed: {len(self.results)}")
        print(f"✅ Sites working: {working_sites}/{len(self.results)}")
        print(f"📋 Total opportunities found: {total_opportunities}")
        
        # Site-by-site breakdown
        print(f"\n📈 DETAILED RESULTS:")
        print(f"-" * 30)
        for site_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'error' else "⚠️"
            short_name = site_name.split(' - ')[0]  # Shorten name for display
            print(f"{status_icon} {short_name:15} | {result['opportunities']:3} opportunities | {result['sample']}")
        
        if not self.test_only:
            # Save detailed JSON report
            report_data = {
                'deployment_info': {
                    'timestamp': self.start_time.isoformat(),
                    'duration_seconds': duration.total_seconds(),
                    'days_back': self.days_back,
                    'media_only': self.media_only,
                    'total_opportunities': total_opportunities,
                    'sites_processed': len(self.results),
                    'sites_working': working_sites
                },
                'site_results': self.results,
                'opportunities': opportunities
            }
            
            # Create timestamped filename
            timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
            json_filename = f"procurement_report_{timestamp}.json"
            csv_filename = f"procurement_opportunities_{timestamp}.csv"
            
            # Save JSON report
            with open(json_filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"💾 Detailed report saved: {json_filename}")
            
            # Save CSV for easy analysis
            if opportunities:
                with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=opportunities[0].keys())
                    writer.writeheader()
                    writer.writerows(opportunities)
                print(f"📊 CSV export saved: {csv_filename}")
            
            # Create/update latest symlinks for easy access
            try:
                if os.path.exists('latest_report.json'):
                    os.remove('latest_report.json')
                os.symlink(json_filename, 'latest_report.json')
                
                if opportunities and os.path.exists('latest_opportunities.csv'):
                    os.remove('latest_opportunities.csv')
                if opportunities:
                    os.symlink(csv_filename, 'latest_opportunities.csv')
                    
                print(f"🔗 Latest files linked: latest_report.json, latest_opportunities.csv")
            except:
                pass  # Symlinks might not work on all systems
        
        # Show sample opportunities
        if opportunities:
            print(f"\n🎯 SAMPLE OPPORTUNITIES (showing first 3):")
            print(f"-" * 40)
            for i, opp in enumerate(opportunities[:3], 1):
                title = opp.get('title', 'No title')[:60] + "..." if len(opp.get('title', '')) > 60 else opp.get('title', 'No title')
                org = opp.get('organization', opp.get('office', 'Unknown'))
                deadline = opp.get('deadline', 'No deadline')
                print(f"{i}. {title}")
                print(f"   Organization: {org}")
                print(f"   Deadline: {deadline}")
                print()
        
        print(f"\n🚀 PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!")
        
        if not self.test_only:
            print(f"\n📁 Output files created:")
            print(f"   • {json_filename} - Detailed JSON report")
            if opportunities:
                print(f"   • {csv_filename} - CSV export for analysis")
            print(f"   • latest_report.json - Latest report (symlink)")
            if opportunities:
                print(f"   • latest_opportunities.csv - Latest opportunities (symlink)")

async def main():
    """Main function with command line argument handling"""
    
    # Parse command line arguments
    days_back = 2
    media_only = '--media-only' in sys.argv
    test_only = '--test-only' in sys.argv
    
    # Handle days-back argument
    if '--days-back' in sys.argv:
        try:
            idx = sys.argv.index('--days-back')
            days_back = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("❌ Error: --days-back requires a number (e.g., --days-back 7)")
            sys.exit(1)
    
    # Show help
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    # Run production monitoring
    monitor = ProductionMonitor(
        days_back=days_back,
        media_only=media_only,
        test_only=test_only
    )
    
    success = await monitor.run_production_monitoring()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
