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
                print(f"Username: {self.username}")
                print(f"Token: {self.user_token[:10]}...{self.user_token[-10:]}")
                return True
            else:
                print(f"Login failed: {result}")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def place_order_direct(self, order):
        """Direct API call to place order (fallback method)"""
        import json
        import requests
        
        # Build the request
        url = "https://api.shoonya.com/NorenWClientTP/PlaceOrder"
        
        order_data = {
            'uid': self.username,
            'actid': self.username,
            'exch': order.exchange,
            'tsym': order.tradingsymbol,
            'qty': str(order.quantity),
            'dscqty': str(order.discloseqty),
            'prc': str(order.price),
            'prd': order.product_type,
            'trantype': order.buy_or_sell,
            'prctyp': order.price_type,
            'ret': order.retention,
            'remarks': order.remarks
        }
        
        payload = {
            'jData': json.dumps(order_data),
            'jKey': self.user_token
        }
        
        print(f"Direct API payload: {payload['jData']}")
        
        try:
            response = requests.post(url, data=payload)
            result = response.json()
            print(f"Direct API response: {result}")
            return result
        except Exception as e:
            print(f"Direct API call failed: {e}")
            return None
    
    def place_basket_orders(self, orders):
        """Place multiple orders using NorenApi built-in method"""
        results = []
        
        for i, order in enumerate(orders):
            try:
                print(f"\n{'='*50}")
                print(f"Placing order {i+1}: {order.buy_or_sell} {order.tradingsymbol} Qty:{order.quantity}")
                print(f"Details: Exchange={order.exchange}, Product={order.product_type}, Price Type={order.price_type}")
                
                # Add validation before placing order
                if not self.logged_in:
                    print(f"❌ Not logged in!")
                    results.append({'stat': 'Not_Ok', 'emsg': 'Not logged in'})
                    continue
                
                # Use NorenApi's place_order method with explicit parameters
                result = self.place_order(
                    buy_or_sell=order.buy_or_sell,
                    product_type=order.product_type,
                    exchange=order.exchange,
                    tradingsymbol=order.tradingsymbol,
                    quantity=int(order.quantity),  # Ensure it's an integer
                    discloseqty=int(order.discloseqty),  # Ensure it's an integer
                    price_type=order.price_type,
                    price=float(order.price) if order.price_type != 'MKT' else 0,
                    trigger_price=None,  # Don't send trigger_price for MKT orders
                    retention=order.retention,
                    remarks=order.remarks
                )
                
                print(f"Raw result: {result}")
                print(f"Result type: {type(result)}")
                
                # If None, try direct API call
                if result is None:
                    print(f"Trying direct API call...")
                    result = self.place_order_direct(order)
                
                # Check if result is still None
                if result is None:
                    print(f"⚠ Order returned None - This usually means an API error")
                    
                    # Check if there's an error in the parent class
                    if hasattr(self, '__lastresponse__'):
                        print(f"Last response: {self.__lastresponse__}")
                    
                    results.append({'stat': 'Not_Ok', 'emsg': 'API returned None'})
                else:
                    results.append(result)
                
            except Exception as exc:
                print(f"❌ Order {i+1} failed with exception: {exc}")
                import traceback
                traceback.print_exc()
                results.append({'stat': 'Not_Ok', 'emsg': str(exc)})
        
        return results
    
    def search_symbol(self, search_text):
        """Search for correct symbol format"""
        try:
            result = self.searchscrip(exchange='NFO', searchtext=search_text)
            if result and 'values' in result:
                print(f"\nSearch results for '{search_text}':")
                for item in result['values'][:5]:  # Show first 5 results
                    print(f"  Symbol: {item.get('tsym')} | Token: {item.get('token')}")
                return result['values']
            else:
                print(f"No results found for '{search_text}'")
                return []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_current_weekly_expiry(self):
        """Get current week's NIFTY expiry - Thursday for weekly options"""
        try:
            # Search specifically for NIFTY options
            search_results = self.search_symbol("NIFTY16DEC25C26000")
            
            # Extract expiry dates from actual option symbols
            expiries = set()
            for result in search_results:
                tsym = result.get('tsym', '')
                if 'NIFTY' in tsym and ('C' in tsym or 'P' in tsym):
                    # Extract expiry from symbol like NIFTY16DEC25C26000
                    parts = tsym.replace('NIFTY', '')
                    # Find expiry part (before C or P)
                    if 'C' in parts:
                        expiry_part = parts.split('C')[0]
                    elif 'P' in parts:
                        expiry_part = parts.split('P')[0]
                    else:
                        continue
                    
                    if len(expiry_part) >= 7 and expiry_part[2:5].isalpha():
                        expiries.add(expiry_part)
            
            if expiries:
                # Sort expiries and take the nearest one
                sorted_expiries = sorted(list(expiries))
                nearest_expiry = sorted_expiries[0]
                print(f"Found expiry from options search: {nearest_expiry}")
                return nearest_expiry
            else:
                # Calculate Thursday expiry correctly
                from datetime import datetime, timedelta
                today = datetime.now().date()
                
                # Find next Tuesday (weekday 1)
                days_ahead = 1 - today.weekday()  # Tuesday is 1
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                # If today is Tuesday and after 3:30 PM, use next Tuesday
                if today.weekday() == 1 and datetime.now().time().hour >= 15:
                    days_ahead = 7
                
                expiry_date = today + timedelta(days=days_ahead)
                formatted = expiry_date.strftime('%d%b%y').upper()
                print(f"Calculated Tuesday expiry: {formatted}")
                return formatted
                
        except Exception as e:
            print(f"Error getting expiry: {e}")
            # Use current week's Thursday as fallback
            return "19DEC24"
    
    def create_order_from_data(self, order_data, basket_name):
        """Create Order object from basket order data"""
        expiry = self.get_current_weekly_expiry()
        strike = int(order_data['strike'])
        option_type = order_data['type']
        
        # CORRECT FORMAT: NIFTY16DEC25C26000 (C for CE, P for PE)
        option_suffix = 'C' if option_type == 'CE' else 'P'
        symbol = f"NIFTY{expiry}{option_suffix}{strike}"
        
        print(f"Creating order for symbol: {symbol}")
        
        # Verify symbol exists
        try:
            search_results = self.search_symbol(f"NIFTY{expiry}{option_suffix}{strike}")
            
            # Find exact match from search
            for result in search_results:
                tsym = result.get('tsym', '')
                if tsym == symbol:
                    token = result.get('token')
                    print(f"✓ Symbol verified: {symbol} (Token: {token})")
                    
                    # Test quote
                    test_quote = self.get_quotes(exchange='NFO', token=token)
                    if test_quote and test_quote.get('stat') == 'Ok':
                        print(f"✓ Quote: LTP={test_quote.get('lp')}")
                    break
            else:
                print(f"⚠ Symbol not found in search results")
        except Exception as e:
            print(f"Symbol verification failed: {e}")
        
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
    

    

    
