# Configurations relevant to the Muesliswap exchange
from configs.config import MAINNET

# Partial matches
ALLOW_PARTIAL_MATCH = False

# BASE CURRENCY on MUESLISWAP
BASE_POLICY = ""  # Leave blank for ADA
BASE_TOKEN_NAME_HEX = ""  # Leave blank for ADA
BASE_TOKEN_DECIMALS = 6

# CONTRACT ADDRESSES
CONTRACT_ADDRESS = (
    "addr1zyq0kyrml023kwjk8zr86d5gaxrt5w8lxnah8r6m6s4jp4g3r6dxnzml343sx8jweqn4vn3fz2kj8kgu9czghx0jrsyqqktyhv"
    if MAINNET
    else "addr_test1wqq0kyrml023kwjk8zr86d5gaxrt5w8lxnah8r6m6s4jp4gka6an7"
)

# METADATA STRUCTURE
METADATA = {
    "TRANSACTION_MESSAGE": 674,
    "ORDER_CREATOR_ADDRESS": 1000,
    "BUY_CURRENCY_SYMBOL_LABEL": 1002,
    "BUY_TOKEN_NAME_LABEL": 1003,
    "ORDER_AMOUNT_LABEL": 1004,
    "ADA_TRANSFER_LABEL": 1005,
    "PARTIAL_MATCH_ALLOWED": 1007,
    "SELL_CURRENY_SYMBOL_LABEL": 1008,
    "SELL_TOKEN_NAME_LABEL": 1009,
}

# TRANSACTION PARAMETERS
MATCHMAKING_FEE = 950000  # 0.95 ADA
DEPOSIT = 1700000  # 1.7 ADA

# MUESLISWAP API ENDPOINTS
MUESLISWAP_API_URL = (
    "https://api.muesliswap.com" if MAINNET else "https://preprod.api.muesliswap.com"
)
MUESLISWAP_ONCHAIN_URL = (
    "https://onchain.muesliswap.com"
    if MAINNET
    else "https://preprod.onchain.muesliswap.com"
)
HEALTH_CHECK_ENDPOINT = "/health"
ORDER_BOOK_ENDPOINT = "/orderbook"
PRICE_ENDPOINT = "/price"
OPEN_POSITIONS_ENDPOINT = "/open-positions"
ORDERS_ENDPOINT = "/orders/v2"
