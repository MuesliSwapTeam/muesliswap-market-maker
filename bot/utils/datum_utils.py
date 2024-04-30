from typing import ClassVar, Union
from dataclasses import dataclass

from pycardano import PlutusData
from configs.msw_connector_config import ALLOW_PARTIAL_MATCH


def from_hex(hex_string: str) -> bytes:
    return bytes.fromhex(hex_string)


@dataclass
class BoolField(PlutusData):
    CONSTR_ID: ClassVar[int] = int(ALLOW_PARTIAL_MATCH)


@dataclass
class PubKeyHash(PlutusData):
    pub_key_hash: bytes
    CONSTR_ID: ClassVar[int] = 0


@dataclass
class StakingCredentialHash(PlutusData):
    staking_cred_hash: bytes
    CONSTR_ID: ClassVar[int] = 0


@dataclass
class StakingInner(PlutusData):
    CONSTR_ID: ClassVar[int] = 0
    staking_cred_hash: Union[StakingCredentialHash]


@dataclass
class StakingOuter(PlutusData):
    staking_inner: StakingInner
    CONSTR_ID: ClassVar[int] = 0


@dataclass
class AddressObject(PlutusData):
    pub_key_hash: PubKeyHash
    staking_outer: StakingOuter
    CONSTR_ID: ClassVar[int] = 0


@dataclass
class OrderFields(PlutusData):
    address_object: AddressObject
    buy_currency: bytes
    buy_token: bytes
    sell_currency: bytes
    sell_token: bytes
    buy_amount: int
    allow_partial: BoolField
    lovelace_attached: int
    CONSTR_ID: ClassVar[int] = 0


@dataclass
class OrderDatum(PlutusData):
    fields: OrderFields
    CONSTR_ID: ClassVar[int] = 0


def create_order_datum(
    oCreatorPubKeyHash,
    oCreatorStakingKeyHash,
    oBuyCurrency,
    oBuyToken,
    oSellCurrency,
    oSellToken,
    oBuyAmount,
    lovelaceAttached,
) -> OrderDatum:

    pub_key_hash_obj = PubKeyHash(pub_key_hash=from_hex(oCreatorPubKeyHash))
    staking_cred_hash_obj = StakingCredentialHash(
        staking_cred_hash=from_hex(oCreatorStakingKeyHash)
    )
    staking_wrapper = StakingOuter(
        staking_inner=StakingInner(staking_cred_hash=staking_cred_hash_obj)
    )
    address_object = AddressObject(
        pub_key_hash=pub_key_hash_obj, staking_outer=staking_wrapper
    )

    allow_partial_obj = BoolField()
    order_fields = OrderFields(
        address_object=address_object,
        buy_currency=from_hex(oBuyCurrency),
        buy_token=from_hex(oBuyToken),
        sell_currency=from_hex(oSellCurrency),
        sell_token=from_hex(oSellToken),
        buy_amount=int(oBuyAmount),
        allow_partial=allow_partial_obj,
        lovelace_attached=int(lovelaceAttached),
    )
    order_datum = OrderDatum(fields=order_fields)
    return order_datum
