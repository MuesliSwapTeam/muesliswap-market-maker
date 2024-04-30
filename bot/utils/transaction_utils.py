from typing import Dict, Optional, List
from pycardano import TransactionOutput, Address, PlutusData, Redeemer, PlutusV2Script

from pycardano.coinselection import LargestFirstSelector

from configs.config import CONTEXT, CONTRACT_DIR
from configs.msw_connector_config import METADATA, ALLOW_PARTIAL_MATCH


class CancelDatum(PlutusData):
    CONSTR_ID = 0


def create_metadata_place_order(
    buy_token_policy_id: str,
    buy_token_hexname: str,
    sell_token_policy_id: str,
    sell_token_hexname: str,
    amount: int,
    total_lovelace_transfer: int,
    address: Address,
) -> dict:
    """
    Create metadata for the transaction.
    """
    return {
        METADATA["TRANSACTION_MESSAGE"]: "{'msg': ['MuesliSwap Place Order']}",
        METADATA["ORDER_CREATOR_ADDRESS"]: "0x"
        + address.payment_part.to_primitive().hex(),
        METADATA["BUY_CURRENCY_SYMBOL_LABEL"]: buy_token_policy_id,
        METADATA["BUY_TOKEN_NAME_LABEL"]: buy_token_hexname,
        METADATA["ORDER_AMOUNT_LABEL"]: amount,
        METADATA["ADA_TRANSFER_LABEL"]: total_lovelace_transfer,
        METADATA["PARTIAL_MATCH_ALLOWED"]: int(ALLOW_PARTIAL_MATCH),
        METADATA["SELL_CURRENY_SYMBOL_LABEL"]: sell_token_policy_id,
        METADATA["SELL_TOKEN_NAME_LABEL"]: sell_token_hexname,
    }


def create_metadata_cancel_order() -> Dict[str, str]:
    """
    Create metadata for the transaction.
    """
    return {
        METADATA["TRANSACTION_MESSAGE"]: "{'msg': ['MuesliSwap Cancel Order']}",
    }


def create_reedemer() -> Redeemer:
    """
    Create a redeemer for the transaction.
    """
    return Redeemer(CancelDatum())


def convert_price_to_lovelace(price: float) -> int:
    """
    Convert the price to lovelace.
    """
    return int(price * 10 ^ 6)


def select_utxos_ada(
    address: Address, amount: int, preselected_utxos: Optional[List] = None
):
    """Select UTXOs for ADA."""
    encoded_address = Address.encode(address)
    if preselected_utxos:
        utxos = preselected_utxos
    else:
        utxos = CONTEXT.utxos(address)
    request = [TransactionOutput.from_primitive([encoded_address, amount])]
    selector = LargestFirstSelector()
    selected, change = selector.select(utxos, request, CONTEXT)
    return selected, change


def select_utxos_multi_asset(
    address: Address,
    ada_amount: int,
    policy_id: str,
    token_name: str,
    token_amount: int,
    preselected_utxos: Optional[List] = None,
):
    """
    Select UTXOs for ADA and token.
    """
    encoded_address = Address.encode(address)
    if preselected_utxos:
        utxos = preselected_utxos
    else:
        utxos = CONTEXT.utxos(address)
    request = [
        TransactionOutput.from_primitive(
            [
                encoded_address,
                [
                    ada_amount,
                    {
                        bytes.fromhex(f"{policy_id}"): {
                            bytes(token_name, "utf-8"): token_amount
                        }
                    },
                ],
            ]
        )
    ]
    selector = LargestFirstSelector()
    selected, change = selector.select(utxos, request, CONTEXT)
    return selected, change


def get_script(name) -> PlutusV2Script:
    """Get the cbor."""
    with open(CONTRACT_DIR.joinpath(name)) as f:
        contract = PlutusV2Script(bytes.fromhex(f.read()))
    return contract


def remove_used_utxos(original_utxos, used_utxos):
    """Remove used UTXOs from the original list."""
    used_utxo_ids = {(utxo.input.transaction_id, utxo.input.index) for utxo in used_utxos}
    updated_utxos = [
        utxo for utxo in original_utxos
        if (utxo.input.transaction_id, utxo.input.index) not in used_utxo_ids
    ]
    return updated_utxos
