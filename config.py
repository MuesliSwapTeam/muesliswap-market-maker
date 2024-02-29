from pycardano import (
    Network,
    OgmiosChainContext,
    BlockFrostChainContext
)

from pathlib import Path

from secret import ogmios_url, kupo_url, block_frost_project_id, blockfrost_base_url

# STRATEGY
STRATEGY_FILE = 'standard_market_making_preprod.yaml'

# NETWORK
MAINNET = False # Set to True for mainnet, False for preprod
NETWORK = Network.MAINNET if MAINNET else Network.TESTNET

# Define the chain context
CONTEXT = BlockFrostChainContext(block_frost_project_id, base_url=blockfrost_base_url)
# CONTEXT = OgmiosChainContext(ogmios_url, network=NETWORK)
# CONTEXT = OgmiosChainContext(ogmios_url, kupo_url=kupo_url network=NETWORK)

# LOGGING
LOGS_DIR = "logs"
DEBUG = False # Set to True for debug mode

# CONTRACTS
CONTRACT_ADDRESS = "addr1zyq0kyrml023kwjk8zr86d5gaxrt5w8lxnah8r6m6s4jp4g3r6dxnzml343sx8jweqn4vn3fz2kj8kgu9czghx0jrsyqqktyhv" \
    if MAINNET else "addr_test1wrl28a6jsx4870ulrfygqvqqdnkdjc5sa8f70ys6dvgvjqc8vudlr"


# METADATA
METADATA = {
    "TRANSACTION_MESSAGE": 647,
    "ORDER_CREATOR_ADDRESS": 1000,
    "BUY_CURRENCY_SYMBOL_LABEL": 1002,
    "BUY_TOKEN_NAME_LABEL": 1003,
    "ORDER_AMOUNT_LABEL": 1004,
    "ADA_TRANSFER_LABEL": 1005,
    "PARTIAL_MATCH_ALLOWED": 1007,
    "SELL_CURRENY_SYMBOL_LABEL": 1008,
    "SELL_TOKEN_NAME_LABEL": 1009
}

# TRANSACTION PARAMETERS 
MATCHMAKING_FEE = 950000 # 0.95 ADA
DEPOSIT = 2000000 # 2 ADA

# API ENDPOINTS
MUESLISWAP_API_URL = "https://api.muesliswap.com" if MAINNET else "https://preprod.api.muesliswap.com"
HEALTH_CHECK_ENDPOINT = "/health"
ORDER_BOOK_ENDPOINT = "/orderbook"
PRICE_ENDPOINT = "/price"
OPEN_POSITIONS_ENDPOINT = "/open_positions"

# WALLET INFO
KEYS_DIR = Path(__file__).parent.joinpath("keys")
KEY_PREFIX = "MuesliMarketMaker-" if MAINNET else "MuesliMarketMaker-Testnet-"

# BASE CURRENCY - Specify the base currency the bot uses to trade (Default: ADA)
BASE_POLICY = "" # Leave blank for ADA
BASE_TOKEN_NAME_HEX = "" # Leave blank for ADA
