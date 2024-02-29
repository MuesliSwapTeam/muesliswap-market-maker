from pycardano import Address

from price import fetch_price
from logger import get_logger
from transactions import place_buy_order, place_sell_order, cancel_order

logger = get_logger(__name__)


def init_strategy(strategy_config: dict):
    """
    Initialize the trading strategy based on the configuration.
    """
    strategy_name = strategy_config.get('name')
    if strategy_name == 'standard_market_making':
        return StandardMarketMakingStrategy(strategy_config)
    # Add other strategies here as needed
    raise ValueError(f"Unknown strategy: {strategy_name}")


def apply_strategy(bot, token_name: str, policy_id: str, hexname: str, amount: str, address: Address, key_path: str):
    """
    Apply the trading strategy.
    """
    try:
        fetch_price(bot, token_name, policy_id, hexname)
        bot.strategy.update_mid_price(bot.price_data[token_name]["price"])
        bot.strategy.execute(bot.active_orders, token_name, policy_id, hexname, amount, address, key_path)
    except Exception as e:
        logger.exception(f"Strategy application error: {e}")
        raise


class StandardMarketMakingStrategy:
    def __init__(self, config):
        """Initialize the strategy with the given configuration."""
        self.config = config
        self.mid_price = None


    def update_mid_price(self, new_price):
        """Update the mid price of the strategy."""
        self.mid_price = new_price


    def calculate_order_prices(self):
        """Calculate and return lists of buy and sell prices."""
        buy_prices = []
        sell_prices = []
        for i in range(1, self.config['n_orders'] + 1):
            delta_price = self.mid_price * self.config['delta'] * i
            buy_prices.append(self.mid_price - delta_price)
            sell_prices.append(self.mid_price + delta_price)
        return buy_prices, sell_prices
    
    
    def execute(self, active_orders, token_name: str, policy_id: str, hexname: str, amount: str, address: Address, key_path: str):
        """Execute the strategy. TODO: Integrate with Muesliswap"""
        if self.mid_price is None:
            return
        
        # Calculate buy and sell prices
        buy_prices, sell_prices = self.calculate_order_prices()
        
        # Cancel existing orders if conditions are met
        for order in active_orders:
            if self.check_if_cancel_order(order):
                cancel_order(order['tx_id'], address, key_path)

        # Place new buy orders
        for price in buy_prices:
            if self.check_if_buy(price):
                place_buy_order(token_name, policy_id, hexname, address, amount, price, key_path)

        # Place new sell orders
        for price in sell_prices:
            if self.check_if_sell(price):
                place_sell_order(token_name, policy_id, hexname, address, amount, price, key_path)
                
                
    def check_if_cancel_order(self, order):
        return False
    
    
    def check_if_buy(self, price):
        return False
    
    
    def check_if_sell(self, price):
        return False
