import requests
import json
from typing import List, Dict

from pycardano import Address

from configs.config import (
    KEY_PREFIX,
    KEYS_DIR,
    ORDER_TRACKING_DIR,
    LOCAL_ORDER_TRACKING_FILE,
    ONCHAIN_ORDER_TRACKING_FILE,
    ORDER_TIMEOUT,
)
from configs.msw_connector_config import (
    MUESLISWAP_API_URL,
    OPEN_POSITIONS_ENDPOINT,
    ORDERS_ENDPOINT,
)
from bot.utils.logger import get_logger
from bot.utils.utils import get_address, get_current_block_height, get_tx_block_height
from bot.utils.order_utils import get_order_type, format_order

logger = get_logger(__name__)


def init_order_tracking(bot) -> Dict:
    """
    Initialize the order tracking information.
    """
    order_tracking = {}
    for token_name in bot.tokens:
        order_tracking_file = ORDER_TRACKING_DIR.joinpath(
            f"{token_name}_{LOCAL_ORDER_TRACKING_FILE}"
        )
        order_tracking.update(
            {token_name: load_order_tracking_file(order_tracking_file, token_name)}
        )
        key_path = KEYS_DIR.joinpath(f"{KEY_PREFIX}{token_name}")
    setattr(bot, "order_tracking", order_tracking)
    for token_name in bot.tokens:
        save_order_tracking(bot, token_name)
        address = get_address(key_path, token_name)
        # Update the bot's onchain order tracking information
        update_orders(bot, address, token_name)
        # Sync the local order tracking information with the onchain data
        sync_order_tracking(bot, token_name)


def load_order_tracking_file(file_name: str, token_name: str) -> Dict:
    """Load the order tracking information from a file."""
    try:
        with open(file_name, "r") as file:
            order_tracking = json.load(file)
    except Exception:
        logger.info(
            f"Order tracking file not found for {token_name}. Creating a new one."
        )
        order_tracking = {
            "buy_orders": {},
            "sell_orders": {},
            "canceled_orders": {},
        }
    else:
        # Ensure all keys are present
        required_keys = ["buy_orders", "sell_orders", "canceled_orders"]
        for key in required_keys:
            if key not in order_tracking:
                logger.info(
                    f"Key '{key}' missing in order tracking for {token_name}. Initializing."
                )
                order_tracking[key] = {}
    return order_tracking


def sync_order_tracking(bot, token_name: str):
    """Synchronize local order tracking with onchain data."""
    # Retrieve onchain and local order tracking data
    local_tracking = bot.order_tracking[token_name]
    onchain_orders = bot.open_orders
    onchain_orders_hashes = [order["txHash"] for order in onchain_orders]
    for order_type in ["buy", "sell"]:
        local_orders = local_tracking[f"{order_type}_orders"]
        synced_orders = {}
        # Remove expired local orders
        for txHash, order_details in local_orders.items():
            # Query tx_height if not present
            tx_height = order_details.get("tx_height", None)
            if not tx_height:
                tx_height = get_tx_block_height(txHash)
                local_orders[txHash]["tx_height"] = tx_height
            # Check if the order is not in the onchain data and has expired
            if txHash not in onchain_orders_hashes:
                current_height = get_current_block_height()
                if (
                    tx_height
                    and current_height
                    and current_height - tx_height > ORDER_TIMEOUT
                ):
                    logger.info(f"Removing expired {order_type} order: {txHash}")
                else:
                    # Either not expired or error querying tx_height or current_height
                    synced_orders[txHash] = order_details
            else:
                order_details["tx_height"] = tx_height
                synced_orders[txHash] = order_details

        # Add missing onchain orders to local tracking
        for onchain_order in onchain_orders:
            onchain_order_type = get_order_type(onchain_order)
            if onchain_order_type == order_type:
                txHash = onchain_order["txHash"]
                if (
                    onchain_order["txHash"] not in synced_orders
                    and txHash not in local_tracking["canceled_orders"]
                ):
                    synced_orders.update(format_order(onchain_order))
                    logger.info(
                        f"Adding missing {order_type} order from onchain: {txHash}"
                    )
        # Update local tracking
        local_tracking[f"{order_type}_orders"] = synced_orders
    # Update order tracking and save to file
    bot.order_tracking[token_name] = local_tracking
    save_order_tracking(bot, token_name)


def save_order_tracking(bot, token_name):
    """Save the updated order tracking to a file."""
    with open(
        ORDER_TRACKING_DIR / f"{token_name}_{LOCAL_ORDER_TRACKING_FILE}", "w"
    ) as file:
        json.dump(bot.order_tracking[token_name], file, indent=4)
        logger.info(f"Saved updated order tracking for {token_name}.")


def update_open_positions(bot, address: Address):
    """
    Display open positions via open-positions endpoint.
    """
    skh = address.staking_part.to_primitive().hex()
    content = f"?skh={skh}&wallet={address.to_primitive().hex()}"
    track_order_query = f"{MUESLISWAP_API_URL}{OPEN_POSITIONS_ENDPOINT}{content}"
    try:
        response = requests.get(track_order_query)
        if response.status_code == 200:
            response_json = response.json()
            open_positions = response_json.get("orders", {})
            setattr(bot, "open_positions", open_positions)
            logger.info(f"Own orders tracked successfully: {bot.open_positions}")
        else:
            logger.error(f"Failed to track orders. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network exception occurred: {e}")

    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")


def update_orders(bot, address: Address, token_name: str):
    """
    Updates the bot's orders based on type: 'open', 'matched', or 'canceled'.
    """
    update_order_type(bot, address, "open")
    update_order_type(bot, address, "matched")
    update_order_type(bot, address, "canceled")
    onchain_order_tracking_file = ORDER_TRACKING_DIR.joinpath(
        f"{token_name}_{ONCHAIN_ORDER_TRACKING_FILE}"
    )
    with open(onchain_order_tracking_file, "w") as file:
        json.dump(
            {
                "open_orders": [format_order(order) for order in bot.open_orders],
                "matched_orders": [format_order(order) for order in bot.matched_orders],
                "canceled_orders": [
                    format_order(order) for order in bot.canceled_orders
                ],
            },
            file,
            indent=4,
        )


def update_order_type(bot, address: Address, order_type: str):
    """
    Updates the bot's orders based on type: 'open', 'matched', or 'canceled'.
    """
    stake_key_hash = address.staking_part.to_primitive().hex()
    orders = get_orders(stake_key_hash, order_type, **{f"{order_type}_orders": True})
    setattr(bot, f"{order_type}_orders", orders)


def get_orders(
    stake_key_hash: str,
    order_type: str,
    canceled_orders: bool = False,
    open_orders: bool = False,
    matched_orders: bool = False,
    only_v2: bool = False,
) -> List:
    """
    Fetches orders from MuesliSwap API orders endpoint based on order type.
    """
    params = {
        "stake-key-hash": stake_key_hash,
        "canceled": "y" if canceled_orders else "n",
        "open": "y" if open_orders else "n",
        "matched": "y" if matched_orders else "n",
        "v2_only": "y" if only_v2 else "n",
    }
    query = "&".join(f"{key}={value}" for key, value in params.items())
    order_query = f"{MUESLISWAP_API_URL}{ORDERS_ENDPOINT}?{query}"
    try:
        response = requests.get(order_query)
        if response.status_code == 200:
            response_json = response.json()
            logger.info(f"Fetched {order_type}_orders successfully")
            return response_json
        else:
            logger.error(
                f"Failed to fetch {order_type} orders. Status code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Network exception occurred: {e}")
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
    return []
