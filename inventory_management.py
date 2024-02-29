from pycardano import ScriptHash, AssetName, Address
from logger import get_logger
from config import CONTEXT

logger = get_logger(__name__)

def check_inventory(bot, token_name: str, policy_id: str, hexname: str, address: Address):
    """
    Checks and updates the bot's inventory for a specific token and address
    """
    try:
        logger.info(f"Querying UTXOs for {address}")
        utxos = CONTEXT.utxos(address)

        total_lovelace = 0
        total_tokens = 0
        token_pid_script_hash = ScriptHash(bytes.fromhex(policy_id))
        token_name_asset_name = AssetName(bytes(token_name, 'utf-8'))

        for utxo in utxos:
            value = utxo.output.amount
            total_lovelace += value.coin

            # Filter multi_asset for specific token_pid and token_name
            filtered_assets = value.multi_asset.filter(
                lambda p, n, amount: p == token_pid_script_hash and n == token_name_asset_name
            )

            # Sum quantities token
            for script_hash in filtered_assets:
                for asset_name in filtered_assets[script_hash]:
                    total_tokens += filtered_assets[script_hash][asset_name]

        logger.info("Inventory checked and updated: ")
        bot.inventory[address.encode()] = {
            "Loveless": total_lovelace, 
            f"{policy_id}.{hexname}": total_tokens
        }
        logger.info(f"Inventory: {bot.inventory}")
    except Exception as e:
        logger.exception(f"Inventory check error: {e}")
        raise
