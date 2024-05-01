from typing import Dict

from pycardano import Address, InsufficientUTxOBalanceException
import math

from bot.price import fetch_price
from bot.utils.logger import get_logger, log_exception
from bot.transactions import place_buy_order, place_sell_order, cancel_order
from bot.order_management import save_order_tracking
from bot.utils.order_utils import order_to_price
from configs.config import CONTEXT

logger = get_logger(__name__)


def init_strategy(strategy_config: dict):
    """
    Initialize the trading strategy based on the configuration.
    """
    strategy_name = strategy_config.get("name")
    if strategy_name == "standard_market_making":
        return StandardMarketMakingStrategy(strategy_config)
    # Add other strategies here as needed
    raise ValueError(f"Unknown strategy: {strategy_name}")


def apply_strategy(
    bot,
    token_name: str,
    token_info: dict,
    address: Address,
    key_path: str,
):
    """
    Apply the trading strategy.
    """
    try:
        bot.strategy.execute(bot, token_name, token_info, address, key_path)
    except Exception as e:
        logger.exception(f"Strategy application error: {e}")
        raise


class StandardMarketMakingStrategy:
    def __init__(self, config):
        self.config = config
        self.mid_price = None

    def update_mid_price(self, new_price):
        self.mid_price = new_price

    def calculate_order_prices(self):
        buy_prices = []
        sell_prices = []
        for i in range(1, self.config["n_orders"] + 1):
            delta_price = self.mid_price * self.config["delta"] * i
            buy_prices.append(math.floor(self.mid_price - delta_price))
            sell_prices.append(math.ceil(self.mid_price + delta_price))
        return buy_prices, sell_prices

    def execute(
        self,
        bot,
        token_name: str,
        token_info: dict,
        address: Address,
        key_path: str,
    ):
        policy_id, hexname, amount, decimals = (
            token_info["policy_id"],
            token_info["hexname"],
            token_info["amount"],
            token_info["decimals"],
        )
        fetch_price(bot, token_name, policy_id, hexname)
        self.update_mid_price(bot.price_data[token_name]["price"])
        if self.mid_price is None:
            return

        # Get the buy and sell prices according to the strategy configuration
        buy_prices, sell_prices = self.calculate_order_prices()

        # Preselect UTxOs for the transactions
        utxos = CONTEXT.utxos(address)
        # We cancel orders that are outside the price range
        for order in bot.open_orders:
            if self.check_if_cancel_order(bot, order, token_name):
                try:
                    # Create and submit tx
                    canceled_order, utxos = cancel_order(
                        order, address, key_path, utxos
                    )
                    # Add canceled order to local order tracking to avoid cancelling it again
                    bot.order_tracking[token_name]["canceled_orders"].update(
                        canceled_order
                    )
                    # Remove order from locla open open orders
                    del bot.order_tracking[token_name]["buy_orders"][order["txHash"]]
                    del bot.order_tracking[token_name]["sell_orders"][order["txHash"]]
                    # Save order tracking files locally
                    save_order_tracking(bot, token_name)
                    logger.info(f"Order {order['txHash']} canceled.")
                except InsufficientUTxOBalanceException:
                    logger.info(
                        f"Insufficient UTxOs. Await previous txs or add more funds"
                    )
                except Exception as e:
                    log_exception(logger, "Error canceling order", e)

        # Alternate between placing buy and sell orders
        max_length = max(len(buy_prices), len(sell_prices))
        for i in range(max_length):
            # Place buy order if within range of buy_prices
            if i < len(buy_prices):
                price = buy_prices[i]
                if price <= 0:
                    logger.info("Skipping, price cannot be zero or negative")
                    continue
                if self.check_if_buy(bot, token_name, price):
                    try:
                        # Create and submit buy order transaction
                        buy_order, utxos = place_buy_order(
                            token_name,
                            policy_id,
                            hexname,
                            address,
                            amount,
                            decimals,
                            price,
                            key_path,
                            utxos,
                        )
                        # Add buy order to local order tracking
                        bot.order_tracking[token_name]["buy_orders"].update(buy_order)
                        # Save order tracking files locally
                        save_order_tracking(bot, token_name)
                        logger.info(f"Buy order placed: {buy_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(
                            f"Insufficient UTxOs. Await previous txs or add more funds"
                        )
                    except Exception as e:
                        log_exception(logger, "Error placing buy order", e)

            # Place sell order if within range of sell_prices
            if i < len(sell_prices):
                price = sell_prices[i]
                if price <= 0:
                    logger.info("Skipping, price cannot be zero or negative")
                    continue
                if self.check_if_sell(bot, token_name, price):
                    try:
                        # Create and submit sell order transaction
                        sell_order, utxos = place_sell_order(
                            token_name,
                            policy_id,
                            hexname,
                            address,
                            amount,
                            decimals,
                            price,
                            key_path,
                            utxos,
                        )
                        # Add sell order to local order tracking
                        bot.order_tracking[token_name]["sell_orders"].update(sell_order)
                        # Save order tracking files locally
                        save_order_tracking(bot, token_name)
                        logger.info(f"Sell order placed: {sell_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(
                            f"Insufficient UTxOs. Await previous txs or add more funds"
                        )
                    except Exception as e:
                        log_exception(logger, "Error placing sell order", e)

    def check_if_cancel_order(self, bot, order: Dict, token_name: str):
        """Cancel order if it moved out of the price range"""
        # Obtain price of the order
        try:
            price = order_to_price(order)
        except Exception as e:
            logger.exception(f"Error parsing order to price: {e}")
            return False
        # Check if order is already canceled
        if order["txHash"] in bot.order_tracking[token_name]["canceled_orders"]:
            logger.info(f"Order {order['txHash']} already canceled.")
            return False
        # Check if order is within the threshold
        elif not self.check_over_refresh_threshold(price):
            logger.info(f"Order {order['txHash']} is within the threshold.")
            return False
        else:
            logger.info(
                f"Order {order['txHash']} is outside the threshold, cancelling order."
            )
            return True

    def check_if_buy(self, bot, token_name, price):
        """Determine if buy order should be placed."""
        if (
            len(bot.order_tracking[token_name]["buy_orders"].keys())
            >= self.config["n_orders"]
        ):
            logger.info(f"Max number of buy orders reached.")
            return False
        elif self.check_over_refresh_threshold(price):
            logger.info(f"Price {price} over threshold, not placing buy order.")
            return False
        else:
            logger.info(f"Price {price} is within the threshold.")
            return True

    def check_if_sell(self, bot, token_name, price):
        """Determine if a sell order should be placed."""
        if (
            len(bot.order_tracking[token_name]["sell_orders"].keys())
            >= self.config["n_orders"]
        ):
            logger.info(f"Max number of sell orders reached.")
            return False
        elif self.check_over_refresh_threshold(price):
            logger.info(f"Price {price} over threshold, not placing sell order.")
            return False
        else:
            logger.info(f"Price {price} is within the threshold.")
            return True

    def check_over_refresh_threshold(self, price):
        "Checks if a given price is over the refresh threshold"
        price_diff = abs(self.mid_price - price) / self.mid_price
        return price_diff > self.config["order_refresh_threshold"]
