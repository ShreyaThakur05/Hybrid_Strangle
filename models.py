"""
Data models and classes for the basket creator
"""

class Order:
    """Order data structure for Shoonya API"""
    def __init__(self):
        self.buy_or_sell = ''
        self.product_type = 'C'
        self.exchange = ''
        self.tradingsymbol = ''
        self.quantity = 0
        self.discloseqty = 0
        self.price_type = 'LMT'
        self.price = 0.00
        self.trigger_price = None
        self.retention = 'DAY'
        self.remarks = ''

class Position:
    """Position data structure for strategy legs"""
    def __init__(self, index, strike, option_type, quantity, remark):
        self.index = index
        self.strike = strike
        self.type = option_type
        self.qty = quantity
        self.remark = remark

class BasketData:
    """Basket data structure"""
    def __init__(self, basket_id, basket_type, spot_value, reference, orders):
        self.id = basket_id
        self.type = basket_type
        self.spot_value = spot_value
        self.reference = reference
        self.orders = orders
        self.timestamp = None
        
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'spotValue': self.spot_value,
            'reference': self.reference,
            'type': self.type,
            'orders': [
                {
                    'action': order.get('action'),
                    'strike': order.get('strike'),
                    'type': order.get('type'),
                    'qty': order.get('qty'),
                    'index': order.get('index'),
                    'remark': order.get('remark')
                } for order in self.orders
            ]
        }