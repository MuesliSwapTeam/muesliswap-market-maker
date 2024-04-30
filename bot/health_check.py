import requests
import time

from configs.msw_connector_config import (
    MUESLISWAP_API_URL,
    MUESLISWAP_ONCHAIN_URL,
    HEALTH_CHECK_ENDPOINT,
)
from bot.utils.logger import get_logger

logger = get_logger(__name__)


def perform_health_check(loop_interval):
    """
    Perform a health check on the API & onchain and retry if one is unhealthy.
    """
    urls = {
        "API": f"{MUESLISWAP_API_URL}{HEALTH_CHECK_ENDPOINT}",
        "Onchain": f"{MUESLISWAP_ONCHAIN_URL}{HEALTH_CHECK_ENDPOINT}",
    }
    for service, url in urls.items():
        while True:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    logger.info(
                        f"{service} health check successful: {response.status_code}"
                    )
                    break
                else:
                    logger.warning(
                        f"{service} health check failed with status: {response.status_code}. Retrying..."
                    )
                    time.sleep(loop_interval)
            except requests.exceptions.RequestException as e:
                logger.warning(f"{service} connection error: {e}. Retrying...")
                time.sleep(loop_interval)
            except Exception as e:
                logger.warning(f"{service} unexpected error: {e}. Retrying...")
                retry_count += 1
                time.sleep(loop_interval)
