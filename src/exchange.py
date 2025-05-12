# exchange.py - Exchange interaction module
import ccxt
import logging

logger = logging.getLogger(__name__)

class ExchangeHandler:
    def __init__(self, config, api_key=None, api_secret=None, api_passphrase=None):
        """Initialize exchange connection"""
        self.config = config
        self.exchange_id = config['exchange_id']
        self.base_currency = config['base_currency']
        self.trade_pairs = [f"{coin}/{self.base_currency}" for coin in config['trade_coins']]
        
        # Initialize exchange
        self.exchange = getattr(ccxt, self.exchange_id)({
            'apiKey': api_key,
            'secret': api_secret,
            'password': api_passphrase,  # Needed specifically for OKX
            'enableRateLimit': True
        })
        
        # Fetch actual fee structure if possible
        self.maker_fee = config['maker_fee']
        self.taker_fee = config['taker_fee']
        self.fee_discount = config['fee_discount']
        
        logger.info(f"Exchange handler initialized for {self.exchange_id}")
        
        # Try to update fees from exchange
        self.update_fees_from_exchange()
    
    def update_fees_from_exchange(self):
        """Fetch and update fee structure from the exchange"""
        try:
            # Load markets to ensure we have the latest data
            self.exchange.load_markets()
            
            # Some exchanges support fetching trading fees
            if hasattr(self.exchange, 'fetch_trading_fees'):
                fees = self.exchange.fetch_trading_fees()
                
                # Update our fee structure if we got valid data
                if fees:
                    if 'maker' in fees:
                        self.maker_fee = fees['maker']
                    if 'taker' in fees:
                        self.taker_fee = fees['taker']
                    
                    logger.info(f"Updated fees from exchange - Maker: {self.maker_fee*100:.4f}%, " +
                               f"Taker: {self.taker_fee*100:.4f}%")
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Could not fetch exchange fees: {e}. Using default values.")
            return False
    
    def get_current_prices(self, coins):
        """Fetch current prices for the specified coins"""
        prices = {}
        for coin in coins:
            pair = f"{coin}/{self.base_currency}"
            try:
                ticker = self.exchange.fetch_ticker(pair)
                prices[coin] = ticker['last']
            except Exception as e:
                logger.error(f"Error fetching price for {pair}: {str(e)}")
        return prices
    
    def fetch_ohlcv(self, coin, timeframe, limit=30):
        """Fetch OHLCV data for a specific coin"""
        pair = f"{coin}/{self.base_currency}"
        try:
            return self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {pair}: {str(e)}")
            return None
    
    def execute_buy(self, coin, amount, simulate=True):
        """Execute a buy order"""
        pair = f"{coin}/{self.base_currency}"
        try:
            if not simulate:
                order = self.exchange.create_market_buy_order(pair, amount)
                return order
            else:
                logger.info(f"SIMULATION: Buy {amount} of {coin}")
                return {"id": "simulation", "status": "closed", "amount": amount}
        except Exception as e:
            logger.error(f"Error executing buy order for {pair}: {str(e)}")
            return None
    
    def execute_sell(self, coin, amount, simulate=True):
        """Execute a sell order"""
        pair = f"{coin}/{self.base_currency}"
        try:
            if not simulate:
                order = self.exchange.create_market_sell_order(pair, amount)
                return order
            else:
                logger.info(f"SIMULATION: Sell {amount} of {coin}")
                return {"id": "simulation", "status": "closed", "amount": amount}
        except Exception as e:
            logger.error(f"Error executing sell order for {pair}: {str(e)}")
            return None