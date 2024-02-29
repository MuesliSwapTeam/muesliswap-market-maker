import requests

from config import MUESLISWAP_API_URL, ORDER_BOOK_ENDPOINT, BASE_POLICY, BASE_TOKEN_NAME_HEX
from utils import parse_token_pid
from logger import get_logger

logger = get_logger(__name__)


def query_order_book(endpoint: str, query: str):
    """
    Send a request to the Muesliswap API and return the response.
    """
    try:
        response = requests.get(f"{MUESLISWAP_API_URL}{endpoint}{query}")
        response.raise_for_status()
        return response.json().get("orders", {})
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Network Error: {e}")
        raise
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        raise


def init_order_book(TOKENS: list[str]) -> dict:
    """
    Initialize the order book dictionary for all selected tokens.
    """
    order_book = {}
    for token_name in TOKENS:
        order_book[token_name] = {'Buy': [], 'Sell': []}
    return order_book


def track_order_book(bot, token_name: str, policy_id: str, hexname: str):
    """
    Track the order book for the selected tokens.
    """
    buy_orders_query = f"?from-policy-id={BASE_POLICY}&from-tokenname={BASE_TOKEN_NAME_HEX}&to-policy-id={policy_id}&to-tokenname={hexname}"
    sell_orders_query = f"?from-policy-id={policy_id}&from-tokenname={hexname}&to-policy-id={BASE_POLICY}&to-tokenname={BASE_TOKEN_NAME_HEX}"
    try:
        logger.info(f"Tracking Buy Orders for {token_name}.")
        bot.order_book[token_name]['Buy'] = query_order_book(ORDER_BOOK_ENDPOINT, buy_orders_query)
        logger.info(f"Successfully tracked Buy Orders for {token_name}.")

        logger.info(f"Tracking Sell Orders for {token_name}.")
        bot.order_book[token_name]['Sell'] = query_order_book(ORDER_BOOK_ENDPOINT, sell_orders_query)
        logger.info(f"Successfully tracked Sell Orders for {token_name}.")
    except Exception as e:
        logger.exception(f"Order book tracking error for {token_name}: {e}")
        raise
