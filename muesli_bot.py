import time
from health_check import perform_health_check
from inventory_management import check_inventory
from order_book_tracking import track_order_book, init_order_book
from order_management import track_own_orders
from strategy import apply_strategy, init_strategy
from logger import get_logger
from config import KEYS_DIR, KEY_PREFIX
from utils import get_address
from price import init_price_data

logger = get_logger(__name__)


class MuesliMarketMaker:
    """
    Main Trading Bot class.
    """
    def __init__(self, strategy_config: dict):
        self.inventory = {}
        self.active_orders = {}
        self.strategy_config = strategy_config
        self.strategy = init_strategy(strategy_config)
        self.tokens = strategy_config['tokens']
        self.order_book = init_order_book(self.tokens)
        self.price_data = init_price_data(self.tokens)


    def run_main_loop(self):
        """
        Run the main loop of the bot.
        """
        logger.info("Starting the main loop of the trading bot.")
        while True:
            for token_name, token_info in self.tokens.items():
                try:
                    key_path = KEYS_DIR.joinpath(f"{KEY_PREFIX}{token_name}")
                    address = get_address(key_path, token_name)
                    logger.info(f"Processing token: {token_name}")

                    perform_health_check()
                    check_inventory(self, token_name, token_info['policy_id'], token_info['hexname'], address)
                    track_order_book(self, token_name, token_info['policy_id'], token_info['hexname'])
                    track_own_orders(self, token_name, token_info['policy_id'], token_info['hexname'], address)
                    apply_strategy(self, token_name, token_info['policy_id'], token_info['hexname'], token_info['amount'], address, key_path)

                except Exception as e:
                    logger.exception(f"Error in main loop for {token_name}: {repr(e)}")
                    continue
            time.sleep(self.strategy_config['loop_interval'])
            