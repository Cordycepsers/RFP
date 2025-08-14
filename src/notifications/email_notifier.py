"""
Email notification system for Proposaland opportunity monitoring.
Sends professional email notifications with Excel and JSON attachments.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import os


class EmailNotifier:
    """Professional email notification system with attachments and HTML templates."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config.get('email', {})
        self.smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.email_config.get('smtp_port', 587)
        self.sender_email = self.email_config.get('sender_email', '')
        self.sender_password = self.email_config.get('sender_password', '')
        self.recipient_email = self.email_config.get('recipient_email', 'majalemaja@pm.me')
        
        # Email templates
        self.templates_dir = Path(__file__).parent / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize templates
        self._create_email_templates()
    
    def _create_email_templates(self):
        """Create HTML email templates."""
        # Main notification template
        main_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proposaland Daily Opportunities Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #366092;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #366092;
            margin: 0;
            font-size: 28px;
        }
        .header .date {
            color: #666;
            font-size: 16px;
            margin-top: 5px;
        }
        .summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #366092;
        }
        .summary h2 {
            color: #366092;
            margin-top: 0;
            font-size: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-item {
            text-align: center;
            padding: 15px;
            background-color: white;
            border-radius: 6px;
            border: 1px solid #ddd;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #366092;
            display: block;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-top: 5px;
        }
        .priority-critical { background-color: #ff6b6b; color: white; }
        .priority-high { background-color: #ffe66d; color: #333; }
        .priority-medium { background-color: #a8e6cf; color: #333; }
        .priority-low { background-color: #e8e8e8; color: #333; }
        .opportunities {
            margin-top: 30px;
        }
        .opportunity {
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .opportunity-header {
            padding: 15px 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }
        .opportunity-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin: 0;
        }
        .opportunity-meta {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .opportunity-body {
            padding: 20px;
        }
        .opportunity-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .detail-item {
            font-size: 14px;
        }
        .detail-label {
            font-weight: bold;
            color: #366092;
        }
        .priority-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .attachments {
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            text-align: center;
        }
        .attachments h3 {
            color: #366092;
            margin-top: 0;
        }
        .attachment-list {
            list-style: none;
            padding: 0;
            margin: 15px 0;
        }
        .attachment-list li {
            margin: 8px 0;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
        }
        .keywords {
            margin-top: 10px;
        }
        .keyword-tag {
            display: inline-block;
            background-color: #366092;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Proposaland Daily Report</h1>
            <div class="date">{{date}}</div>
        </div>
        
        <div class="summary">
            <h2>📊 Summary</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">{{total_opportunities}}</span>
                    <span class="stat-label">Total Opportunities</span>
                </div>
                <div class="stat-item priority-critical">
                    <span class="stat-number">{{critical_count}}</span>
                    <span class="stat-label">Critical Priority</span>
                </div>
                <div class="stat-item priority-high">
                    <span class="stat-number">{{high_count}}</span>
                    <span class="stat-label">High Priority</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{{avg_score}}</span>
                    <span class="stat-label">Avg Score</span>
                </div>
            </div>
            
            <p><strong>Top Keywords:</strong> {{top_keywords}}</p>
            <p><strong>Top Sources:</strong> {{top_sources}}</p>
        </div>
        
        {{#if has_critical_opportunities}}
        <div class="opportunities">
            <h2>🚨 Critical Priority Opportunities</h2>
            {{#each critical_opportunities}}
            <div class="opportunity">
                <div class="opportunity-header">
                    <h3 class="opportunity-title">{{title}}</h3>
                    <div class="opportunity-meta">
                        {{organization}} | 
                        <span class="priority-badge priority-critical">{{priority}}</span> |
                        Score: {{relevance_score}}
                    </div>
                </div>
                <div class="opportunity-body">
                    <div class="opportunity-details">
                        <div class="detail-item">
                            <span class="detail-label">Reference:</span> {{reference_number}}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Deadline:</span> {{deadline}}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Budget:</span> {{budget}}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Location:</span> {{location}}
                        </div>
                    </div>
                    <div class="keywords">
                        {{#each keywords_found}}
                        <span class="keyword-tag">{{this}}</span>
                        {{/each}}
                    </div>
                </div>
            </div>
            {{/each}}
        </div>
        {{/if}}
        
        {{#if has_high_opportunities}}
        <div class="opportunities">
            <h2>⚡ High Priority Opportunities</h2>
            {{#each high_opportunities}}
            <div class="opportunity">
                <div class="opportunity-header">
                    <h3 class="opportunity-title">{{title}}</h3>
                    <div class="opportunity-meta">
                        {{organization}} | 
                        <span class="priority-badge priority-high">{{priority}}</span> |
                        Score: {{relevance_score}}
                    </div>
                </div>
                <div class="opportunity-body">
                    <div class="opportunity-details">
                        <div class="detail-item">
                            <span class="detail-label">Reference:</span> {{reference_number}}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Deadline:</span> {{deadline}}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Budget:</span> {{budget}}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Location:</span> {{location}}
                        </div>
                    </div>
                    <div class="keywords">
                        {{#each keywords_found}}
                        <span class="keyword-tag">{{this}}</span>
                        {{/each}}
                    </div>
                </div>
            </div>
            {{/each}}
        </div>
        {{/if}}
        
        <div class="attachments">
            <h3>📎 Attachments</h3>
            <p>Complete opportunity data is attached to this email:</p>
            <ul class="attachment-list">
                <li>📊 Excel Tracker (proposaland_tracker_{{date_str}}.xlsx)</li>
                <li>📄 JSON Data (proposaland_opportunities_{{date_str}}.json)</li>
            </ul>
            <p><em>Open the Excel file for detailed analysis and tracking capabilities.</em></p>
        </div>
        
        <div class="footer">
            <p>Generated by Proposaland Opportunity Monitor | {{timestamp}}</p>
            <p>This is an automated report. For questions, please contact your system administrator.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Save template
        template_path = self.templates_dir / 'main_notification.html'
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(main_template)
    
    def send_daily_report(self, opportunities: List[Dict], summary: Dict, 
                         excel_path: str, json_path: str) -> bool:
        """Send daily opportunities report with attachments."""
        try:
            # Prepare email content
            subject = self._generate_subject(summary)
            html_content = self._generate_html_content(opportunities, summary)
            text_content = self._generate_text_content(opportunities, summary)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = self.recipient_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Add attachments
            self._add_attachment(message, excel_path)
            self._add_attachment(message, json_path)
            
            # Send email
            success = self._send_email(message)
            
            if success:
                logger.info(f"Daily report sent successfully to {self.recipient_email}")
            else:
                logger.error("Failed to send daily report")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def send_urgent_alert(self, critical_opportunities: List[Dict]) -> bool:
        """Send urgent alert for critical opportunities."""
        try:
            if not critical_opportunities:
                return True
            
            subject = f"🚨 URGENT: {len(critical_opportunities)} Critical Opportunities Found"
            
            # Generate urgent alert content
            html_content = self._generate_urgent_alert_html(critical_opportunities)
            text_content = self._generate_urgent_alert_text(critical_opportunities)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = self.recipient_email
            
            # Add content
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            success = self._send_email(message)
            
            if success:
                logger.info(f"Urgent alert sent for {len(critical_opportunities)} critical opportunities")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending urgent alert: {e}")
            return False
    
    def _generate_subject(self, summary: Dict) -> str:
        """Generate email subject line."""
        total = summary.get('total_opportunities', 0)
        critical = summary.get('priority_breakdown', {}).get('Critical', 0)
        high = summary.get('priority_breakdown', {}).get('High', 0)
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        if critical > 0:
            return f"🚨 Proposaland Report ({date_str}): {total} opportunities, {critical} CRITICAL"
        elif high > 0:
            return f"⚡ Proposaland Report ({date_str}): {total} opportunities, {high} high priority"
        else:
            return f"📊 Proposaland Report ({date_str}): {total} opportunities found"
    
    def _generate_html_content(self, opportunities: List[Dict], summary: Dict) -> str:
        """Generate HTML email content."""
        # Load template
        template_path = self.templates_dir / 'main_notification.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Prepare template variables
        date_str = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        priority_breakdown = summary.get('priority_breakdown', {})
        top_keywords = summary.get('top_keywords', [])
        top_sources = summary.get('top_organizations', [])
        
        # Get priority-specific opportunities
        critical_opps = [opp for opp in opportunities if opp.get('priority') == 'Critical'][:5]
        high_opps = [opp for opp in opportunities if opp.get('priority') == 'High'][:5]
        
        # Format data for template
        template_vars = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'date_str': date_str,
            'timestamp': timestamp,
            'total_opportunities': summary.get('total_opportunities', 0),
            'critical_count': priority_breakdown.get('Critical', 0),
            'high_count': priority_breakdown.get('High', 0),
            'avg_score': f"{summary.get('average_score', 0):.2f}",
            'top_keywords': ', '.join([kw['keyword'] for kw in top_keywords[:5]]),
            'top_sources': ', '.join([org['name'] for org in top_sources[:3]]),
            'has_critical_opportunities': len(critical_opps) > 0,
            'critical_opportunities': self._format_opportunities_for_template(critical_opps),
            'has_high_opportunities': len(high_opps) > 0,
            'high_opportunities': self._format_opportunities_for_template(high_opps)
        }
        
        # Simple template replacement (for a full implementation, consider using Jinja2)
        html_content = template
        for key, value in template_vars.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value))
        
        # Handle conditional blocks (simplified)
        if not template_vars['has_critical_opportunities']:
            # Remove critical opportunities section
            start_marker = "{{#if has_critical_opportunities}}"
            end_marker = "{{/if}}"
            start_idx = html_content.find(start_marker)
            if start_idx != -1:
                end_idx = html_content.find(end_marker, start_idx)
                if end_idx != -1:
                    html_content = html_content[:start_idx] + html_content[end_idx + len(end_marker):]
        
        return html_content
    
    def _generate_text_content(self, opportunities: List[Dict], summary: Dict) -> str:
        """Generate plain text email content."""
        lines = []
        lines.append("PROPOSALAND DAILY OPPORTUNITIES REPORT")
        lines.append("=" * 50)
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append(f"Total Opportunities: {summary.get('total_opportunities', 0)}")
        
        priority_breakdown = summary.get('priority_breakdown', {})
        lines.append(f"Critical Priority: {priority_breakdown.get('Critical', 0)}")
        lines.append(f"High Priority: {priority_breakdown.get('High', 0)}")
        lines.append(f"Medium Priority: {priority_breakdown.get('Medium', 0)}")
        lines.append(f"Low Priority: {priority_breakdown.get('Low', 0)}")
        lines.append(f"Average Score: {summary.get('average_score', 0):.2f}")
        lines.append("")
        
        # Top keywords
        top_keywords = summary.get('top_keywords', [])
        if top_keywords:
            lines.append("TOP KEYWORDS:")
            for kw in top_keywords[:5]:
                lines.append(f"  - {kw['keyword']} ({kw['count']} opportunities)")
            lines.append("")
        
        # Critical opportunities
        critical_opps = [opp for opp in opportunities if opp.get('priority') == 'Critical']
        if critical_opps:
            lines.append("CRITICAL PRIORITY OPPORTUNITIES:")
            lines.append("-" * 40)
            for i, opp in enumerate(critical_opps[:5], 1):
                lines.append(f"{i}. {opp.get('title', 'No title')}")
                lines.append(f"   Organization: {opp.get('organization', 'Unknown')}")
                lines.append(f"   Reference: {opp.get('reference_number', 'N/A')}")
                lines.append(f"   Score: {opp.get('relevance_score', 0):.2f}")
                lines.append(f"   Keywords: {', '.join(opp.get('keywords_found', []))}")
                lines.append("")
        
        # High priority opportunities
        high_opps = [opp for opp in opportunities if opp.get('priority') == 'High']
        if high_opps:
            lines.append("HIGH PRIORITY OPPORTUNITIES:")
            lines.append("-" * 40)
            for i, opp in enumerate(high_opps[:5], 1):
                lines.append(f"{i}. {opp.get('title', 'No title')}")
                lines.append(f"   Organization: {opp.get('organization', 'Unknown')}")
                lines.append(f"   Reference: {opp.get('reference_number', 'N/A')}")
                lines.append(f"   Score: {opp.get('relevance_score', 0):.2f}")
                lines.append("")
        
        lines.append("ATTACHMENTS:")
        lines.append("- Excel Tracker (proposaland_tracker_YYYY-MM-DD.xlsx)")
        lines.append("- JSON Data (proposaland_opportunities_YYYY-MM-DD.json)")
        lines.append("")
        lines.append("Generated by Proposaland Opportunity Monitor")
        
        return "\n".join(lines)
    
    def _generate_urgent_alert_html(self, critical_opportunities: List[Dict]) -> str:
        """Generate HTML content for urgent alerts."""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #ff6b6b; color: white; padding: 20px; text-align: center; border-radius: 8px;">
                    <h1 style="margin: 0;">🚨 URGENT ALERT</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">{len(critical_opportunities)} Critical Opportunities Detected</p>
                </div>
                
                <div style="margin-top: 20px;">
                    <p><strong>The following critical opportunities require immediate attention:</strong></p>
        """
        
        for i, opp in enumerate(critical_opportunities[:3], 1):
            html += f"""
                    <div style="border: 1px solid #ddd; border-radius: 6px; margin: 15px 0; padding: 15px; background-color: #fff5f5;">
                        <h3 style="margin: 0 0 10px 0; color: #d63031;">{i}. {opp.get('title', 'No title')}</h3>
                        <p style="margin: 5px 0;"><strong>Organization:</strong> {opp.get('organization', 'Unknown')}</p>
                        <p style="margin: 5px 0;"><strong>Reference:</strong> {opp.get('reference_number', 'N/A')}</p>
                        <p style="margin: 5px 0;"><strong>Score:</strong> {opp.get('relevance_score', 0):.2f}</p>
                        <p style="margin: 5px 0;"><strong>Keywords:</strong> {', '.join(opp.get('keywords_found', []))}</p>
                    </div>
            """
        
        html += """
                    <div style="background-color: #e8f4f8; padding: 15px; border-radius: 6px; margin-top: 20px; text-align: center;">
                        <p style="margin: 0;"><strong>Action Required:</strong> Review these opportunities immediately and prepare proposals as needed.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_urgent_alert_text(self, critical_opportunities: List[Dict]) -> str:
        """Generate text content for urgent alerts."""
        lines = []
        lines.append("🚨 URGENT ALERT - CRITICAL OPPORTUNITIES DETECTED")
        lines.append("=" * 60)
        lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Critical Opportunities Found: {len(critical_opportunities)}")
        lines.append("")
        lines.append("IMMEDIATE ACTION REQUIRED:")
        lines.append("")
        
        for i, opp in enumerate(critical_opportunities[:5], 1):
            lines.append(f"{i}. {opp.get('title', 'No title')}")
            lines.append(f"   Organization: {opp.get('organization', 'Unknown')}")
            lines.append(f"   Reference: {opp.get('reference_number', 'N/A')}")
            lines.append(f"   Score: {opp.get('relevance_score', 0):.2f}")
            lines.append(f"   Keywords: {', '.join(opp.get('keywords_found', []))}")
            lines.append("")
        
        lines.append("Please review these opportunities immediately and prepare proposals as needed.")
        lines.append("")
        lines.append("Generated by Proposaland Opportunity Monitor")
        
        return "\n".join(lines)
    
    def _format_opportunities_for_template(self, opportunities: List[Dict]) -> List[Dict]:
        """Format opportunities for HTML template."""
        formatted = []
        
        for opp in opportunities:
            formatted_opp = {
                'title': opp.get('title', 'No title'),
                'organization': opp.get('organization', 'Unknown'),
                'priority': opp.get('priority', 'Low'),
                'relevance_score': f"{opp.get('relevance_score', 0):.2f}",
                'reference_number': opp.get('reference_number', 'N/A'),
                'deadline': self._format_deadline(opp.get('deadline')),
                'budget': self._format_budget(opp.get('budget'), opp.get('currency', 'USD')),
                'location': opp.get('location', 'Not specified'),
                'keywords_found': opp.get('keywords_found', [])
            }
            formatted.append(formatted_opp)
        
        return formatted
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """Add file attachment to email message."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"Attachment file not found: {file_path}")
                return
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.name}'
            )
            
            message.attach(part)
            logger.info(f"Added attachment: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
    
    def _send_email(self, message: MIMEMultipart) -> bool:
        """Send email message via SMTP."""
        try:
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                
                text = message.as_string()
                server.sendmail(self.sender_email, self.recipient_email, text)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _format_deadline(self, deadline) -> str:
        """Format deadline for display."""
        if not deadline:
            return 'Not specified'
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return deadline
        
        if isinstance(deadline, datetime):
            return deadline.strftime('%Y-%m-%d')
        
        return str(deadline)
    
    def _format_budget(self, budget, currency: str) -> str:
        """Format budget for display."""
        if not budget:
            return 'Not specified'
        
        return f"{currency} {budget:,.0f}"
    
    def test_email_configuration(self) -> bool:
        """Test email configuration by sending a test message."""
        try:
            # Create test message
            message = MIMEMultipart()
            message['Subject'] = "Proposaland Email Configuration Test"
            message['From'] = self.sender_email
            message['To'] = self.recipient_email
            
            test_content = f"""
            This is a test email from the Proposaland Opportunity Monitor.
            
            Configuration Test Results:
            - SMTP Server: {self.smtp_server}:{self.smtp_port}
            - Sender: {self.sender_email}
            - Recipient: {self.recipient_email}
            - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            If you receive this email, the configuration is working correctly.
            """
            
            text_part = MIMEText(test_content, 'plain')
            message.attach(text_part)
            
            # Send test email
            success = self._send_email(message)
            
            if success:
                logger.info("Email configuration test successful")
            else:
                logger.error("Email configuration test failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Email configuration test error: {e}")
            return False

