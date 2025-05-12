# main.py - Main entry point for the crypto trading bot
import logging
import time
import os
from datetime import datetime
import argparse

# Import our modules
from config import load_config
from modules.exchange import ExchangeHandler
from modules.performance import PerformanceCalculator
from modules.fee_calculator import FeeCalculator
from modules.data_manager import DataManager
from modules.trade_logic import TradeLogic

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def load_api_keys():
    """Load API keys from environment variables or .env file"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_passphrase = os.getenv("API_PASSPHRASE")
    
    return api_key, api_secret, api_passphrase

def main():
    """Main function to run the crypto trading bot"""
    parser = argparse.ArgumentParser(description='Cryptocurrency Trading Bot')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode (no real trades)')
    parser.add_argument('--once', action='store_true', help='Run one cycle and exit')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Load API keys
    api_key, api_secret, api_passphrase = load_api_keys()
    
    # Initialize components
    logger.info("Initializing crypto trading bot...")
    
    exchange = ExchangeHandler(config, api_key, api_secret, api_passphrase)
    performance_calc = PerformanceCalculator(exchange, config)
    fee_calc = FeeCalculator(exchange, config)
    data_manager = DataManager(config)
    trade_logic = TradeLogic(exchange, fee_calc, data_manager, config)
    
    logger.info("Bot initialization complete")
    
    # Run the bot
    try:
        if args.once:
            # Run one cycle and exit
            logger.info("Running single trading cycle")
            trade_logic.run_trading_cycle(simulate=args.simulate)
        else:
            # Run continuously
            logger.info(f"Starting continuous trading bot with {config['check_interval']} second interval")
            logger.info(f"Running in {'simulation' if args.simulate else 'live trading'} mode")
            
            while True:
                cycle_start = datetime.now()
                logger.info(f"Starting trading cycle at {cycle_start}")
                
                trade_logic.run_trading_cycle(simulate=args.simulate)
                
                # Calculate time to next cycle
                elapsed = (datetime.now() - cycle_start).total_seconds()
                sleep_time = max(1, config['check_interval'] - elapsed)
                
                next_cycle = datetime.now().timestamp() + sleep_time
                next_cycle_str = datetime.fromtimestamp(next_cycle).strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"Cycle complete. Next cycle at {next_cycle_str} (sleeping for {sleep_time:.1f} seconds)")
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # Final portfolio value
        prices = exchange.get_current_prices(config['trade_coins'])
        if prices:
            final_value = trade_logic.calculate_portfolio_value(prices)
            logger.info(f"Final portfolio value: {final_value:.2f} {config['base_currency']}")
        
        logger.info("Bot execution completed")

if __name__ == "__main__":
    main()