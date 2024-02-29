from muesli_bot import MuesliMarketMaker
from logger import get_logger
from utils import load_strategy_config, check_wallets

logger = get_logger(__name__)

def main():
    logger.info("Starting market-making bot.")
    try:
        # Load the strategy configuration
        strategy_config = load_strategy_config()
        if strategy_config is None:
            logger.error("Failed to load strategy configuration.")
            return
        # Initialize the bot with the loaded strategy
        bot = MuesliMarketMaker(strategy_config)

        # Check existing wallets for the selected tokens
        check_wallets(bot.tokens)
        
        # Start main loop
        bot.run_main_loop()
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
    finally:
        logger.info("Market-making bot stopped.")

if __name__ == "__main__":
    main()
