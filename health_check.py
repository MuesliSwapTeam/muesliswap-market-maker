import requests

from config import MUESLISWAP_API_URL, HEALTH_CHECK_ENDPOINT
from logger import get_logger

logger = get_logger(__name__)

def perform_health_check():
    """
    Perform a health check on the API and return the response.
    """
    try:
        response = requests.get(f"{MUESLISWAP_API_URL}{HEALTH_CHECK_ENDPOINT}")
        logger.info("Health check performed successfully.")
        return response.text
    except Exception as e:
        logger.exception(f"Health check error: {e}")
        raise
