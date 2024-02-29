import logging
import os
from datetime import datetime

from config import LOGS_DIR, DEBUG

def configure_logger():
    """
    Configure the logger.
    """
    # Create logs directory if not exists
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    # Current date for log file naming
    current_date = datetime.now().strftime('%Y-%m-%d')
    # Config for logging
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s' 
                            if DEBUG else '%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(f'{LOGS_DIR}/market_bot_log_{current_date}.log'),
                            logging.StreamHandler()
                        ])

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
