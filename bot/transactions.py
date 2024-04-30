from typing import Dict, Optional, List

from pycardano import (
    TransactionOutput,
    TransactionInput,
    Value,
    TransactionBuilder,
    Address,
    AuxiliaryData,
    Metadata,
    UTxO,
)

from configs.config import CONTEXT, DISABLE_TX
from configs.msw_connector_config import (
    CONTRACT_ADDRESS,
    MATCHMAKING_FEE,
    DEPOSIT,
    BASE_POLICY,
    BASE_TOKEN_NAME_HEX,
)
from bot.utils.utils import get_signing_info
from bot.utils.transaction_utils import (
    create_metadata_place_order,
    select_utxos_ada,
    select_utxos_multi_asset,
    create_metadata_cancel_order,
    create_reedemer,
    get_script,
    remove_used_utxos,
)
from bot.utils.datum_utils import create_order_datum

from bot.utils.logger import get_logger

logger = get_logger(__name__)


def place_buy_order(
    token_name: str,
    policy_id: str,
    hexname: str,
    address: Address,
    amount: int,
    decimals: int,
    price: int,
    key_path: str,
    preselected_utxos: Optional[List] = None,
) -> Dict[str, Dict[str, str]]:
    """Create and place a buy order on exchange.

    Args:
        token_name (str): Name of buy token
        policy_id (str): Policy ID of buy token
        hexname (str): Hexname of buy token
        address (Address): Address of the buyer
        amount (int): Amount of buy token
        price (float): Price of buy token
        key_path (str): Path to the signing key

    Returns:
        Dict[str, Dict[str, str]]: Transaction data
    """
    _, payment_skey, _ = get_signing_info(key_path)

    # Create builder and add input address
    builder = TransactionBuilder(CONTEXT)
    builder.add_input_address(address)

    # Calculate total amount
    total_amount_to_pay = int(amount / 10**decimals) * price

    fees_and_deposit = MATCHMAKING_FEE + DEPOSIT
    total_amount_to_send = total_amount_to_pay + fees_and_deposit
    logger.info(f"Creating buy order for {token_name} with price {price}")
    # Select and add UTXOs to the transaction
    selected_utxos, _ = select_utxos_ada(
        address, total_amount_to_send, preselected_utxos
    )
    for utxo in selected_utxos:
        builder.add_input(utxo)

    # Create metadata
    metadata = create_metadata_place_order(
        policy_id,
        hexname,
        BASE_POLICY,
        BASE_TOKEN_NAME_HEX,
        amount,
        fees_and_deposit,
        address,
    )
    # Add metadata to the transaction
    auxiliary_data = AuxiliaryData(data=Metadata(metadata))
    builder.auxiliary_data = auxiliary_data

    # Create Datum
    datum = create_order_datum(
        address.payment_part.to_primitive().hex(),
        address.staking_part.to_primitive().hex(),
        policy_id,
        hexname,
        BASE_POLICY,
        BASE_TOKEN_NAME_HEX,
        amount,
        fees_and_deposit,
    )
    # Add outputs
    builder.add_output(
        TransactionOutput(
            address=Address.decode(CONTRACT_ADDRESS),
            amount=Value(total_amount_to_send),
            datum_hash=datum.hash(),
        ),
        datum=datum,
        add_datum_to_witness=True,
    )

    # Create final signed transaction
    signed_tx = builder.build_and_sign([payment_skey], change_address=address)
    txHash = CONTEXT.submit_tx(signed_tx) if not DISABLE_TX else "Buy_test"
    return {
        txHash: {
            "fromTokenPolicy": BASE_POLICY,
            "fromTokenHexname": BASE_TOKEN_NAME_HEX,
            "fromAmount": total_amount_to_pay,
            "toTokenPolicy": policy_id,
            "toTokenHexname": hexname,
            "toAmount": amount,
            "attachedLvl": fees_and_deposit,
        }
    }, (
        remove_used_utxos(preselected_utxos, selected_utxos)
        if preselected_utxos
        else None
    )


def place_sell_order(
    token_name: str,
    policy_id: str,
    hexname: str,
    address: Address,
    amount: int,
    decimals: int,
    price: float,
    key_path: str,
    preselected_utxos: Optional[List] = None,
) -> Dict[str, Dict[str, str]]:
    """Create and place a sell order on exchange.

    Args:
        token_name (str): Name of sell token
        policy_id (str): Policy ID of sell token
        hexname (str): Hexname of sell token
        address (Address): Address of the seller
        amount (int): Amount of sell token
        price (float): Price of sell token
        key_path (str): Path to the signing key

    Returns:
        Dict[str, Dict[str, str]]: Transaction data
    """
    _, payment_skey, _ = get_signing_info(key_path)

    # Create builder and add input address
    builder = TransactionBuilder(CONTEXT)
    builder.add_input_address(address)

    # Amount of ADA to ask for
    total_amount_to_ask = int((amount / 10**decimals)) * price - MATCHMAKING_FEE

    fees_and_deposit = MATCHMAKING_FEE + DEPOSIT
    logger.info(f"Creating Sell order for {amount} of {token_name} with price {price}")

    # Select and add UTXOs to the transaction
    selected_utxos, _ = select_utxos_multi_asset(
        address, fees_and_deposit, policy_id, token_name, amount, preselected_utxos
    )
    for utxo in selected_utxos:
        builder.add_input(utxo)

    # Create metadata
    metadata = create_metadata_place_order(
        BASE_POLICY,
        BASE_TOKEN_NAME_HEX,
        policy_id,
        hexname,
        total_amount_to_ask,
        fees_and_deposit,
        address,
    )

    # Add metadata to the transaction
    auxiliary_data = AuxiliaryData(data=Metadata(metadata))
    builder.auxiliary_data = auxiliary_data

    # Create Datum
    datum = create_order_datum(
        address.payment_part.to_primitive().hex(),
        address.staking_part.to_primitive().hex(),
        BASE_POLICY,
        BASE_TOKEN_NAME_HEX,
        policy_id,
        hexname,
        total_amount_to_ask,
        fees_and_deposit,
    )

    # Add outputs
    builder.add_output(
        TransactionOutput(
            address=Address.decode(CONTRACT_ADDRESS),
            amount=Value.from_primitive(
                [
                    fees_and_deposit,
                    {
                        bytes.fromhex(f"{policy_id}"): {
                            bytes(token_name, "utf-8"): amount
                        }
                    },
                ]
            ),
            datum_hash=datum.hash(),
        ),
        datum=datum,
        add_datum_to_witness=True,
    )

    # Create final signed transaction
    signed_tx = builder.build_and_sign([payment_skey], change_address=address)
    txHash = CONTEXT.submit_tx(signed_tx) if not DISABLE_TX else "Sell_test"
    return {
        txHash: {
            "fromTokenPolicy": policy_id,
            "fromTokenHexname": hexname,
            "fromAmount": amount,
            "toTokenPolicy": BASE_POLICY,
            "toTokenHexname": BASE_TOKEN_NAME_HEX,
            "toAmount": total_amount_to_ask + MATCHMAKING_FEE,
            "attachedLvl": fees_and_deposit,
        }
    }, (
        remove_used_utxos(preselected_utxos, selected_utxos)
        if preselected_utxos
        else None
    )


