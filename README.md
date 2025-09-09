# MuesliSwap Market Making Bot

Open-Source framework for the Muesliswap market making bot.  

## Warning

:warning: **Use the market-making bot at your own risk.** Running this bot involves substantial risk, including the potential loss of funds. Only use this bot with amounts that you are willing to lose. The developers and contributors of this bot are not liable for any financial losses that may occur from using this software. Make sure you understand the code and the strategies. By using this bot, you acknowledge that you are aware of the risks involved and assume all responsibility.

## Project Documentation

Below is a documentation of the files and directories in the project:

### Main Script

- `run.py`: The main executable script that runs the bot.

### Main components of the bot
The `/bot` directory contains the main components of the bot.

  - `health_check.py`: Health check script for the API endpoints.
  - `inventory_management.py`: Manages and monitors inventory.
  - `muesli_bot.py`: The main bot script responsible for executing trades.
  - `order_book_tracking.py`: Tracks the state of the order book.
  - `order_management.py`: Handles order tracking of the bot.
  - `price.py`: Contains functionality for price data retrieval.
  - `strategy.py`: Implements the trading strategy of the bot.
  - `transactions.py`: Handles the creation and submission of transactions to the exchange.

  - `/utils`: Utility scripts for various functions such as wallet generation and logging.
    - `datum_utils.py`: Utilities for handling datum construction for orders.
    - `gen_wallet.py`:  Utility script for generating wallets and keys.
    - `logger.py`: Custom logger for the bot's operation.
    - `order_utils.py`: Utilities related to order management.
    - `transaction_utils.py`: Utilities for transaction order placement and cancelation.
    - `utils.py`: Generic utility functions used across the bot.

### Configurations
The `/configs` directory contains all configuration files for the bot. Configuration files are used to set up trading parameters, API keys, and other necessary settings for the bot to operate.

- `config.py`: The central configuration script where you can set environment variables and global settings.
- `msw_connector_config.py`: Configuration for the MuesliSwap connector, setting up endpoints, transaction metadata, etc.
- `secret_template.py`: A template for storing secrets. Rename to `secret.py` and add your actual secret keys.

- `strategies/`: Strategy configuration files in YAML format.
  - `standard_market_making_mainnet.yaml`: Configuration for standard market making on the mainnet.
  - `standard_market_making_preprod.yaml`: Configuration for standard market making on the preprod testnet.
  - `aggressive_market_making_mainnet.yaml`: Configuration for aggressive market making on the mainnet.
  - `aggressive_market_making_preprod.yaml`: Configuration for aggressive market making on the preprod testnet.
  - `volume_based_adaptive_mainnet.yaml`: Configuration for volume-based adaptive strategy on the mainnet.
  - `volume_based_adaptive_preprod.yaml`: Configuration for volume-based adaptive strategy on the preprod testnet.
  - `trend_following_mainnet.yaml`: Configuration for trend-following strategy on the mainnet.
  - `trend_following_preprod.yaml`: Configuration for trend-following strategy on the preprod testnet.

### Other Files & Directories

- `/scripts`: Directory containg the script's cbor.
  - `script.cbor`: Script cbor for canceling orders.

- `poetry.lock`: Lockfile for specifying exact versions of dependencies.
- `pyproject.toml`: Defines the project and its dependencies.

- `keys/`: Will be created by ```gen_wallet.py```. Contains addreses, skeys and vkeys for the wallets. After creation, you will need to fund the wallet for the bot to operate.
- `logs/`: Log files for the bot's operations and events.
- `orders/`: Will be created by bot. Contains logs of open/matched/canceled orders.
- `inventory/`: Will be created by bot. Logs the inventory (lovelace and tokens) state over time.

## MuesliSwap Integration

This bot integrates with the MuesliSwap Decentralized Exchange (DEX) through its API, enabling the retrieval of order book details, current prices, and active orders managed by the bot.

### Configuration
API configurations are set within the `configs/msw_connector_config.py` file.

### Key API Endpoints
- **Health Check**: `/health` - Verifies the API's operational status.
- **Order Book**: `/orderbook` - Retrieves the order book for specified token pairs.
- **Price Query**: `/price` - Obtains the current prices for specific token pairs.
- **Open Positions**: `/open-positions` - Checks the number of open positions for a particular token.
- **Order Status**: `/orders/v2` - Queries the status (open, matched, or canceled) of orders for a specified token.

