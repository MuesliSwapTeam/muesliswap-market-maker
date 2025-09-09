from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from collections import deque
import statistics

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
    strategy_type = strategy_config.get("type", "market_making")
    
    if strategy_name == "standard_market_making":
        return StandardMarketMakingStrategy(strategy_config)
    elif strategy_name == "aggressive_market_making":
        return AggressiveMarketMakingStrategy(strategy_config)
    elif strategy_name == "volume_based_adaptive":
        return VolumeBasedAdaptiveStrategy(strategy_config)
    elif strategy_name == "trend_following":
        return TrendFollowingStrategy(strategy_config)
    else:
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


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, config):
        self.config = config
        self.mid_price = None
        self.price_history = deque(maxlen=config.get("price_history_length", 20))
        self.volume_history = deque(maxlen=config.get("volume_history_length", 10))
    
    def update_mid_price(self, new_price):
        """Update the mid price and maintain price history."""
        self.mid_price = new_price
        if new_price is not None:
            self.price_history.append(new_price)
    
    def update_volume(self, volume):
        """Update volume history for volume-based strategies."""
        if volume is not None:
            self.volume_history.append(volume)
    
    def calculate_volatility(self) -> float:
        """Calculate price volatility based on recent price history."""
        if len(self.price_history) < 2:
            return 0.0
        
        prices = list(self.price_history)
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        return statistics.stdev(returns) if len(returns) > 1 else 0.0
    
    def calculate_average_volume(self) -> float:
        """Calculate average volume over recent history."""
        if not self.volume_history:
            return 0.0
        return statistics.mean(self.volume_history)
    
    def check_over_refresh_threshold(self, price):
        """Checks if a given price is over the refresh threshold"""
        if self.mid_price is None:
            return False
        price_diff = abs(self.mid_price - price) / self.mid_price
        return price_diff > self.config["order_refresh_threshold"]
    
    def check_if_cancel_order(self, bot, order: Dict, token_name: str):
        """Cancel order if it moved out of the price range"""
        try:
            price = order_to_price(order)
        except Exception as e:
            logger.exception(f"Error parsing order to price: {e}")
            return False
        
        if order["txHash"] in bot.order_tracking[token_name]["canceled_orders"]:
            logger.info(f"Order {order['txHash']} already canceled.")
            return False
        elif not self.check_over_refresh_threshold(price):
            logger.info(f"Order {order['txHash']} is within the threshold.")
            return False
        else:
            logger.info(f"Order {order['txHash']} is outside the threshold, cancelling order.")
            return True
    
    def check_if_buy(self, bot, token_name, price):
        """Determine if buy order should be placed."""
        if len(bot.order_tracking[token_name]["buy_orders"].keys()) >= self.config["n_orders"]:
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
        if len(bot.order_tracking[token_name]["sell_orders"].keys()) >= self.config["n_orders"]:
            logger.info(f"Max number of sell orders reached.")
            return False
        elif self.check_over_refresh_threshold(price):
            logger.info(f"Price {price} over threshold, not placing sell order.")
            return False
        else:
            logger.info(f"Price {price} is within the threshold.")
            return True
    
    @abstractmethod
    def calculate_order_prices(self):
        """Calculate buy and sell prices based on strategy logic."""
        pass
    
    @abstractmethod
    def execute(self, bot, token_name: str, token_info: dict, address: Address, key_path: str):
        """Execute the trading strategy."""
        pass


class StandardMarketMakingStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)

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