def cancel_order(
    order: Dict,
    address: Address,
    key_path: str,
    preselected_utxos: Optional[List] = None,
) -> Dict[str, Dict[str, str]]:
    """Cancel order.

    Args:
        order (Dict): Order to cancel fetched by MuesliSwap orders API
        address (Address): Bot address
        key_path (str): Path to the signing key

    Returns:
        Dict[str, Dict[str, str]]: Transaction data
    """
    _, payment_skey, _ = get_signing_info(key_path)

    # Create builder and add input address
    builder = TransactionBuilder(CONTEXT)
    builder.add_input_address(address)

    # We only need the deposit for canceling
    total_amount = DEPOSIT

    # Select and add UTXOs to the transaction
    selected_utxos, _ = select_utxos_ada(address, total_amount, preselected_utxos)
    for utxo in selected_utxos:
        builder.add_input(utxo)

    # Create metadata
    metadata = create_metadata_cancel_order()

    # Add metadata to the transaction
    auxiliary_data = AuxiliaryData(data=Metadata(metadata))
    builder.auxiliary_data = auxiliary_data

    attachedLvl = int(order["attachedLvl"])
    if (
        order["fromToken"]["address"]["policyId"] == BASE_POLICY
        and order["fromToken"]["address"]["name"] == BASE_TOKEN_NAME_HEX
    ):
        toAmount = int(order["toAmount"])
    else:
        toAmount = int(order["toAmount"]) - MATCHMAKING_FEE

    # Recreate datum
    datum = create_order_datum(
        address.payment_part.to_primitive().hex(),
        address.staking_part.to_primitive().hex(),
        order["toToken"]["address"]["policyId"],
        order["toToken"]["address"]["name"],
        order["fromToken"]["address"]["policyId"],
        order["fromToken"]["address"]["name"],
        toAmount,
        int(order["attachedLvl"]),
    )

    redeemer = create_reedemer()
    script = get_script("script.cbor")
    if (
        order["fromToken"]["address"]["policyId"] == BASE_POLICY
        and order["fromToken"]["address"]["name"] == BASE_TOKEN_NAME_HEX
    ):
        tx_out_amount = Value(int(order["fromAmount"]) + attachedLvl)
    else:
        tx_out_amount = Value.from_primitive(
            [
                attachedLvl,
                {
                    bytes.fromhex(f"{ order['fromToken']['address']['policyId']}"): {
                        order["fromToken"]["address"]["name"]: int(order["fromAmount"])
                    }
                },
            ]
        )

    # Create script utxo to spend
    tx_in = TransactionInput.from_primitive([order["txHash"], order["outputIdx"]])
    utxo_to_spend = UTxO(
        tx_in,
        TransactionOutput(
            CONTRACT_ADDRESS,
            amount=tx_out_amount,
            datum_hash=datum.hash(),
        ),
    )

    # Add outputs
    builder.add_script_input(
        utxo_to_spend,
        script=script,
        datum=datum,
        redeemer=redeemer,
    )

    # Return this to the bot
    builder.add_output(
        TransactionOutput(
            address=address,
            amount=tx_out_amount,
        )
    )

    # Create final signed transaction
    builder.required_signers = [address.payment_part]
    signed_tx = builder.build_and_sign([payment_skey], change_address=address)
    txHash = CONTEXT.submit_tx(signed_tx) if not DISABLE_TX else "Cancel_test"

    return {
        order["txHash"]: {
            "cancel_txHash": txHash,
            "toTokenPolicy": order["toToken"]["address"]["policyId"],
            "toTokenHexname": order["toToken"]["address"]["name"],
            "toAmount": int(order["toAmount"]),
            "fromTokenPid": order["fromToken"]["address"]["policyId"],
            "fromTokenHexname": order["fromToken"]["address"]["name"],
            "fromAmount": int(order["toAmount"]),
            "attachedLvl:": order["attachedLvl"],
        }
    }, (
        remove_used_utxos(preselected_utxos, selected_utxos)
        if preselected_utxos
        else None
    )
