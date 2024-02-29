from pycardano import (
        TransactionOutput, 
        Value, 
        TransactionBuilder,
        Address,
)

from config import CONTEXT, CONTRACT_ADDRESS, MATCHMAKING_FEE, DEPOSIT
from utils import get_signing_info, get_signing_info
from transaction_utils import create_metadata, convert_price_to_lovelace
from logger import get_logger


logger = get_logger(__name__)


def place_buy_order(token_name: str, policy_id: str, hexname: str, address: Address, amount: int, price: float, key_path: str):
    """
    Create a buy order.
    """
    pass


def place_sell_order(token_name: str, policy_id: str, hexname: str, address: Address, amount: int, price: float, key_path: str):
    """
    Create a sell order.
    """
    pass


def cancel_order(tx_id: str, address: Address, key_path: str):
    """
    Cancel all orders.
    """
    pass


def cancel_all_orders(address: str, key_path: str):
    """
    Cancel all orders.
    """
    pass
