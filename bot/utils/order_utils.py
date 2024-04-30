from typing import Dict

from configs.msw_connector_config import (
    BASE_POLICY,
    BASE_TOKEN_NAME_HEX,
    BASE_TOKEN_DECIMALS,
)


def order_to_price(order: Dict) -> int:
    """
    Extract the price from an order in Lovelace, considering the token decimals.
    """
    if order["fromToken"]["address"]["policyId"] == BASE_POLICY:
        from_amount = int(order["fromAmount"])
        to_amount = int(order["toAmount"])
        price_in_ada = from_amount / to_amount
        return int(price_in_ada * 10**BASE_TOKEN_DECIMALS)
    elif order["toToken"]["address"]["policyId"] == BASE_POLICY:
        to_amount = int(order["toAmount"])
        from_amount = int(order["fromAmount"])
        price_in_ada = to_amount / from_amount
        return int(price_in_ada * 10**BASE_TOKEN_DECIMALS)
    else:
        raise ValueError(f"Invalid order format or unrecognized policy ID: {order}")


def get_order_type(order: Dict) -> str:
    """
    Get the order type (buy/sell) from the order.
    """
    if (
        order["fromToken"]["address"]["policyId"] == BASE_POLICY
        and order["fromToken"]["address"]["name"] == BASE_TOKEN_NAME_HEX
    ):
        return "buy"
    elif (
        order["toToken"]["address"]["policyId"] == BASE_POLICY
        and order["toToken"]["address"]["name"] == BASE_TOKEN_NAME_HEX
    ):
        return "sell"
    else:
        raise ValueError(f"Invalid order format: {order}")


def format_order(order: Dict) -> Dict:
    """
    Format the order for local storage.
    """
    return {
        order["txHash"]: {
            "fromTokenPolicy": order["fromToken"]["address"]["policyId"],
            "fromTokenHexname": order["fromToken"]["address"]["name"],
            "fromAmount": order["fromAmount"],
            "toTokenPolicy": order["toToken"]["address"]["policyId"],
            "toTokenHexname": order["toToken"]["address"]["name"],
            "toAmount": order["toAmount"],
            "attachedLvl": order["attachedLvl"],
            "placedAt": order["placedAt"],
            "finalizedAt": order["finalizedAt"],
        }
    }
