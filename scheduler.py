#!/usr/bin/env python3
"""
Proposaland Daily Scheduler
Automated scheduling system for daily opportunity monitoring at 9 AM.
"""

import schedule
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import subprocess
import json
from typing import Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from proposaland_monitor import ProposalandMonitor
from src.outputs.excel_generator import ExcelGenerator
from src.outputs.json_generator import JSONGenerator
from src.notifications.email_notifier import EmailNotifier


class ProposalandScheduler:
    """Daily scheduler for automated opportunity monitoring."""
    
    def __init__(self, config_path: str = "config/proposaland_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.setup_logging()
        
        # Initialize components
        self.monitor = ProposalandMonitor(config_path)
        self.excel_generator = ExcelGenerator(self.config)
        self.json_generator = JSONGenerator(self.config)
        self.email_notifier = EmailNotifier(self.config)
        
        # Scheduling configuration
        self.daily_time = self.config.get('scheduler', {}).get('daily_time', '09:00')
        self.timezone = self.config.get('scheduler', {}).get('timezone', 'UTC')
        self.max_retries = self.config.get('scheduler', {}).get('max_retries', 3)
        self.retry_delay = self.config.get('scheduler', {}).get('retry_delay_minutes', 30)
        
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
        """Setup logging for scheduler."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Scheduler-specific log file
        scheduler_log = log_dir / f"scheduler_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logger.add(
            scheduler_log,
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | SCHEDULER | {level} | {message}"
        )
        
        logger.info("Proposaland scheduler initialized")
    
    def run_daily_monitoring(self):
        """Execute the complete daily monitoring workflow."""
        start_time = datetime.now()
        logger.info("Starting daily monitoring workflow")
        
        try:
            # Step 1: Run monitoring
            logger.info("Step 1: Running opportunity monitoring")
            opportunities = self.monitor.run_monitoring()

            if not opportunities:
                logger.warning("No opportunities found - sending empty report")
                self._send_empty_report()
                return

            # Step 2: Filter and score opportunities
            logger.info("Step 2: Filtering and scoring opportunities")
            filtered_opportunities = self.monitor.filter_opportunities(opportunities)
            scored_opportunities = self.monitor.score_opportunities(filtered_opportunities)
            classified_opportunities = self.monitor.classify_priorities(scored_opportunities)

            # Convert OpportunityData objects to dicts for output and notification modules
            classified_opportunities_dicts = [opp.__dict__ for opp in classified_opportunities]

            # Step 3: Generate outputs
            logger.info("Step 3: Generating Excel and JSON outputs")
            excel_path = self.excel_generator.generate_tracker(classified_opportunities_dicts)
            json_path = self.json_generator.generate_json_output(classified_opportunities_dicts)

            # Step 4: Generate summary
            logger.info("Step 4: Generating summary report")
            summary = self.monitor.generate_summary_report(classified_opportunities)

            # Step 5: Send email notifications
            logger.info("Step 5: Sending email notifications")
            email_success = self.email_notifier.send_daily_report(
                classified_opportunities_dicts, summary, excel_path, json_path
            )

            # Step 6: Send urgent alerts if needed
            critical_opportunities = [opp for opp in classified_opportunities_dicts if opp.get('priority') == 'Critical']
            if critical_opportunities:
                logger.info(f"Step 6: Sending urgent alert for {len(critical_opportunities)} critical opportunities")
                self.email_notifier.send_urgent_alert(critical_opportunities)

            # Log completion
            duration = datetime.now() - start_time
            logger.info(f"Daily monitoring completed successfully in {duration}")
            logger.info(f"Results: {len(classified_opportunities)} opportunities, "
                       f"{len(critical_opportunities)} critical, "
                       f"email sent: {email_success}")
            
            # Save execution summary
            self._save_execution_summary(classified_opportunities, summary, duration, True)
            
        except Exception as e:
            duration = datetime.now() - start_time
            logger.error(f"Daily monitoring failed after {duration}: {e}")
            self._save_execution_summary([], {}, duration, False, str(e))
            
            # Send error notification
            self._send_error_notification(str(e))
            raise
    
    def run_with_retry(self):
        """Run daily monitoring with retry logic."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Daily monitoring attempt {attempt}/{self.max_retries}")
                self.run_daily_monitoring()
                return  # Success, exit retry loop
                
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                
                if attempt < self.max_retries:
                    wait_minutes = self.retry_delay * attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_minutes} minutes...")
                    time.sleep(wait_minutes * 60)
                else:
                    logger.error("All retry attempts failed")
                    raise
    
    def start_scheduler(self):
        """Start the daily, weekly, and monthly scheduler."""
        logger.info(f"Starting Proposaland scheduler - daily execution at {self.daily_time}")
        # Schedule daily monitoring
        schedule.every().day.at(self.daily_time).do(self.run_with_retry)
        # Schedule weekly maintenance (Sundays at 2 AM)
        schedule.every().sunday.at("02:00").do(self.run_weekly_maintenance)
        # Schedule monthly cleanup workaround: check daily at 03:00 if it's the first day of the month
        schedule.every().day.at("03:00").do(self.run_monthly_cleanup_if_first_day)
    def run_monthly_cleanup_if_first_day(self):
        """Run monthly cleanup only on the first day of the month."""
        if datetime.now().day == 1:
            self.run_monthly_cleanup()

    def run(self):
        logger.info("Scheduler started - waiting for scheduled tasks...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before continuing
    
    def run_weekly_maintenance(self):
        """Run weekly maintenance tasks."""
        logger.info("Starting weekly maintenance")
        
        try:
            # Clean old log files (keep last 30 days)
            self._cleanup_old_logs()
            
            # Clean old output files (keep last 60 days)
            self._cleanup_old_outputs()
            
            # Generate weekly summary report
            self._generate_weekly_summary()
            
            # Test email configuration
            self.email_notifier.test_email_configuration()
            
            logger.info("Weekly maintenance completed")
            
        except Exception as e:
            logger.error(f"Weekly maintenance failed: {e}")
    
    def run_monthly_cleanup(self):
        """Run monthly cleanup tasks."""
        logger.info("Starting monthly cleanup")
        
        try:
            # Archive old data
            self._archive_old_data()
            
            # Generate monthly analytics
            self._generate_monthly_analytics()
            
            # System health check
            self._run_system_health_check()
            
            logger.info("Monthly cleanup completed")
            
        except Exception as e:
            logger.error(f"Monthly cleanup failed: {e}")
    
    def _send_empty_report(self):
        """Send notification when no opportunities are found."""
        try:
            # Create empty Excel and JSON files
            empty_opportunities = []
            excel_path = self.excel_generator.generate_tracker(empty_opportunities)
            json_path = self.json_generator.generate_json_output(empty_opportunities)
            
            # Generate empty summary
            summary = {
                'total_opportunities': 0,
                'priority_breakdown': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0},
                'average_score': 0.0,
                'top_keywords': [],
                'top_organizations': []
            }
            
            # Send email
            self.email_notifier.send_daily_report(empty_opportunities, summary, excel_path, json_path)
            
        except Exception as e:
            logger.error(f"Error sending empty report: {e}")
    
    def _send_error_notification(self, error_message: str):
        """Send error notification email."""
        try:
            # Create simple error email
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message['Subject'] = "🚨 Proposaland Monitoring System Error"
            message['From'] = self.email_notifier.sender_email
            message['To'] = self.email_notifier.recipient_email
            
            error_content = f"""
            Proposaland Monitoring System Error Report
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Error: {error_message}
            
            The daily monitoring process has failed. Please check the system logs and resolve the issue.
            
            System will attempt to retry according to the configured retry policy.
            """
            
            text_part = MIMEText(error_content, 'plain')
            message.attach(text_part)
            
            # Send error email
            self.email_notifier._send_email(message)
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    def _save_execution_summary(self, opportunities, summary, duration, success, error_message=None):
        """Save execution summary for monitoring and analytics."""
        try:
            summary_dir = Path("logs/execution_summaries")
            summary_dir.mkdir(parents=True, exist_ok=True)
            
            execution_summary = {
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'duration_seconds': duration.total_seconds(),
                'opportunities_found': len(opportunities),
                'summary': summary,
                'error_message': error_message
            }
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            summary_file = summary_dir / f"execution_summary_{date_str}.json"
            
            with open(summary_file, 'w') as f:
                json.dump(execution_summary, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error saving execution summary: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files."""
        try:
            log_dir = Path("logs")
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
    
    def _cleanup_old_outputs(self):
        """Clean up old output files."""
        try:
            output_dir = Path("output")
            cutoff_date = datetime.now() - timedelta(days=60)
            
            for output_file in output_dir.glob("*"):
                if output_file.stat().st_mtime < cutoff_date.timestamp():
                    output_file.unlink()
                    logger.info(f"Deleted old output file: {output_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up outputs: {e}")
    
    def _generate_weekly_summary(self):
        """Generate weekly summary report."""
        try:
            # This would analyze the past week's execution summaries
            logger.info("Weekly summary generation not yet implemented")
            
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
    
    def _archive_old_data(self):
        """Archive old data files."""
        try:
            # This would archive data older than a certain threshold
            logger.info("Data archiving not yet implemented")
            
        except Exception as e:
            logger.error(f"Error archiving data: {e}")
    
    def _generate_monthly_analytics(self):
        """Generate monthly analytics report."""
        try:
            # This would generate comprehensive monthly analytics
            logger.info("Monthly analytics generation not yet implemented")
            
        except Exception as e:
            logger.error(f"Error generating monthly analytics: {e}")
    
    def _run_system_health_check(self):
        """Run system health check."""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'disk_space': self._check_disk_space(),
                'log_files': self._check_log_files(),
                'config_files': self._check_config_files(),
                'email_config': self.email_notifier.test_email_configuration()
            }
            
            logger.info(f"System health check completed: {health_status}")
            
        except Exception as e:
            logger.error(f"Error running health check: {e}")
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            
            return {
                'total_gb': total // (1024**3),
                'used_gb': used // (1024**3),
                'free_gb': free // (1024**3),
                'usage_percent': (used / total) * 100
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_log_files(self) -> Dict[str, Any]:
        """Check log file status."""
        try:
            log_dir = Path("logs")
            log_files = list(log_dir.glob("*.log"))
            
            return {
                'log_files_count': len(log_files),
                'latest_log': max(log_files, key=lambda f: f.stat().st_mtime).name if log_files else None,
                'total_size_mb': sum(f.stat().st_size for f in log_files) // (1024**2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_config_files(self) -> Dict[str, Any]:
        """Check configuration file status."""
        try:
            config_file = Path(self.config_path)
            
            return {
                'config_exists': config_file.exists(),
                'config_size': config_file.stat().st_size if config_file.exists() else 0,
                'last_modified': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat() if config_file.exists() else None
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Proposaland Daily Scheduler')
    parser.add_argument('--config', default='config/proposaland_config.json', 
                       help='Path to configuration file')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run monitoring once and exit (for testing)')
    parser.add_argument('--test-email', action='store_true', 
                       help='Test email configuration and exit')
    
    args = parser.parse_args()
    
    try:
        scheduler = ProposalandScheduler(args.config)
        
        if args.test_email:
            success = scheduler.email_notifier.test_email_configuration()
            print(f"Email test {'PASSED' if success else 'FAILED'}")
            sys.exit(0 if success else 1)
        
        if args.run_once:
            scheduler.run_daily_monitoring()
        else:
            scheduler.start_scheduler()
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

