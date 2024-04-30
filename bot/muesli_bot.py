import time
from bot.health_check import perform_health_check
from bot.inventory_management import update_inventory
from bot.order_book_tracking import track_order_book, init_order_book
from bot.order_management import (
    update_open_positions,
    update_orders,
    init_order_tracking,
    sync_order_tracking,
)
from bot.strategy import apply_strategy, init_strategy
from bot.utils.logger import get_logger
from configs.config import KEYS_DIR, KEY_PREFIX

from bot.utils.utils import get_address
from bot.price import init_price_data

logger = get_logger(__name__)


class MuesliMarketMaker:
    """
    Main Trading Bot class.
    """

    def __init__(self, strategy_config: dict):
        self.inventory = {}
        self.open_positions = {}
        self.open_orders = {}
        self.matched_orders = {}
        self.canceled_orders = {}
        self.strategy_config = strategy_config
        self.strategy = init_strategy(strategy_config)
        self.tokens = strategy_config["tokens"]
        init_order_book(self)
        init_price_data(self)
        init_order_tracking(self)

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

                    perform_health_check(self.strategy_config["loop_interval"])
                    update_inventory(self, token_name, token_info, address)
                    track_order_book(self, token_name, token_info)
                    update_open_positions(self, address)
                    update_orders(self, address, token_name)
                    sync_order_tracking(self, token_name)
                    apply_strategy(
                        self,
                        token_name,
                        token_info,
                        address,
                        key_path,
                    )
                except Exception as e:
                    logger.exception(f"Error in main loop for {token_name}: {repr(e)}")
                    continue
            time.sleep(self.strategy_config["loop_interval"])
