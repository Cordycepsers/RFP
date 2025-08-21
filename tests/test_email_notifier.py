import json
from pathlib import Path

from src.notifications.email_notifier import EmailNotifier


def test_email_notifier_renders():
    config_path = Path('config/proposaland_config.json')
    config = json.loads(config_path.read_text())
    notifier = EmailNotifier(config)

    json_path = Path('output/proposaland_opportunities_2025-08-15.json')
    obj = json.loads(json_path.read_text())
    opps = obj.get('opportunities', [])
    summary = obj.get('summary', {})

    subject = notifier._generate_subject(summary)
    html = notifier._generate_html_content(
        opps, summary, excel_path='output/proposaland_tracker_2025-08-15.xlsx', json_path=str(json_path))
    text = notifier._generate_text_content(opps, summary)

    assert isinstance(subject, str) and subject
    assert isinstance(html, str) and '<html' in html.lower()
    assert isinstance(
        text, str) and 'PROPOSALAND DAILY OPPORTUNITIES REPORT' in text
