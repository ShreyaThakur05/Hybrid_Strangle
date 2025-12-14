"""
Shoonya API wrapper with basket functionality
"""

from NorenRestApiPy.NorenApi import NorenApi
import pyotp
from datetime import datetime
import datetime as dt
from models import Order

class ShoonyaApiWrapper(NorenApi):
    """Enhanced Shoonya API with basket functionality"""
    
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWClientTP/', 
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )
        self.logged_in = False
    
    def authenticate(self, credentials):
        """Login to Shoonya with TOTP generation"""
        try:
            # Generate current TOTP
            totp = pyotp.TOTP(credentials['factor2'])
            current_otp = totp.now()
            
            result = self.login(
                userid=credentials['user'],
                password=credentials['pwd'],
                twoFA=current_otp,
                vendor_code=credentials['vc'],
                api_secret=credentials['app_key'],
                imei=credentials['imei']
            )
            
            if result and result.get('stat') == 'Ok':
                self.logged_in = True
                # Store credentials for direct API calls
                self.username = credentials['user']
                self.user_token = result.get('susertoken')
                print(f"Login successful at {datetime.now()}")
                return True
            else:
                print(f"Login failed: {result}")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def place_basket_orders(self, orders):
        """Place multiple orders using NorenApi place_order method"""
        results = []
        
        for i, order in enumerate(orders):
            try:
                print(f"Placing order {i+1}: {order.buy_or_sell} {order.tradingsymbol} Qty:{order.quantity}")
                
                # Use NorenApi's built-in place_order method
                result = self.place_order(
                    buy_or_sell=order.buy_or_sell,
                    product_type=order.product_type,
                    exchange=order.exchange,
                    tradingsymbol=order.tradingsymbol,
                    quantity=order.quantity,
                    discloseqty=order.discloseqty,
                    price_type=order.price_type,
                    price=order.price,
                    trigger_price="0",
                    retention=order.retention,
                    remarks=order.remarks
                )
                
                print(f"Order {i+1} result: {result}")
                results.append(result)
                
            except Exception as exc:
                print(f"Order {i+1} failed: {exc}")
                results.append({'stat': 'Not_Ok', 'emsg': str(exc)})
        
        return results
    
    def create_order_from_data(self, order_data, basket_name):
        """Create Order object from basket order data"""
        # Generate trading symbol - try different formats
        expiry = "26DEC24"  # Update with actual expiry
        strike = int(order_data['strike'])
        
        # Try standard NIFTY option format
        symbol = f"NIFTY{expiry}{strike}{order_data['type']}"
        
        # Alternative format with space
        # symbol = f"NIFTY {expiry} {strike} {order_data['type']}"
        
        print(f"Creating order for symbol: {symbol}")
        
        # Test if symbol exists by getting quote first
        try:
            test_quote = self.get_quotes('NFO', symbol)
            print(f"Symbol test result: {test_quote}")
        except Exception as e:
            print(f"Symbol test failed: {e}")
        
        order = Order()
        order.buy_or_sell = 'S' if order_data['action'] == 'SELL' else 'B'
        order.product_type = 'M'  # NRML
        order.exchange = 'NFO'
        order.tradingsymbol = symbol
        order.quantity = str(order_data['qty'])
        order.discloseqty = '0'
        order.price_type = 'MKT'
        order.price = '0'
        order.trigger_price = '0'
        order.retention = 'DAY'
        order.remarks = order_data.get('remark', basket_name)
        
        return order
    
    def get_spot_price(self, symbol='BANKNIFTY'):
        """Get current NIFTY/BANKNIFTY spot price"""
        try:
            # Token mapping
            tokens = {
                'NIFTY': '26000',
                'BANKNIFTY': '26009'
            }
            
            token = tokens.get(symbol)
            if not token:
                raise ValueError(f"Unknown symbol: {symbol}")
            
            quote = self.get_quotes(exchange='NSE', token=token)
            
            if quote and quote.get('stat') == 'Ok':
                spot = float(quote.get('lp', 0))
                return spot
            else:
                print(f"Failed to get spot price")
                return None
                
        except Exception as e:
            print(f"Error getting spot price: {str(e)}")
            return None