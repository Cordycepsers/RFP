import json
from pathlib import Path
from datetime import datetime

from src.notifications.email_notifier import EmailNotifier


def test_email_notifier_renders():
    config_path = Path('config/proposaland_config.json')
    config = json.loads(config_path.read_text())
    notifier = EmailNotifier(config)

    # Create mock data instead of reading from file
    mock_opportunities = [
        {
            'title': 'Video Production for Health Campaign',
            'organization': 'UNICEF',
            'location': 'Kenya',
            'budget': 75000,
            'currency': 'USD',
            'deadline': '2025-09-15',
            'relevance_score': 0.85,
            'priority': 'High',
            'source_url': 'https://example.com/tender1'
        },
        {
            'title': 'Digital Marketing Campaign',
            'organization': 'World Bank',
            'location': 'Tanzania',
            'budget': 50000,
            'currency': 'USD',
            'deadline': '2025-09-20',
            'relevance_score': 0.72,
            'priority': 'Medium',
            'source_url': 'https://example.com/tender2'
        }
    ]
    
    mock_summary = {
        'total_opportunities': 2,
        'high_priority_count': 1,
        'medium_priority_count': 1,
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'websites_scanned': ['UNICEF', 'World Bank']
    }
    
    opps = mock_opportunities
    summary = mock_summary

    subject = notifier._generate_subject(summary)
    html = notifier._generate_html_content(opps, summary)
    text = notifier._generate_text_content(opps, summary)

    assert isinstance(subject, str) and subject
    assert isinstance(html, str) and '<html' in html.lower()
    assert isinstance(
        text, str) and 'PROPOSALAND DAILY OPPORTUNITIES REPORT' in text
