from pycardano import Network, BlockFrostChainContext

from pathlib import Path

from configs.secret import blockfrost_project_id, blockfrost_base_url

# STRATEGY
# STRATEGY_FILE = 'standard_market_making_preprod.yaml'
STRATEGY_FILE = "standard_market_making_mainnet.yaml"

# NETWORK
MAINNET = True  # Set to True for mainnet, False for preprod
NETWORK = Network.MAINNET if MAINNET else Network.TESTNET

# Define the chain context
CONTEXT = BlockFrostChainContext(blockfrost_project_id, base_url=blockfrost_base_url)

# ORDER TIMEOUT: Wait if order is not onchain in open order
ORDER_TIMEOUT = 2  # heigth

# LOGGING & DEBUGGING
LOGS_DIR = Path(__file__).parent.parent.joinpath("logs")
DEBUG = False  # Set to True for logger debug mode
DISABLE_TX = False  # Set to True to disable transactions for testing/debugging purposes

# Track newly placed and canceled orders locally to avoid double spending
ORDER_TRACKING_DIR = Path(__file__).parent.parent.joinpath("orders")
INVENTORY_DIR = Path(__file__).parent.parent.joinpath("inventory")
LOCAL_ORDER_TRACKING_FILE = "local_order_tracking.json"
ONCHAIN_ORDER_TRACKING_FILE = "onchain_order_tracking.json"

# WALLET INFO
KEYS_DIR = Path(__file__).parent.parent.joinpath("keys")
CONTRACT_DIR = Path(__file__).parent.parent.joinpath("scripts")

KEY_PREFIX = "MuesliMarketMaker-" if MAINNET else "MuesliMarketMaker-Testnet-"
