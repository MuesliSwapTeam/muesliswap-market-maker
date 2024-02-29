import yaml
from typing import Tuple, Dict, List

from pycardano import (
    PaymentVerificationKey,
    PaymentSigningKey,
    Address,
)

from config import (
    KEYS_DIR,
    NETWORK,
    STRATEGY_FILE,
    KEY_PREFIX
)

from gen_wallet import create_signing_key

from logger import get_logger

logger = get_logger(__name__)

def get_signing_info(name: str) -> Tuple[PaymentVerificationKey, PaymentSigningKey, Address]:
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
        with open(KEYS_DIR.joinpath(f"{name}.addr"), 'r') as f:
            address = Address.from_primitive(f.read().strip())
        return address
    except FileNotFoundError:
        logger.error(f"Address file not found for {token_name}. You need to create a wallet first.")
        raise
    except Exception as e:
        logger.exception(f"Error reading address for {token_name}: {e}")
        raise


def load_strategy_config() -> Dict:
    """
    Load the strategy configuration from the YAML file.
    """
    try:
        with open(f'strategies/{STRATEGY_FILE}', 'r') as file:
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


def parse_token_pid(token_pid) -> Tuple[str, str]:
    """
    Parse the token policy ID and hex name from the token.
    """
    try:
        policy, token_name_hex = token_pid.split(".")
        return policy, token_name_hex
    except ValueError:
        logger.error(f"Invalid token PID format (expected 'policy.token_name_hex'): {token_pid}")
        raise
    

def check_wallets(tokens):
    """
    Check the wallets for the tokens.
    """
    for token_name, _ in tokens.items():
        try:
            create_signing_key(f"{KEY_PREFIX}{token_name}")
        except FileExistsError as e:
            logger.info(f"Wallet already exists for {token_name}: {e}")
            continue
        