"""
Main basket management orchestrator
"""

import time
from datetime import datetime
from shoonya_api import ShoonyaApiWrapper
from strategy import StrangleStrategy
from file_manager import FileManager
from notification import EmailNotifier
from config_manager import ConfigManager
from trade_logger import TradeLogger

class BasketManager:
    """Main orchestrator for basket creation and management"""
    
    def __init__(self, config):
        self.config = config
        self.api = ShoonyaApiWrapper()
        self.strategy = StrangleStrategy(config['trading']['quantity'])
        self.file_manager = FileManager(config)
        self.notifier = EmailNotifier(config['email'])
        self.config_manager = ConfigManager()
        self.trade_logger = TradeLogger(config)
        
        # State management
        self.current_positions = []
        self.baskets = []
        self.position_prices = {}  # Track sell prices
    
    def initialize(self):
        """Initialize the basket manager"""
        api_success = self.api.authenticate(self.config['shoonya'])
        sheets_success = self.trade_logger.initialize_sheets()
        return api_success and sheets_success
    
    def create_basket(self, basket_data):
        """Create and process a basket"""
        basket_id = basket_data['id']
        basket_name = f"{basket_data['type']}_{datetime.now().strftime('%H%M%S')}"
        
        print(f"\n{'='*60}")
        print(f"Creating Basket: {basket_id}")
        print(f"Type: {basket_data['type']}")
        print(f"Spot: {basket_data['spotValue']}")
        
        # Try to place orders in Shoonya
        self._attempt_order_placement(basket_data, basket_name)
        
        # Save basket files
        self._save_basket_files(basket_data)
        
        # Send notification
        self.notifier.send_basket_notification(basket_data)
        
        # Display order summary
        self._display_order_summary(basket_data)
        
        print(f"{'='*60}\n")
        return basket_data
    
    def check_and_adjust(self, spot_value):
        """Check if adjustment is needed and create basket"""
        # Force exit check for >=200 point movement
        spot_reference = self.config_manager.get_spot_reference()
        if spot_reference and abs(spot_value - spot_reference) >= 200:
            print(f"FORCE EXIT: Spot moved {abs(spot_value - spot_reference):.0f} points (>=200)")
            self._force_exit_all_positions(spot_value)
            return
        
        if not self._should_adjust(spot_value):
            return
        
        adjustment_needed, movement = self.strategy.calculate_adjustment_needed(
            spot_value, self.config_manager.get_spot_reference()
        )
        
        if adjustment_needed:
            self._process_adjustment(spot_value, movement)
    
    def _should_adjust(self, spot_value):
        """Check if adjustment should be processed"""
        spot_reference = self.config_manager.get_spot_reference()
        if spot_reference is None or spot_reference == 0.0:
            return False
        
        # Check trading hours first
        if not self._is_trading_hours():
            return False
        
        # Check loss limit - force exit if loss > 1%
        if self._check_loss_limit(spot_value):
            return False
        
        # Check max adjustments limit
        max_adj = self.config_manager.get_max_adjustment()
        if max_adj <= 0:
            print(f"No adjustments remaining.")
            return False
        
        return True
    
    def _is_trading_hours(self):
        """Check if current time is within trading hours"""
        current_time = datetime.now().strftime('%H:%M:%S')
        start_time = self.config['trading']['session_start']
        end_time = self.config['trading']['session_end']
        
        if current_time < start_time or current_time > end_time:
            if current_time < start_time:
                print(f"Before trading hours. Waiting until {start_time}")
            else:
                print(f"After trading hours. Session ended at {end_time}")
            return False
        return True
    
    def _check_loss_limit(self, current_spot):
        """Check if loss exceeds limit and force exit"""
        if not self.current_positions:
            return False
        
        # Get current market prices for all positions
        current_prices = self._get_current_market_prices()
        
        # Calculate portfolio P&L
        total_pl, pl_percentage, total_margin = self.trade_logger.calculate_portfolio_pl(
            self.current_positions, current_prices
        )
        
        max_loss = self.config['trading']['max_loss_percent']
        
        if abs(pl_percentage) > max_loss:
            print(f"FORCE EXIT: P&L {pl_percentage:.2f}% exceeds limit {max_loss}%")
            self._force_exit_all_positions(current_spot, pl_percentage)
            return True
        
        return False
    
    def _force_exit_all_positions(self, current_spot, pl_percentage=None):
        """Force exit all positions and log trades"""
        if not self.current_positions:
            return
        
        date_str = datetime.now().strftime('%Y%m%d')
        remark = f"BASKET_{date_str}_EXIT"
        
        # Get current market prices
        current_prices = self._get_current_market_prices()
        
        # Log all closing trades
        total_pl = 0
        for position in self.current_positions:
            if position.strike in current_prices:
                current_price = current_prices[position.strike]
                sell_price = self.position_prices.get(f"{position.strike}_{position.type}", 0)
                
                pl, pl_pct = self.trade_logger.log_trade(
                    position, sell_price, current_price, 'BUY'
                )
                total_pl += pl
        
        # Create BUY orders to close all positions
        exit_orders = []
        for position in self.current_positions:
            exit_orders.append({
                'action': 'BUY',
                'strike': position.strike,
                'type': position.type,
                'qty': position.qty,
                'index': position.index,
                'remark': remark
            })
        
        exit_basket = {
            'id': f"BASKET_{date_str}_EXIT",
            'timestamp': datetime.now().isoformat(),
            'spotValue': current_spot,
            'type': 'FORCE_EXIT',
            'pl_percentage': pl_percentage,
            'orders': exit_orders
        }
        
        # Process exit basket
        basket = self.create_basket(exit_basket)
        self.baskets.append(basket)
        
        # Log basket summary
        if pl_percentage:
            self.trade_logger.log_basket_summary(exit_basket, total_pl, pl_percentage)
        
        # Reset state
        self.current_positions = []
        self.position_prices = {}
        self.config_manager.reset_for_next_day()
        
        print(f"Force exit completed. All positions closed.")
    
    def _process_adjustment(self, spot_value, movement):
        """Process position adjustment"""
        print(f"\nAdjustment triggered! Movement: {movement:+.0f} points")
        
        # Calculate new reference and positions
        current_reference = self.config_manager.get_spot_reference()
        new_reference = self.strategy.calculate_new_reference(current_reference, movement)
        target_positions = self.strategy.create_initial_positions(new_reference)
        
        # Find positions to adjust
        to_close, to_open = self.strategy.find_positions_to_adjust(
            self.current_positions, target_positions
        )
        
        # Get current market prices
        current_prices = self._get_current_market_prices()
        
        # Log closing trades
        total_pl = 0
        for position in to_close:
            if position.strike in current_prices:
                current_price = current_prices[position.strike]
                sell_price = self.position_prices.get(f"{position.strike}_{position.type}", 0)
                
                pl, pl_pct = self.trade_logger.log_trade(
                    position, sell_price, current_price, 'BUY'
                )
                total_pl += pl
        
        # Log opening trades
        for position in to_open:
            if position.strike in current_prices:
                market_price = current_prices[position.strike]
                self.position_prices[f"{position.strike}_{position.type}"] = market_price
                
                pl, pl_pct = self.trade_logger.log_trade(
                    position, market_price, market_price, 'SELL'
                )
                total_pl += pl
        
        # Create adjustment basket
        adjustment_count = 3 - self.config_manager.get_max_adjustment()
        date_str = datetime.now().strftime('%Y%m%d')
        remark = f"BASKET_{date_str}_ADJ{adjustment_count}"
        
        orders = self.strategy.create_adjustment_orders(to_close, to_open, remark)
        
        basket_data = {
            'id': f"BASKET_{date_str}_ADJ{adjustment_count}",
            'timestamp': datetime.now().isoformat(),
            'spotValue': spot_value,
            'oldReference': current_reference,
            'newReference': new_reference,
            'movement': movement,
            'type': 'ADJUSTMENT',
            'orders': orders
        }
        
        # Process the basket
        basket = self.create_basket(basket_data)
        self.baskets.append(basket)
        
        # Log basket summary
        pl_percentage = (total_pl / (len(target_positions) * 75 * 800000 / 75)) * 100
        self.trade_logger.log_basket_summary(basket_data, total_pl, pl_percentage)
        
        # Update state
        self.current_positions = target_positions
        self.config_manager.decrement_adjustment()
        self.config_manager.update_spot_reference(new_reference)
    
    def _attempt_order_placement(self, basket_data, basket_name):
        """Attempt to place orders in Shoonya"""
        if not self.api.logged_in:
            print("Not logged in to Shoonya. Skipping order placement.")
            return
        
        try:
            orders = []
            for order_data in basket_data['orders']:
                order = self.api.create_order_from_data(order_data, basket_name)
                orders.append(order)
                print(f"Created order: {order.buy_or_sell} {order.tradingsymbol} Qty:{order.quantity}")
            
            print(f"Placing {len(orders)} orders...")
            results = self.api.place_basket_orders(orders)
            successful = sum(1 for r in results if r and r.get('stat') == 'Ok')
            print(f"Basket orders placed: {successful}/{len(orders)} successful")
            
            for i, result in enumerate(results):
                if result:
                    status = result.get('stat', 'Unknown')
                    order_id = result.get('norenordno', 'No ID')
                    error_msg = result.get('emsg', '')
                    print(f"Order {i+1}: {status} - {order_id} {error_msg}")
                else:
                    print(f"Order {i+1}: Failed - No response")
                    
        except Exception as e:
            print(f"Order placement failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_basket_files(self, basket_data):
        """Save basket data to files"""
        # Save JSON
        json_file = self.file_manager.save_basket_json(basket_data)
        
        # Save and validate XML
        xml_file = self.file_manager.save_basket_xml(basket_data)
        if self.file_manager.validate_xml(xml_file):
            print("XML validated successfully")
        else:
            print("XML validation failed")
    
    def _display_order_summary(self, basket_data):
        """Display order summary"""
        print(f"Orders in basket: {len(basket_data['orders'])}")
        for order in basket_data['orders']:
            price_str = f" @ Rs.{order['price']}" if 'price' in order else ""
            print(f"  {order['action']} {order['strike']} {order['type']} x{order['qty']}{price_str}")
    
    def create_initial_basket(self, initial_spot):
        """Create the initial basket"""
        self.current_positions = self.strategy.create_initial_positions(initial_spot)
        
        # Get market prices and log initial trades
        current_prices = self._get_current_market_prices()
        total_pl = 0
        
        for position in self.current_positions:
            if position.strike in current_prices:
                market_price = current_prices[position.strike]
                # Store sell price for future P&L calculation
                self.position_prices[f"{position.strike}_{position.type}"] = market_price
                
                # Log initial SELL trade
                pl, pl_pct = self.trade_logger.log_trade(
                    position, market_price, market_price, 'SELL'
                )
                total_pl += pl
        
        # Create initial basket data
        date_str = datetime.now().strftime('%Y%m%d')
        orders = self.strategy.create_initial_orders(self.current_positions)
        
        basket_data = {
            'id': f"BASKET_{date_str}_INITIAL",
            'timestamp': datetime.now().isoformat(),
            'spotValue': initial_spot,
            'type': 'INITIAL',
            'orders': orders
        }
        
        # Process and log basket
        basket = self.create_basket(basket_data)
        self.baskets.append(basket)
        
        # Update config
        self.config_manager.update_spot_reference(initial_spot)
        self.config_manager.reset_adjustments()
        
        return basket_data
    
    def _get_current_market_prices(self):
        """Get current market prices for all positions"""
        prices = {}
        try:
            for position in self.current_positions:
                # Use Shoonya API to get current option price
                expiry = "26DEC24"  # Update with actual expiry
                symbol = f"{self.config['trading']['index']}{expiry}{position.strike}{position.type}"
                quote = self.api.get_quotes('NFO', symbol)
                if quote and 'lp' in quote:
                    prices[position.strike] = float(quote['lp'])
                else:
                    prices[position.strike] = 0.0
        except Exception as e:
            print(f"Error fetching market prices: {e}")
        
        return prices