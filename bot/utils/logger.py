import logging
from datetime import datetime

from configs.config import LOGS_DIR, DEBUG


def configure_logger():
    """
    Configure the logger.
    """
    # Create logs directory if not exists
    LOGS_DIR.mkdir(exist_ok=True)

    # Current date for log file naming
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Config for logging
    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format=(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            if DEBUG
            else "%(asctime)s - %(levelname)s - %(message)s"
        ),
        handlers=[
            logging.FileHandler(f"{LOGS_DIR}/market_bot_log_{current_date}.log"),
            logging.StreamHandler(),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Returns logger with the given name.
    """
    # Get logger
    logger = logging.getLogger(name)

    # Configure logger
    configure_logger()

    logger.propagate = True
    return logger


def log_exception(logger, msg, error):
    """Log exception depending on level"""
    if DEBUG:
        logger.debug(f"{msg} {error}")
    else:
        logger.info(f"{msg}")
