# MuesliSwap Market Making Bot

Framework for the Muesliswap market making bot.  
Stay tuned for our upcoming integration with MuesliSwap.

## Project Documentation

Below is a documentation of the files and directories in the project:

- `keys/`: Will be created by ```gen_wallet.py```. Contains addreses, skeys and vkeys for transactions.
- `logs/`: Log files for the bot's operations and events.
- `strategies/`: Strategy configuration files in YAML format.
  - `standard_market_making_mainnet.yaml`: Configuration for standard market making on the mainnet.
  - `standard_market_making_preprod.yaml`: Configuration for standard market making on the preprod testnet.
- `config.py`: Configuration file where global parameters are set.
- `gen_wallet.py`: Utility script for generating wallets and keys.
- `health_check.py`: Script to check the bot's health and connectivity to the exchange.
- `inventory_management.py`: Manages the bot's inventory for the traded tokens.
- `logger.py`: Sets up logging for the bot.
- `main.py`: The main executable script that runs the market making bot.
- `muesli_bot.py`: Core loop of the bot's functionalities and trading logic.
- `order_book_tracking.py`: Tracks the state of the order book on the exchange.
- `order_management.py`: Track the active orders of the bot.
- `poetry.lock`: Lockfile for specifying exact versions of dependencies.
- `price.py`: Fetches token pricing information.
- `pyproject.toml`: Defines the project and its dependencies.
- `secret_template.py`: Template for secrets configuration. Rename to `secret.py` and fill out before use.
- `strategy.py`: Defines and manages the bot's trading strategies.
- `transaction_utils.py`: Helper functions for creating and managing transactions.
- `transactions.py`: Handles the creation and submission of transactions to the exchange.
- `utils.py`: Utility functions used across the bot.


## Setup

### Install Dependencies:  

```
poetry install
poetry shell
```

### Configure Node  

You will need Blockfrost or Ogmios endpoints
1. Change ```secret_template.py``` to ```secret.py```
2. Fill in your environment parameters with the correct value for Blockfrost or Ogmios and Kupo endpoints.

### Basic Parameter Configuration:

Adjust parameters in ```config.py``` to your preferences:
1. Switch between Mainnet and Preprod for testing
2. Choose one of the strategy files under ```/strategies``` (e.g. ```standard_market_making.yaml```) or write your own strategy
3. Update the tokens you want to trade

### Configure Strategy Parameters:

Adjust the parameters in your ```strategy.yaml``` (e.g. ```standard_market_making.yaml```) to your needs:

```
"name": "standard_market_making",   # Name of the strategy
"type": "market_making",            # Type of strategy, e.g. market_making
"exchange": "muesliswap",           # Exchange to run the strategy on
"n_orders": 3,                      # Number of orders to place on each side of the order book
"delta": 0.01,                      # Distance between orders as a fraction of the mid price
"order_refresh_threshold": 0.01,    # Percentage change in price to trigger order refresh
"loop_interval": 1,                 # Time in seconds between each loop
"tokens": {                         # Tokens to trade
    "MILK": {                                                               
        "hexname": "4d494c4b7632",
        "policy_id": "afbe91c0b44b3040e360057bf8354ead8c49c4979ae6ab7c4fbdc9eb",
        "amount": 5,   # Amount of tokens per trade
    }
}
```

### Setup Wallets

The bot expects a separate wallet and corresponding keys for each token specified in the ```strategy.yaml```.
When you run ```python main.py``` the bot checks for the existence of the wallets for all tokens and creates new wallets if they don't exist.
To use the bot, you will need to fund the newly created wallets with ADA and the respective token.

### Run Market Maker

Execute ```python main.py```
