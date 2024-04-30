import json
from datetime import datetime
from typing import Dict
import os

from pycardano import ScriptHash, AssetName, Address
from bot.utils.logger import get_logger
from configs.config import CONTEXT, INVENTORY_DIR

logger = get_logger(__name__)


def update_inventory(bot, token_name: str, token_info: Dict, address: Address):
    """
    Checks and updates the bot's inventory for a specific token and address.
    """
    policy_id, hexname = token_info["policy_id"], token_info["hexname"]
    try:
        logger.info(f"Querying UTXOs for {token_name} wallet.")
        utxos = CONTEXT.utxos(address)
        total_lovelace = 0
        total_tokens = 0
        token_pid_script_hash = ScriptHash(bytes.fromhex(policy_id))
        token_name_asset_name = AssetName(bytes.fromhex(hexname))

        for utxo in utxos:
            value = utxo.output.amount
            total_lovelace += value.coin
            filtered_assets = value.multi_asset.filter(
                lambda p, n, amount: p == token_pid_script_hash
                and n == token_name_asset_name
            )
            for script_hash in filtered_assets:
                for asset_name in filtered_assets[script_hash]:
                    total_tokens += filtered_assets[script_hash][asset_name]

        total_lovelace_open_orders = 0
        total_tokens_open_orders = 0
        for order in bot.open_orders:
            if (
                order["fromToken"]["address"]["policyId"] == ""
                and order["fromToken"]["address"]["name"] == ""
            ):
                total_lovelace_open_orders += int(order["fromAmount"])
            elif (
                order["fromToken"]["address"]["policyId"] == policy_id
                and order["fromToken"]["address"]["name"] == hexname
            ):
                total_tokens_open_orders += int(order["fromAmount"])
            total_lovelace_open_orders += int(order["attachedLvl"])

        total_lovelace += total_lovelace_open_orders
        total_tokens += total_tokens_open_orders

        inventory_data = calculate_inventory(
            bot,
            token_name,
            token_info,
            total_lovelace,
            total_tokens,
        )

        os.makedirs(INVENTORY_DIR, exist_ok=True)
        inventory_file_name = INVENTORY_DIR.joinpath(f"{token_name}_inventory.json")

        if os.path.exists(inventory_file_name):
            with open(inventory_file_name, "r") as file:
                data = json.load(file)
                if data and data[0]["inventory"] == inventory_data:
                    logger.info("No changes in inventory, skipping log entry.")
                    return

        inventory_record = {
            "timestamp": datetime.now().isoformat(),
            "address": str(address),
            "inventory": inventory_data,
        }
        with open(inventory_file_name, "r+") as file:
            data.insert(0, inventory_record)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

        logger.info(f"Inventory updated and saved: {inventory_record}")

    except FileNotFoundError:
        with open(inventory_file_name, "w") as file:
            json.dump([inventory_record], file, indent=4)
            logger.info(
                f"Inventory file created and first entry saved: {inventory_record}"
            )

    except Exception as e:
        logger.exception(f"Inventory check error: {e}")
        raise


def calculate_inventory(bot, token_name, token_info, total_lovelace, total_tokens):
    """Calculates the total value of the inventory in Lovelace."""
    try:
        if (
            token_name in bot.price_data
            and bot.price_data[token_name].get("price") is not None
        ):
            price = bot.price_data[token_name]["price"]
            if "decimals" in token_info:
                total = int(
                    total_lovelace
                    + (total_tokens / 10 ** token_info["decimals"]) * price
                )
            else:
                logger.exception(f"Invalid decimals for {token_name}")
                total = total_lovelace
        else:
            total = None
            logger.exception(f"Price data not available for {token_name}")

        inventory_data = {
            "Loveless": total_lovelace,
            f"{token_info['policy_id']}.{token_info['hexname']}": total_tokens,
            "Total Lovelace Value": total if total is not None else total_lovelace,
        }
        return inventory_data

    except KeyError as e:
        logger.exception(f"Key error occurred: {e}")
    except TypeError as e:
        logger.exception(f"Type error occurred: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
