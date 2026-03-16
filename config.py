"""
Configuration settings for the Shoonya 6-Leg Strangle Basket Creator
"""

CONFIG = {
    'config_file': None,  # No longer using JSON file
    'basket_dir': 'baskets',
    'xml_schema': 'basket_schema.xsd',
    'check_interval': 1,  # seconds
    
    # Email Configuration
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'from_email': '',
        'app_password': '',
        'to_emails': [
            ''
        ]
    },
    
    # Shoonya API Configuration
    'shoonya': {
        'user': '',
        'pwd': '',
        'factor2': '',
        'vc': '',
        'app_key': '',
        'imei': ''
    },
    
    # Trading Configuration
    'trading': {
        'index': 'NIFTY',
        'exchange': 'NFO',
        'product_type': 'M',  # NRML
        'quantity': 75,
        'session_start': '07:20:00',
        'session_end': '18:00:00',
        'max_loss_percent': 1.0,  # Force exit if loss > 1%
        'force_exit_movement': 200  # Force exit if spot moves >= 200 points
    },
    
    # Margin Configuration
    'margin': {
        'base_margin_per_lot': 150000,  # Base margin per lot (approx 1.5L)
        'span_margin_per_qty': 50,      # SPAN margin per quantity
        'exposure_margin_rate': 0.05,   # 5% of premium value
        'lot_size': 75                  # NIFTY lot size
    },
    
    # State Configuration (previously in config.json)
    'state': {
        'closed_date': '2025-12-14',
        'max_adjustment': 2,
        'spot_reference': 26200.0,
        'position_prices': {'26100_PE': 71.1, '26100_CE': 71.1, '26000_PE': 18.95, '26200_CE': 28.25, '25900_PE': 8.1, '26300_CE': 9.75}
    }
}
