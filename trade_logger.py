"""
Google Sheets trade logging system
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

class TradeLogger:
    """Simple Google Sheets trade logging"""
    
    def __init__(self, config):
        self.config = config
        self.sheet = None
        self.lot_size = 75
        self.margin_per_lot = 800000  # 8 lakh per lot as originally specified
        
    def initialize_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            # Use service account credentials
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            # You need to create service account JSON file
            creds = Credentials.from_service_account_file(
                'service_account.json', scopes=scope)
            
            client = gspread.authorize(creds)
            
            # Open or create spreadsheet
            try:
                self.sheet = client.open("Trading_Log").sheet1
                # Check if headers exist, if not add them
                if not self.sheet.get_all_values() or self.sheet.cell(1,1).value != 'NIFTY 6-LEG STRANGLE TRADING LOG':
                    self.sheet.clear()
                    self._setup_headers()
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create("Trading_Log")
                self.sheet = spreadsheet.sheet1
                self._setup_headers()
                
            return True
        except Exception as e:
            print(f"Google Sheets initialization failed: {e}")
            return False
    
    def _setup_headers(self):
        """Setup spreadsheet headers"""
        # Add title
        self.sheet.append_row(['NIFTY 6-LEG STRANGLE TRADING LOG'])
        self.sheet.append_row(['Account:', self.config['shoonya']['user']])
        self.sheet.append_row([])
        
        # Add trade log headers
        headers = [
            'Date', 'Time', 'Strike', 'Type', 'Action', 
            'Sell Price', 'Current/Buy Price', 'P&L',
            'Qty', 'Lots', 'Total Margin', 'P&L %'
        ]
        self.sheet.append_row(headers)
        
        # Add description row
        descriptions = [
            'Trade Date', 'Trade Time', 'Strike Price', 'CE/PE', 'SELL/BUY',
            'Sell Value', 'Current/Buy Value', 'Profit/Loss Amount',
            'Quantity', 'Number of Lots', 'Deployed Capital', 'Loss/Profit %'
        ]
        self.sheet.append_row(descriptions)
        self.sheet.append_row([''] * 12)
    
    def log_trade(self, position, sell_price, current_price, action='SELL'):
        """Log individual trade with simple P&L calculation"""
        if not self.sheet:
            return 0, 0
            
        try:
            lots = position.qty / self.lot_size
            total_margin = lots * self.margin_per_lot
            
            if action == 'SELL':
                profit_loss = 0  # No P&L on opening
                position.sell_price = sell_price  # Store for future calculations
            else:  # BUY (closing)
                profit_loss = (sell_price - current_price) * position.qty
            
            pl_percentage = (profit_loss / total_margin * 100) if total_margin > 0 else 0
            
            row = [
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%H:%M:%S'),
                position.strike,
                position.type,
                action,
                sell_price if action == 'SELL' else getattr(position, 'sell_price', 0),
                current_price,
                profit_loss,
                position.qty,
                lots,
                total_margin,
                f"{pl_percentage:.2f}%"
            ]
            
            self.sheet.append_row(row)
            return profit_loss, pl_percentage
            
        except Exception as e:
            print(f"Trade logging failed: {e}")
            return 0, 0
    
    def log_basket_summary(self, basket_data, total_pl, total_pl_percent):
        """Log basket summary"""
        if not self.sheet:
            return
            
        try:
            summary_row = [
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%H:%M:%S'),
                f"BASKET_{basket_data.get('type', 'SUMMARY')}",
                'SUMMARY',
                '',
                '',
                '',
                total_pl,
                '',
                '',
                '',
                f"{total_pl_percent:.2f}%"
            ]
            
            self.sheet.append_row(summary_row)
            self.sheet.append_row([''] * 12)
            
        except Exception as e:
            print(f"Basket summary logging failed: {e}")
    
    def calculate_portfolio_pl(self, positions, current_prices):
        """Calculate total portfolio P&L with simple calculation"""
        total_pl = 0
        total_margin = 0
        
        for position in positions:
            if position.strike in current_prices:
                current_price = current_prices[position.strike]
                sell_price = getattr(position, 'sell_price', 0)
                
                lots = position.qty / self.lot_size
                margin = lots * self.margin_per_lot
                total_margin += margin
                
                # Calculate P&L (we sold, so profit when current < sell)
                pl = (sell_price - current_price) * position.qty
                total_pl += pl
        
        pl_percentage = (total_pl / total_margin * 100) if total_margin > 0 else 0
        return total_pl, pl_percentage, total_margin
    
    def update_account_summary(self, limits_data=None):
        """Update account summary - disabled"""
        pass
    
    def set_api_reference(self, api):
        """Set API reference"""
        self.api = api