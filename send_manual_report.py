#!/usr/bin/env python3
"""
Manual report sender - sends email with current opportunities data
"""

import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append('src')

from src.notifications.email_notifier import EmailNotifier

def send_manual_report():
    """Send manual email report with current data."""
    print("🚀 Sending manual email report with real data...")
    
    # Load config
    with open('config/proposaland_config.json', 'r') as f:
        config = json.load(f)
    
    # Load the latest opportunities data
    try:
        with open('output/proposaland_opportunities_2025-08-14.json', 'r') as f:
            data = json.load(f)
        
        opportunities_list = data['opportunities']
        print(f"📊 Loaded {len(opportunities_list)} opportunities")
        
        # Use existing files
        excel_path = 'output/proposaland_tracker_2025-08-14.xlsx'
        json_path = 'output/proposaland_opportunities_2025-08-14.json'
        
        # Create summary from the data
        summary = data.get('summary', {
            'total_opportunities': len(opportunities_list),
            'priority_breakdown': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': len(opportunities_list)},
            'sources': list(set([opp['organization'] for opp in opportunities_list[:10]])),
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Initialize email notifier
        notifier = EmailNotifier(config)
        print(f"📧 Sending to: {', '.join(notifier.recipient_emails)}")
        
        # Send email
        success = notifier.send_daily_report(opportunities_list, summary, excel_path, json_path)
        
        if success:
            print("🎉 Email sent successfully!")
            print("📬 Check all recipient inboxes:")
            for email in notifier.recipient_emails:
                print(f"  ✉️  {email}")
            print("📋 Report includes:")
            print(f"  📊 {len(opportunities_list)} opportunities")
            print(f"  📈 Excel tracker: {excel_path}")
            print(f"  📄 JSON data: {json_path}")
        else:
            print("❌ Email sending failed")
            
    except FileNotFoundError:
        print("❌ No opportunities data found. Run monitoring first.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_manual_report()
