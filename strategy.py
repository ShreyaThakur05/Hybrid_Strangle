"""
6-Leg Strangle strategy logic and position management
"""

import time
from models import Position

class StrangleStrategy:
    """6-Leg Strangle strategy implementation"""
    
    def __init__(self, quantity=50):
        self.quantity = quantity
    
    def create_initial_positions(self, reference_price):
        """Create initial 6-leg strangle positions in strict execution order"""
        basket_id = f"BASKET_{int(time.time())}"
        
        # Round to nearest 50 for NIFTY strikes
        atm_strike = self._round_to_strike(reference_price)
        
        # Strict order: Spot first, then ±100, then ±200
        positions = [
            # 1. ATM orders
            Position('-1', atm_strike, 'PE', self.quantity, basket_id),  # ATM PE
            Position('+1', atm_strike, 'CE', self.quantity, basket_id),  # ATM CE
            
            # 2. ±100 strike orders
            Position('-2', atm_strike - 100, 'PE', self.quantity, basket_id),  # -100 PE
            Position('+2', atm_strike + 100, 'CE', self.quantity, basket_id),  # +100 CE
            
            # 3. ±200 strike orders
            Position('-3', atm_strike - 200, 'PE', self.quantity, basket_id),  # -200 PE
            Position('+3', atm_strike + 200, 'CE', self.quantity, basket_id),  # +200 CE
        ]
        
        return positions
    
    def _round_to_strike(self, price, strike_interval=100):
        """Round price to nearest valid strike price"""
        return round(price / strike_interval) * strike_interval
    
    def calculate_adjustment_needed(self, current_spot, reference_spot, threshold=100):
        """Check if adjustment is needed based on spot movement"""
        movement = current_spot - reference_spot
        return abs(movement) >= threshold, movement
    
    def calculate_new_reference(self, current_reference, movement, block_size=100):
        """Calculate new reference price after adjustment"""
        blocks_moved = int(movement / block_size)
        return current_reference + (blocks_moved * block_size)
    
    def find_positions_to_adjust(self, current_positions, target_positions):
        """Find positions to close and open for adjustment"""
        existing_strikes = {f"{p.strike}_{p.type}" for p in current_positions}
        target_strikes = {f"{p.strike}_{p.type}" for p in target_positions}
        
        to_close = [p for p in current_positions 
                   if f"{p.strike}_{p.type}" not in target_strikes]
        to_open = [p for p in target_positions 
                  if f"{p.strike}_{p.type}" not in existing_strikes]
        
        return to_close, to_open
    
    def create_adjustment_orders(self, to_close, to_open, remark):
        """Create orders for position adjustment"""
        orders = []
        
        # Close orders (BUY back short positions)
        for position in to_close:
            orders.append({
                'action': 'BUY',
                'strike': position.strike,
                'type': position.type,
                'qty': position.qty,
                'index': position.index,
                'remark': remark
            })
        
        # Open orders (SELL new positions)
        for position in to_open:
            orders.append({
                'action': 'SELL',
                'strike': position.strike,
                'type': position.type,
                'qty': position.qty,
                'index': position.index,
                'remark': remark
            })
        
        return orders
    
    def create_initial_orders(self, positions):
        """Create initial SELL orders in strict execution order"""
        # Orders must maintain the exact position order for XML execution sequence
        return [
            {
                'action': 'SELL',
                'strike': p.strike,
                'type': p.type,
                'qty': p.qty,
                'index': p.index,
                'remark': p.remark,
                'execution_order': i + 1  # Track execution sequence
            } for i, p in enumerate(positions)
        ]