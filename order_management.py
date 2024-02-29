import requests

from config import MUESLISWAP_API_URL, OPEN_POSITIONS_ENDPOINT, KEYS_DIR, KEY_PREFIX
from utils import get_address
from logger import get_logger

logger = get_logger(__name__)


def track_own_orders(bot, token_name: str, policy_id: str, hexname: str, address: str):
    """
    Track the bot's own orders.
    """
    key_path = KEYS_DIR.joinpath(f"{KEY_PREFIX}{token_name}")
    address = get_address(key_path, token_name)
    try:
        # TODO fully integrate with the Muesliswap API
        track_order_query = f"{MUESLISWAP_API_URL}{OPEN_POSITIONS_ENDPOINT}"
        response = requests.get(f"{MUESLISWAP_API_URL}{OPEN_POSITIONS_ENDPOINT}")
        bot.active_orders = response.json()
        logger.info("Own orders tracked successfully.")
    except Exception as e:
        logger.exception(f"Error tracking own orders: {e}")
        raise
