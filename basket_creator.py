"""
Shoonya 6-Leg Strangle Basket Creator
Main execution script for monitoring spot price and creating baskets automatically
"""

import time
from datetime import datetime
from config import CONFIG
from basket_manager import BasketManager
from file_manager import FileManager

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("Starting Shoonya Basket Monitor")
    print("="*60)
    
    # Initialize components
    basket_manager = BasketManager(CONFIG)
    config_manager = basket_manager.config_manager
    
    # Date validation
    if config_manager.is_closed_today():
        print("Already closed for today. Exiting.")
        return
    
    # Login to Shoonya
    if not basket_manager.initialize():
        print("Failed to login. Exiting.")
        return
    
    # Strategy logic based on config state
    if config_manager.should_initiate():
        print("Initiating strategy...")
        spot_value = basket_manager.api.get_spot_price(CONFIG['trading']['index'])
        if spot_value:
            basket_manager.create_initial_basket(spot_value)
            print(f"Strategy initiated at spot: {spot_value}")
        else:
            print("Failed to get spot price. Exiting.")
            return
    
    elif config_manager.should_adjust():
        print("Adjustment mode...")
        _run_adjustment_mode(basket_manager, config_manager)
    
    elif config_manager.should_monitor():
        print("Monitoring mode...")
        _run_monitoring_mode(basket_manager, config_manager)
    
    else:
        print("No action required based on current config state.")

def _run_adjustment_mode(basket_manager, config_manager):
    """Run adjustment mode"""
    print(f"Max adjustments remaining: {config_manager.get_max_adjustment()}")
    
    try:
        while config_manager.get_max_adjustment() > 0:
            current_time = datetime.now().strftime('%H:%M:%S')
            
            if current_time > CONFIG['trading']['session_end']:
                print("Trading session ended")
                config_manager.reset_for_next_day()
                break
            
            spot_value = basket_manager.api.get_spot_price(CONFIG['trading']['index'])
            if spot_value:
                print(f"[{current_time}] Spot: {spot_value} | Ref: {config_manager.get_spot_reference()}")
                basket_manager.check_and_adjust(spot_value)
            
            time.sleep(CONFIG['check_interval'])
            
    except KeyboardInterrupt:
        print("Monitoring stopped")

def _run_monitoring_mode(basket_manager, config_manager):
    """Run monitoring mode"""
    print("Monitoring for exit conditions...")
    
    try:
        while True:
            current_time = datetime.now().strftime('%H:%M:%S')
            
            if current_time >= CONFIG['trading']['session_end']:
                print("Market close - Resetting for next day")
                config_manager.reset_for_next_day()
                break
            
            spot_value = basket_manager.api.get_spot_price(CONFIG['trading']['index'])
            if spot_value:
                # Check for force exit conditions
                spot_reference = config_manager.get_spot_reference()
                if spot_reference and abs(spot_value - spot_reference) >= CONFIG['trading']['force_exit_movement']:
                    print(f"Force exit triggered: {abs(spot_value - spot_reference):.0f} point movement")
                    basket_manager._force_exit_all_positions(spot_value)
                    break
                
                # Check P&L based exit
                if basket_manager._check_loss_limit(spot_value):
                    break
            
            time.sleep(CONFIG['check_interval'])
            
    except KeyboardInterrupt:
        print("Monitoring stopped")



if __name__ == '__main__':
    main()