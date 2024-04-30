import requests

from configs.msw_connector_config import (
    MUESLISWAP_API_URL,
    PRICE_ENDPOINT,
    BASE_POLICY,
    BASE_TOKEN_NAME_HEX,
)
from bot.utils.logger import get_logger

logger = get_logger(__name__)


def fetch_price(bot, token_name: str, policy_id: str, hexname: str):
    """
    Fetch the mid-price of the token pair from the API endpoint.
    """
    query = f"?base-policy-id={BASE_POLICY}&base-tokenname={BASE_TOKEN_NAME_HEX}&quote-policy-id={policy_id}&quote-tokenname={hexname}"
    try:
        logger.info(f"Fetching price data for {token_name}.")
        price_data = query_price_endpoint(PRICE_ENDPOINT, query)
        bot.price_data[token_name] = process_price_data(price_data)
        logger.info(f"Successfully fetched price data for {token_name}.")
    except Exception as e:
        logger.exception(f"Price fetching error for {token_name}: {e}")
        raise


def query_price_endpoint(endpoint: str, query: str):
    """
    Send a request to the Muesliswap API and return the response.
    """
    try:
        response = requests.get(f"{MUESLISWAP_API_URL}{endpoint}{query}")
        response.raise_for_status()

        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Network Error: {e}")
        raise
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        raise


def process_price_data(response: dict):
    """
    Process price data and return prices & spread
    """
    required_keys = ["quoteDecimalPlaces", "askPrice", "bidPrice", "price"]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing key in response: {key}")

    try:
        token_decimals = int(response["quoteDecimalPlaces"])
        ask_price = float(response["askPrice"])
        bid_price = float(response["bidPrice"])
        price = float(response["price"])

        ask_price_int = round(ask_price * 10**token_decimals)
        bid_price_int = round(bid_price * 10**token_decimals)
        price_int = round(price * 10**token_decimals)
        spread_int = round((ask_price - bid_price) * 10**token_decimals)

        return {
            "askPrice": ask_price_int,
            "bidPrice": bid_price_int,
            "price": price_int,
            "spread": spread_int,
        }

    except (TypeError, ValueError) as e:
        raise ValueError(f"Error processing price data: {e}")


def init_price_data(bot):
    """
    Initialize the price data dictionary for all selected tokens.
    """
    setattr(bot, "price_data", {})
    for token_name, token_info in bot.tokens.items():
        fetch_price(bot, token_name, token_info["policy_id"], token_info["hexname"])