class AggressiveMarketMakingStrategy(BaseStrategy):
    """Aggressive market making strategy with tighter spreads and dynamic adjustment."""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_delta = config.get("delta", 0.02)  # Tighter base spread
        self.volatility_multiplier = config.get("volatility_multiplier", 1.5)
        self.min_delta = config.get("min_delta", 0.005)  # Minimum spread
        self.max_delta = config.get("max_delta", 0.05)   # Maximum spread
    
    def calculate_order_prices(self):
        """Calculate prices with dynamic spread based on volatility."""
        if self.mid_price is None:
            return [], []
        
        # Adjust delta based on volatility
        volatility = self.calculate_volatility()
        adjusted_delta = min(
            max(self.base_delta * (1 + volatility * self.volatility_multiplier), self.min_delta),
            self.max_delta
        )
        
        buy_prices = []
        sell_prices = []
        for i in range(1, self.config["n_orders"] + 1):
            delta_price = self.mid_price * adjusted_delta * i
            buy_prices.append(math.floor(self.mid_price - delta_price))
            sell_prices.append(math.ceil(self.mid_price + delta_price))
        
        logger.info(f"Aggressive MM - Volatility: {volatility:.4f}, Adjusted Delta: {adjusted_delta:.4f}")
        return buy_prices, sell_prices
    
    def execute(self, bot, token_name: str, token_info: dict, address: Address, key_path: str):
        """Execute aggressive market making strategy."""
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
        
        # Cancel orders that are outside the price range
        for order in bot.open_orders:
            if self.check_if_cancel_order(bot, order, token_name):
                try:
                    canceled_order, utxos = cancel_order(order, address, key_path, utxos)
                    bot.order_tracking[token_name]["canceled_orders"].update(canceled_order)
                    del bot.order_tracking[token_name]["buy_orders"][order["txHash"]]
                    del bot.order_tracking[token_name]["sell_orders"][order["txHash"]]
                    save_order_tracking(bot, token_name)
                    logger.info(f"Order {order['txHash']} canceled.")
                except InsufficientUTxOBalanceException:
                    logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                except Exception as e:
                    log_exception(logger, "Error canceling order", e)
        
        # Place orders with aggressive pricing
        max_length = max(len(buy_prices), len(sell_prices))
        for i in range(max_length):
            if i < len(buy_prices):
                price = buy_prices[i]
                if price <= 0:
                    continue
                if self.check_if_buy(bot, token_name, price):
                    try:
                        buy_order, utxos = place_buy_order(
                            token_name, policy_id, hexname, address, amount, decimals,
                            price, key_path, utxos
                        )
                        bot.order_tracking[token_name]["buy_orders"].update(buy_order)
                        save_order_tracking(bot, token_name)
                        logger.info(f"Aggressive buy order placed: {buy_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                    except Exception as e:
                        log_exception(logger, "Error placing buy order", e)
            
            if i < len(sell_prices):
                price = sell_prices[i]
                if price <= 0:
                    continue
                if self.check_if_sell(bot, token_name, price):
                    try:
                        sell_order, utxos = place_sell_order(
                            token_name, policy_id, hexname, address, amount, decimals,
                            price, key_path, utxos
                        )
                        bot.order_tracking[token_name]["sell_orders"].update(sell_order)
                        save_order_tracking(bot, token_name)
                        logger.info(f"Aggressive sell order placed: {sell_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                    except Exception as e:
                        log_exception(logger, "Error placing sell order", e)


class VolumeBasedAdaptiveStrategy(BaseStrategy):
    """Volume-based adaptive strategy that adjusts behavior based on trading volume."""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_delta = config.get("delta", 0.05)
        self.volume_threshold_high = config.get("volume_threshold_high", 1.5)
        self.volume_threshold_low = config.get("volume_threshold_low", 0.5)
        self.high_volume_delta_multiplier = config.get("high_volume_delta_multiplier", 0.7)
        self.low_volume_delta_multiplier = config.get("low_volume_delta_multiplier", 1.3)
    
    def calculate_order_prices(self):
        """Calculate prices based on volume conditions."""
        if self.mid_price is None:
            return [], []
        
        avg_volume = self.calculate_average_volume()
        current_volume = self.volume_history[-1] if self.volume_history else 0
        
        # Adjust delta based on volume
        if current_volume > avg_volume * self.volume_threshold_high:
            # High volume - tighter spreads to capture more trades
            adjusted_delta = self.base_delta * self.high_volume_delta_multiplier
            logger.info(f"High volume detected - using tighter spreads")
        elif current_volume < avg_volume * self.volume_threshold_low:
            # Low volume - wider spreads to reduce risk
            adjusted_delta = self.base_delta * self.low_volume_delta_multiplier
            logger.info(f"Low volume detected - using wider spreads")
        else:
            # Normal volume - standard spreads
            adjusted_delta = self.base_delta
            logger.info(f"Normal volume - using standard spreads")
        
        buy_prices = []
        sell_prices = []
        for i in range(1, self.config["n_orders"] + 1):
            delta_price = self.mid_price * adjusted_delta * i
            buy_prices.append(math.floor(self.mid_price - delta_price))
            sell_prices.append(math.ceil(self.mid_price + delta_price))
        
        return buy_prices, sell_prices
    
    def execute(self, bot, token_name: str, token_info: dict, address: Address, key_path: str):
        """Execute volume-based adaptive strategy."""
        policy_id, hexname, amount, decimals = (
            token_info["policy_id"],
            token_info["hexname"],
            token_info["amount"],
            token_info["decimals"],
        )
        
        fetch_price(bot, token_name, policy_id, hexname)
        self.update_mid_price(bot.price_data[token_name]["price"])
        
        # Update volume (this would need to be implemented in the price fetching)
        # For now, we'll use a placeholder
        current_volume = 1.0  # This should be fetched from the API
        self.update_volume(current_volume)
        
        if self.mid_price is None:
            return
        
        # Get the buy and sell prices according to the strategy configuration
        buy_prices, sell_prices = self.calculate_order_prices()
        
        # Preselect UTxOs for the transactions
        utxos = CONTEXT.utxos(address)
        
        # Cancel orders that are outside the price range
        for order in bot.open_orders:
            if self.check_if_cancel_order(bot, order, token_name):
                try:
                    canceled_order, utxos = cancel_order(order, address, key_path, utxos)
                    bot.order_tracking[token_name]["canceled_orders"].update(canceled_order)
                    del bot.order_tracking[token_name]["buy_orders"][order["txHash"]]
                    del bot.order_tracking[token_name]["sell_orders"][order["txHash"]]
                    save_order_tracking(bot, token_name)
                    logger.info(f"Order {order['txHash']} canceled.")
                except InsufficientUTxOBalanceException:
                    logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                except Exception as e:
                    log_exception(logger, "Error canceling order", e)
        
        # Place orders with volume-adaptive pricing
        max_length = max(len(buy_prices), len(sell_prices))
        for i in range(max_length):
            if i < len(buy_prices):
                price = buy_prices[i]
                if price <= 0:
                    continue
                if self.check_if_buy(bot, token_name, price):
                    try:
                        buy_order, utxos = place_buy_order(
                            token_name, policy_id, hexname, address, amount, decimals,
                            price, key_path, utxos
                        )
                        bot.order_tracking[token_name]["buy_orders"].update(buy_order)
                        save_order_tracking(bot, token_name)
                        logger.info(f"Volume-adaptive buy order placed: {buy_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                    except Exception as e:
                        log_exception(logger, "Error placing buy order", e)
            
            if i < len(sell_prices):
                price = sell_prices[i]
                if price <= 0:
                    continue
                if self.check_if_sell(bot, token_name, price):
                    try:
                        sell_order, utxos = place_sell_order(
                            token_name, policy_id, hexname, address, amount, decimals,
                            price, key_path, utxos
                        )
                        bot.order_tracking[token_name]["sell_orders"].update(sell_order)
                        save_order_tracking(bot, token_name)
                        logger.info(f"Volume-adaptive sell order placed: {sell_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                    except Exception as e:
                        log_exception(logger, "Error placing sell order", e)


class TrendFollowingStrategy(BaseStrategy):
    """Trend-following strategy that places more orders in the direction of the trend."""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_delta = config.get("delta", 0.05)
        self.trend_strength_threshold = config.get("trend_strength_threshold", 0.02)
        self.trend_multiplier = config.get("trend_multiplier", 1.5)
        self.sma_period = config.get("sma_period", 10)
    
    def calculate_sma(self, period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(self.price_history) < period:
            return self.mid_price if self.mid_price else 0
        
        recent_prices = list(self.price_history)[-period:]
        return statistics.mean(recent_prices)
    
    def detect_trend(self) -> str:
        """Detect trend direction: 'up', 'down', or 'sideways'."""
        if len(self.price_history) < self.sma_period:
            return 'sideways'
        
        sma = self.calculate_sma(self.sma_period)
        current_price = self.mid_price
        
        if current_price > sma * (1 + self.trend_strength_threshold):
            return 'up'
        elif current_price < sma * (1 - self.trend_strength_threshold):
            return 'down'
        else:
            return 'sideways'
    
    def calculate_order_prices(self):
        """Calculate prices with trend bias."""
        if self.mid_price is None:
            return [], []
        
        trend = self.detect_trend()
        logger.info(f"Trend detected: {trend}")
        
        buy_prices = []
        sell_prices = []
        
        for i in range(1, self.config["n_orders"] + 1):
            base_delta_price = self.mid_price * self.base_delta * i
            
            if trend == 'up':
                # In uptrend, place more sell orders (take profit) and fewer buy orders
                buy_prices.append(math.floor(self.mid_price - base_delta_price * self.trend_multiplier))
                sell_prices.append(math.ceil(self.mid_price + base_delta_price * 0.7))
            elif trend == 'down':
                # In downtrend, place more buy orders (accumulate) and fewer sell orders
                buy_prices.append(math.floor(self.mid_price - base_delta_price * 0.7))
                sell_prices.append(math.ceil(self.mid_price + base_delta_price * self.trend_multiplier))
            else:
                # Sideways trend, use standard pricing
                buy_prices.append(math.floor(self.mid_price - base_delta_price))
                sell_prices.append(math.ceil(self.mid_price + base_delta_price))
        
        return buy_prices, sell_prices
    
    def execute(self, bot, token_name: str, token_info: dict, address: Address, key_path: str):
        """Execute trend-following strategy."""
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
        
        # Cancel orders that are outside the price range
        for order in bot.open_orders:
            if self.check_if_cancel_order(bot, order, token_name):
                try:
                    canceled_order, utxos = cancel_order(order, address, key_path, utxos)
                    bot.order_tracking[token_name]["canceled_orders"].update(canceled_order)
                    del bot.order_tracking[token_name]["buy_orders"][order["txHash"]]
                    del bot.order_tracking[token_name]["sell_orders"][order["txHash"]]
                    save_order_tracking(bot, token_name)
                    logger.info(f"Order {order['txHash']} canceled.")
                except InsufficientUTxOBalanceException:
                    logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                except Exception as e:
                    log_exception(logger, "Error canceling order", e)
        
        # Place orders with trend bias
        max_length = max(len(buy_prices), len(sell_prices))
        for i in range(max_length):
            if i < len(buy_prices):
                price = buy_prices[i]
                if price <= 0:
                    continue
                if self.check_if_buy(bot, token_name, price):
                    try:
                        buy_order, utxos = place_buy_order(
                            token_name, policy_id, hexname, address, amount, decimals,
                            price, key_path, utxos
                        )
                        bot.order_tracking[token_name]["buy_orders"].update(buy_order)
                        save_order_tracking(bot, token_name)
                        logger.info(f"Trend-following buy order placed: {buy_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                    except Exception as e:
                        log_exception(logger, "Error placing buy order", e)
            
            if i < len(sell_prices):
                price = sell_prices[i]
                if price <= 0:
                    continue
                if self.check_if_sell(bot, token_name, price):
                    try:
                        sell_order, utxos = place_sell_order(
                            token_name, policy_id, hexname, address, amount, decimals,
                            price, key_path, utxos
                        )
                        bot.order_tracking[token_name]["sell_orders"].update(sell_order)
                        save_order_tracking(bot, token_name)
                        logger.info(f"Trend-following sell order placed: {sell_order}")
                    except InsufficientUTxOBalanceException:
                        logger.info(f"Insufficient UTxOs. Await previous txs or add more funds")
                    except Exception as e:
                        log_exception(logger, "Error placing sell order", e)