### Documentation
For more detailed information about the API's capabilities and usage, refer to the official [MuesliSwap API Documentation](https://docs.muesliswap.com/cardano/muesli-api).

### Trading Logic
The methods for placing and canceling orders within the MuesliSwap order book are implemented in `bot/transactions.py`.


## Setup

Follow these steps to set up the up bot.

### Install Dependencies

```
poetry install
poetry shell
```

### Configure Blockfrost  

You will need Blockfrost to operate the bot.
1. Change ```secret_template.py``` to ```secret.py```
2. Fill in your environment parameters with the correct values for your Blockfrost project.

### Basic Parameter Configuration

Adjust parameters in ```configs/config.py``` to your preferences:
1. Switch between Mainnet and Preprod for testing.
2. Choose one of the strategy files under ```configs/strategies``` (e.g. ```standard_market_making.yaml```) or write your own strategy.
3. Update the tokens you want to trade

### Configure Strategy Parameters

The bot supports multiple customizable trading strategies. Choose one of the available strategies and adjust the parameters in your ```strategy.yaml``` file:

#### Available Strategies

1. **Standard Market Making** (`standard_market_making`)
   - Basic market making with fixed spreads
   - Suitable for stable markets with consistent liquidity

2. **Aggressive Market Making** (`aggressive_market_making`)
   - Tighter spreads with dynamic adjustment based on volatility
   - Higher frequency trading with risk management
   - Best for active markets where you want to capture more volume

3. **Volume-Based Adaptive** (`volume_based_adaptive`)
   - Adjusts spreads based on trading volume patterns
   - Tighter spreads during high volume, wider during low volume
   - Ideal for markets with varying activity levels

4. **Trend Following** (`trend_following`)
   - Places more orders in the direction of price trends
   - Uses Simple Moving Average (SMA) for trend detection
   - Suitable for trending markets

#### Basic Configuration Example

```
"name": "standard_market_making",   # Name of the strategy
"type": "market_making",            # Type of strategy, e.g. market_making
"exchange": "muesliswap",           # Exchange to run the strategy on
"n_orders": 1,                      # Number of orders to place on each side of the order book
"delta": 0.05,                      # Distance between orders as a fraction of the mid price
"order_refresh_threshold": 0.1,     # Percentage change in price to trigger order refresh
"loop_interval": 5,                 # Time in seconds between each loop
"tokens": {                         # Tokens to trade
    "MILKv2": {                                                               
        "hexname": "4d494c4b7632",
        "policy_id": "afbe91c0b44b3040e360057bf8354ead8c49c4979ae6ab7c4fbdc9eb",
        "amount": 1000000,   # Amount tokens per trade including decimals, i.e. 1000000 corresponds to 1 MILKv2
        "decimals": 6 # Number of decimals in the token
    }
}
```

#### Strategy-Specific Parameters

**Aggressive Market Making:**
- `volatility_multiplier`: How much volatility affects spread adjustment (default: 1.5)
- `min_delta`: Minimum spread (default: 0.005)
- `max_delta`: Maximum spread (default: 0.05)
- `price_history_length`: Number of price points for volatility calculation (default: 20)

**Volume-Based Adaptive:**
- `volume_threshold_high`: High volume threshold multiplier (default: 1.5)
- `volume_threshold_low`: Low volume threshold multiplier (default: 0.5)
- `high_volume_delta_multiplier`: Spread multiplier for high volume (default: 0.7)
- `low_volume_delta_multiplier`: Spread multiplier for low volume (default: 1.3)
- `volume_history_length`: Number of volume points for average calculation (default: 10)

**Trend Following:**
- `trend_strength_threshold`: Minimum price deviation from SMA to consider a trend (default: 0.02)
- `trend_multiplier`: Multiplier for trend-biased order placement (default: 1.5)
- `sma_period`: Period for Simple Moving Average calculation (default: 10)
- `price_history_length`: Number of price points for trend analysis (default: 20)

### Setup Wallets

The bot expects a separate wallet and corresponding keys for each token specified in the ```strategy.yaml```.
When you run ```python main.py``` the bot checks for the existence of the wallets for all tokens and creates new wallets if they don't exist.
To use the bot, you will need to fund the newly created wallets with ADA and the respective token.

### Run the bot
After everything is set up, you can run the bot by executing ```python run.py```.
