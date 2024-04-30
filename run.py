from bot.muesli_bot import MuesliMarketMaker
from bot.utils.logger import get_logger
from bot.utils.utils import load_strategy_config, check_wallets, create_local_orders_dir

logger = get_logger(__name__)

def main():
    logger.info("Starting market-making bot.")
    try:
        # Load the strategy configuration
        strategy_config = load_strategy_config()
        if strategy_config is None:
            logger.error("Failed to load strategy configuration.")
            return
        
        # Check existing wallets for the selected tokens
        check_wallets(strategy_config['tokens'])

        # Init local orders tracking
        create_local_orders_dir()
                 
        # Initialize the bot with the loaded strategy
        bot = MuesliMarketMaker(strategy_config)

        # Start main loop
        bot.run_main_loop()
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
    finally:
        logger.info("Market-making bot stopped.")

if __name__ == "__main__":
    main()
