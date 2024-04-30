import requests

from configs.msw_connector_config import (
    MUESLISWAP_API_URL,
    ORDER_BOOK_ENDPOINT,
    BASE_POLICY,
    BASE_TOKEN_NAME_HEX,
)
from bot.utils.logger import get_logger

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


def init_order_book(bot):
    """
    Initialize the order book dictionary for all selected tokens.
    """
    order_book = {}
    for token_name in bot.tokens:
        order_book[token_name] = {"Buy": [], "Sell": []}
    setattr(bot, "order_book", order_book)


def track_order_book(bot, token_name: str, token_info: dict):
    """
    Track the order book for the selected tokens.
    """
    policy_id, hexname = token_info["policy_id"], token_info["hexname"]
    buy_orders_query = (
        f"?from-policy-id={BASE_POLICY}"
        f"&from-tokenname={BASE_TOKEN_NAME_HEX}"
        f"&to-policy-id={policy_id}"
        f"&to-tokenname={hexname}"
    )
    sell_orders_query = (
        f"?from-policy-id={policy_id}"
        f"&from-tokenname={hexname}"
        f"&to-policy-id={BASE_POLICY}"
        f"&to-tokenname={BASE_TOKEN_NAME_HEX}"
    )
    try:
        logger.info(f"Tracking Buy Orders for {token_name}.")
        bot.order_book[token_name]["Buy"] = query_order_book(
            ORDER_BOOK_ENDPOINT, buy_orders_query
        )
        logger.info(f"Successfully tracked Buy Orders for {token_name}.")

        logger.info(f"Tracking Sell Orders for {token_name}.")
        bot.order_book[token_name]["Sell"] = query_order_book(
            ORDER_BOOK_ENDPOINT, sell_orders_query
        )
        logger.info(f"Successfully tracked Sell Orders for {token_name}.")
    except Exception as e:
        logger.exception(f"Order book tracking error for {token_name}: {e}")
        raise
