"""
Email notification system for basket creation alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    """Handles email notifications for basket creation"""
    
    def __init__(self, email_config):
        self.config = email_config
        self.enabled = email_config.get('enabled', True)
    
    def send_basket_notification(self, basket_data):
        """Send email notification when basket is created"""
        if not self.enabled:
            return True
            
        try:
            msg = self._create_email_message(basket_data)
            self._send_email(msg)
            print(f"Email sent to {', '.join(self.config['to_emails'])}")
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    def _create_email_message(self, basket_data):
        """Create HTML email message"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New Basket Created: {basket_data['id']}"
        msg['From'] = self.config['from_email']
        msg['To'] = ', '.join(self.config['to_emails'])
        
        html_content = self._generate_html_content(basket_data)
        msg.attach(MIMEText(html_content, 'html'))
        
        return msg
    
    def _generate_html_content(self, basket_data):
        """Generate HTML content for email"""
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2563eb;">New Basket Created</h2>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 10px 0;">
              <p><strong>Basket ID:</strong> {basket_data['id']}</p>
              <p><strong>Type:</strong> {basket_data['type']}</p>
              <p><strong>Timestamp:</strong> {basket_data['timestamp']}</p>
              <p><strong>Spot Value:</strong> ₹{basket_data['spotValue']}</p>
              <p><strong>Reference:</strong> ₹{basket_data.get('newReference', basket_data.get('reference'))}</p>
            </div>
            
            <h3>Orders ({len(basket_data['orders'])})</h3>
            <table style="border-collapse: collapse; width: 100%;">
              <tr style="background: #e5e7eb;">
                <th style="padding: 8px; border: 1px solid #d1d5db;">Action</th>
                <th style="padding: 8px; border: 1px solid #d1d5db;">Strike</th>
                <th style="padding: 8px; border: 1px solid #d1d5db;">Type</th>
                <th style="padding: 8px; border: 1px solid #d1d5db;">Qty</th>
                <th style="padding: 8px; border: 1px solid #d1d5db;">Price</th>
              </tr>
        """
        
        for order in basket_data['orders']:
            color = '#10b981' if order['action'] == 'SELL' else '#ef4444'
            price_display = f"₹{order['price']}" if 'price' in order else 'Market'
            html += f"""
              <tr>
                <td style="padding: 8px; border: 1px solid #d1d5db; color: {color};"><strong>{order['action']}</strong></td>
                <td style="padding: 8px; border: 1px solid #d1d5db;">{order['strike']}</td>
                <td style="padding: 8px; border: 1px solid #d1d5db;">{order['type']}</td>
                <td style="padding: 8px; border: 1px solid #d1d5db;">{order['qty']}</td>
                <td style="padding: 8px; border: 1px solid #d1d5db;">{price_display}</td>
              </tr>
            """
        
        html += """
            </table>
            <p style="margin-top: 20px; color: #6b7280; font-size: 12px;">
              This is an automated notification. Basket created but NOT executed.
            </p>
          </body>
        </html>
        """
        
        return html
    
    def _send_email(self, msg):
        """Send email using SMTP"""
        with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
            server.starttls()
            server.login(self.config['from_email'], self.config['app_password'])
            server.send_message(msg)