import yaml
from typing import Tuple, Dict 

from pycardano import (
    PaymentVerificationKey,
    PaymentSigningKey,
    Address,
)

from configs.config import (
    KEYS_DIR,
    NETWORK,
    STRATEGY_FILE,
    KEY_PREFIX,
    ORDER_TRACKING_DIR,
    CONTEXT,
)

from bot.utils.gen_wallet import create_signing_key

from bot.utils.logger import get_logger, log_exception

logger = get_logger(__name__)


def get_signing_info(
    name: str,
) -> Tuple[PaymentVerificationKey, PaymentSigningKey, Address]:
    """
    Extract the signing info from the key files.
    """
    try:
        skey_path = str(KEYS_DIR.joinpath(f"{name}.skey"))
        payment_skey = PaymentSigningKey.load(skey_path)
        payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
        payment_address = Address(payment_vkey.hash(), network=NETWORK)
        return payment_vkey, payment_skey, payment_address
    except FileNotFoundError:
        logger.error(f"Signing key file not found for {name}")
        raise
    except Exception as e:
        logger.exception(f"Error loading signing info for {name}: {e}")
        raise


def get_address(name: str, token_name: str) -> Address:
    """
    Get the wallet address for the token.
    """
    try:
        with open(KEYS_DIR.joinpath(f"{name}.addr"), "r") as f:
            address = Address.from_primitive(f.read().strip())
        return address
    except FileNotFoundError:
        logger.error(
            f"Address file not found for {token_name}. You need to create a wallet first."
        )
        raise
    except Exception as e:
        logger.exception(f"Error reading address for {token_name}: {e}")
        raise


def load_strategy_config() -> Dict:
    """
    Load the strategy configuration from the YAML file.
    """
    try:
        with open(f"configs/strategies/{STRATEGY_FILE}", "r") as file:
            strategy = yaml.safe_load(file)
        return strategy
    except FileNotFoundError:
        logger.error(f"Strategy file not found: {STRATEGY_FILE}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML strategy file: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error loading strategy file: {e}")
        raise


def create_local_orders_dir():
    """
    Create the local orders directory if it doesn't exist.
    """
    try:
        ORDER_TRACKING_DIR.mkdir(exist_ok=True)
    except FileExistsError:
        logger.info(f"Local orders directory already exists: {ORDER_TRACKING_DIR}")
        return
    except Exception as e:
        logger.exception(f"Error creating local orders directory: {e}")
        raise


def parse_token_pid(token_pid) -> Tuple[str, str]:
    """
    Parse the token policy ID and hex name from the token.
    """
    try:
        policy, token_name_hex = token_pid.split(".")
        return policy, token_name_hex
    except ValueError:
        logger.error(
            f"Invalid token PID format (expected 'policy.token_name_hex'): {token_pid}"
        )
        raise


def check_wallets(tokens):
    """
    Check if wallets for the tokens exist else create.
    """
    for token_name, _ in tokens.items():
        try:
            create_signing_key(f"{KEY_PREFIX}{token_name}")
        except FileExistsError:
            logger.info(f"Wallet already exists for {token_name}")
            continue


def get_current_block_height():
    try:
        latest_block = CONTEXT.api.block_latest()
        return latest_block.height
    except Exception as e:
        log_exception(logger, "Error getting block height", e)
        return None


def get_tx_block_height(txHash: str):
    try:
        tx_info = CONTEXT.api.transaction(txHash)
        return tx_info.block_height
    except Exception as e:
        log_exception(logger, "Error getting transaction info", e)
        return None
