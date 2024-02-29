from pycardano import (
        TransactionOutput,
        Address,
)

from pycardano.coinselection import LargestFirstSelector

from config import CONTEXT, METADATA


def create_metadata(
    buy_token_policy_id: str,
    buy_token_hexname: str,
    sell_token_policy_id: str,
    sell_token_hexname: str,
    amount: int,
    total_lovelace_transfer: int,
    address: Address) -> dict:
    """
    Create metadata for the transaction.
    """
    return {
        METADATA["TRANSACTION_MESSAGE"]: '{"msg": ["MuesliSwap Place Order"]}',
        METADATA["ORDER_CREATOR_ADDRESS"]: address.payment_part.to_primitive().hex(),
        METADATA["BUY_CURRENCY_SYMBOL_LABEL"]: buy_token_policy_id,
        METADATA["BUY_TOKEN_NAME_LABEL"]: buy_token_hexname,
        METADATA["ORDER_AMOUNT_LABEL"]:  amount,
        METADATA["ADA_TRANSFER_LABEL"]: total_lovelace_transfer,
        METADATA["PARTIAL_MATCH_ALLOWED"]: "1",
        METADATA["SELL_CURRENY_SYMBOL_LABEL"]: sell_token_policy_id,
        METADATA["SELL_TOKEN_NAME_LABEL"]: sell_token_hexname
    }


def convert_price_to_lovelace(price: float) -> int:
    """
    Convert the price to lovelace.
    """
    return int(price * 1000000)


def select_utxos_ada(address: Address, amount: int):
    """
    Select UTXOs for a transaction.
    """
    encoded_address = Address.encode(address)
    utxos = CONTEXT.utxos(address)
    request = [TransactionOutput.from_primitive([encoded_address, amount])]
    selector = LargestFirstSelector()
    selected, change = selector.select(utxos, request, CONTEXT)
    return selected, change
