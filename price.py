import requests

from config import MUESLISWAP_API_URL, PRICE_ENDPOINT, BASE_POLICY, BASE_TOKEN_NAME_HEX
from logger import get_logger

logger = get_logger(__name__)


def fetch_price(bot, token_name: str, policy_id: str, hexname: str):
    """
    Fetch the mid-price of the token pair from the API endpoint.
    """
    query= f"?base-policy-id={BASE_POLICY}&base-tokenname={BASE_TOKEN_NAME_HEX}&quote-policy-id={policy_id}&quote-tokenname={hexname}"
    try:
        logger.info(f"Fetching price data for {token_name}.")
        bot.price_data[token_name] = query_price_endpoint(PRICE_ENDPOINT, query)
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


def init_price_data(TOKENS: list[str]):
    """
    Initialize the price data dictionary for all selected tokens.
    """
    price_data = {}
    for token_name in TOKENS:
        price_data[token_name] = {}
    return price_data
