"""
Configuration settings for the Shoonya 6-Leg Strangle Basket Creator
"""

CONFIG = {
    'config_file': 'config.json',
    'basket_dir': 'baskets',
    'xml_schema': 'basket_schema.xsd',
    'check_interval': 1,  # seconds
    
    # Email Configuration
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'from_email': 'shreyathakurindia@gmail.com',
        'app_password': 'gzcf vvwy efsp wtmm',
        'to_emails': [
            ''
        ]
    },
    
    # Shoonya API Configuration
    'shoonya': {
        'user': 'FA367053',
        'pwd': 'Shreya@0503',
        'factor2': '57MVEP4VRYWF3554S275B3POCA426373',
        'vc': 'FA367053_U',
        'app_key': 'bbd83a033ef48e58107d9d3453a89bb2',
        'imei': 'abc1234'
    },
    
    # Trading Configuration
    'trading': {
        'index': 'NIFTY',
        'exchange': 'NFO',
        'product_type': 'M',  # NRML
        'quantity': 75,
        'session_start': '09:20:00',
        'session_end': '14:00:00',
        'max_adjustment': 0,
        'closed_date': '2025-12-15',
        'spot_reference': 0.0,
        'max_loss_percent': 1.0,  # Force exit if loss > 1%
        'force_exit_movement': 200  # Force exit if spot moves >= 200 points
    }
}