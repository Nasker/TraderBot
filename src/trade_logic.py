# trade_logic.py - Trading decision logic
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradeLogic:
    def __init__(self, exchange_handler, fee_calculator, data_manager, config):
        """Initialize trade logic"""
        self.exchange = exchange_handler
        self.fee_calc = fee_calculator
        self.data_manager = data_manager
        self.config = config
        
        self.base_currency = config['base_currency']
        self.trade_coins = config['trade_coins']
        self.trade_amount = config['trade_amount']
        self.min_profit_threshold = config['min_profit_threshold']
        
        # Initialize holdings
        self.holdings = {coin: 0 for coin in self.trade_coins}
        self.holdings[self.base_currency] = self.trade_amount
        
        # Trading stats
        self.total_fees_paid = 0
        self.trades_executed = 0
        self.daily_trade_count = 0
        self.last_trade_day = None
        
        logger.info(f"Trade logic initialized with {len(self.trade_coins)} coins")
    
    def reset_daily_trade_count(self):
        """Reset daily trade count if it's a new day"""
        today = datetime.now().date()
        if self.last_trade_day != today:
            self.daily_trade_count = 0
            self.last_trade_day = today
            return True
        return False
    
    def decide_trades(self, performance_data, prices):
        """
        Decide which trades to make based on performance data,
        accounting for trading fees
        Returns list of trades to execute (sell_coin, buy_coin, expected_return)
        """
        # Reset daily trade count if needed
        self.reset_daily_trade_count()
        
        # Check if we've hit the daily trade limit
        if self.daily_trade_count >= self.config['max_trades_per_day']:
            logger.info(f"Daily trade limit reached ({self.config['max_trades_per_day']}). No trades will be executed.")
            return []
        
        # Sort coins by performance score
        ranked_coins = sorted(performance_data.items(), 
                              key=lambda x: x[1]['score'], 
                              reverse=True)
        
        trades = []
        current_holdings = []
        
        # Find what we're currently holding
        for coin, amount in self.holdings.items():
            if coin != self.base_currency and amount > 0:
                current_holdings.append(coin)
        
        # Get top performing coin
        top_coin = ranked_coins[0][0]
        
        # If we're holding base currency and there's a good performer, consider buying it
        if self.holdings[self.base_currency] >= self.trade_amount:
            # Calculate expected return after fees
            expected_return = self.fee_calc.calculate_fee_adjusted_return(
                self.base_currency, top_coin, performance_data, self.base_currency
            )
            
            # Only buy if expected return is positive after fees
            if expected_return > self.min_profit_threshold:
                trades.append((self.base_currency, top_coin, expected_return))
                logger.info(f"Planning to buy {top_coin} using {self.base_currency}, " +
                           f"expected return: {expected_return*100:.2f}% after fees")
            else:
                logger.info(f"Holding {self.base_currency}: Expected return after fees " +
                           f"({expected_return*100:.2f}%) below threshold ({self.min_profit_threshold*100:.2f}%)")
        
        # If we're holding any bottom performers, consider selling them
        for coin, perf in reversed(ranked_coins):
            if coin in current_holdings and perf['score'] < 0:
                # Calculate expected return of selling to base currency
                expected_return = self.fee_calc.calculate_fee_adjusted_return(
                    coin, self.base_currency, performance_data, self.base_currency
                )
                
                # Selling poor performers might be worth it even with fees
                if expected_return > -self.fee_calc.standard_fee:  # If we lose less by selling than keeping
                    trades.append((coin, self.base_currency, expected_return))
                    logger.info(f"Planning to sell {coin} due to poor performance " +
                               f"(score: {perf['score']:.2f}, expected return: {expected_return*100:.2f}% after fees)")
                else:
                    logger.info(f"Not selling {coin} despite poor performance - " +
                               f"selling cost ({self.fee_calc.standard_fee*100:.2f}%) exceeds potential benefit")
        
        # Consider rotation from lower performing to top performer
        for coin in current_holdings:
            if coin != top_coin:
                # Calculate expected return of rotation
                expected_return = self.fee_calc.calculate_fee_adjusted_return(
                    coin, top_coin, performance_data, self.base_currency
                )
                
                # Only rotate if expected return exceeds our minimum threshold
                if expected_return > self.min_profit_threshold:
                    trades.append((coin, top_coin, expected_return))
                    logger.info(f"Planning to rotate from {coin} to {top_coin}, " +
                               f"expected return: {expected_return*100:.2f}% after fees")
                else:
                    coin_score = performance_data[coin]['score']
                    top_score = performance_data[top_coin]['score']
                    diff = top_score - coin_score
                    
                    logger.info(f"Not rotating {coin}->{top_coin}: Performance diff {diff:.2f}% " +
                               f"not sufficient after fees ({self.min_profit_threshold*100:.2f}%)")
        
        return trades
    
    def execute_trade(self, sell_coin, buy_coin, prices, expected_return, simulate=True):
        """
        Execute a trade from sell_coin to buy_coin
        Returns (success, fee_paid, trade_record)
        """
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'sell_coin': sell_coin,
            'buy_coin': buy_coin,
            'expected_return': expected_return
        }
        
        try:
            if sell_coin == self.base_currency:
                # We're buying a crypto with base currency
                trade_amount = min(self.holdings[self.base_currency], self.trade_amount)
                if trade_amount <= 0:
                    logger.warning(f"Insufficient {self.base_currency} balance")
                    return False, 0, None
                    
                fee_amount = self.fee_calc.calculate_buy_fee(trade_amount)
                effective_amount = trade_amount - fee_amount
                
                crypto_amount = effective_amount / prices[buy_coin]
                
                logger.info(f"Buying {crypto_amount:.6f} {buy_coin} at {prices[buy_coin]} {self.base_currency}")
                logger.info(f"Fee: {fee_amount:.6f} {self.base_currency} ({self.fee_calc.standard_fee*100:.3f}%)")
                
                # Execute the trade
                if not simulate:
                    order = self.exchange.execute_buy(buy_coin, crypto_amount)
                    if not order:
                        logger.error("Buy order failed")
                        return False, 0, None
                
                # Update holdings
                self.holdings[self.base_currency] -= trade_amount
                self.holdings[buy_coin] += crypto_amount
                
                # Complete trade record
                trade_record.update({
                    'type': 'buy',
                    'amount': crypto_amount,
                    'price': prices[buy_coin],
                    'fee': fee_amount,
                    'fee_currency': self.base_currency,
                    'simulated': simulate
                })
                
                # Update stats
                self.total_fees_paid += fee_amount
                self.trades_executed += 1
                self.daily_trade_count += 1
                
                # Save trade to history
                self.data_manager.add_trade(trade_record)
                
                return True, fee_amount, trade_record
                
            elif buy_coin == self.base_currency:
                # We're selling a crypto for base currency
                amount_to_trade = self.holdings[sell_coin]
                
                if amount_to_trade <= 0:
                    logger.warning(f"Insufficient {sell_coin} balance")
                    return False, 0, None
                
                base_amount = amount_to_trade * prices[sell_coin]
                fee_amount = self.fee_calc.calculate_sell_fee(base_amount)
                net_base_amount = base_amount - fee_amount
                
                logger.info(f"Selling {amount_to_trade:.6f} {sell_coin} at {prices[sell_coin]} {self.base_currency}")
                logger.info(f"Fee: {fee_amount:.6f} {self.base_currency} ({self.fee_calc.standard_fee*100:.3f}%)")
                
                # Execute the trade
                if not simulate:
                    order = self.exchange.execute_sell(sell_coin, amount_to_trade)
                    if not order:
                        logger.error("Sell order failed")
                        return False, 0, None
                
                # Update holdings
                self.holdings[self.base_currency] += net_base_amount
                self.holdings[sell_coin] = 0
                
                # Complete trade record
                trade_record.update({
                    'type': 'sell',
                    'amount': amount_to_trade,
                    'price': prices[sell_coin],
                    'fee': fee_amount,
                    'fee_currency': self.base_currency,
                    'simulated': simulate
                })
                
                # Update stats
                self.total_fees_paid += fee_amount
                self.trades_executed += 1
                self.daily_trade_count += 1
                
                # Save trade to history
                self.data_manager.add_trade(trade_record)
                
                return True, fee_amount, trade_record
                
            else:
                # We're trading between two cryptos (requires two operations)
                amount_to_trade = self.holdings[sell_coin]
                
                if amount_to_trade <= 0:
                    logger.warning(f"Insufficient {sell_coin} balance")
                    return False, 0, None
                
                # Step 1: Sell to base currency
                base_amount = amount_to_trade * prices[sell_coin]
                sell_fee = self.fee_calc.calculate_sell_fee(base_amount)
                net_base_amount = base_amount - sell_fee
                
                # Step 2: Buy the new crypto
                buy_fee = self.fee_calc.calculate_buy_fee(net_base_amount)
                net_buy_amount = net_base_amount - buy_fee
                buy_amount = net_buy_amount / prices[buy_coin]
                
                total_fee = sell_fee + buy_fee
                
                logger.info(f"Rotating {amount_to_trade:.6f} {sell_coin} to {buy_amount:.6f} {buy_coin}")
                logger.info(f"Total fees: {total_fee:.6f} {self.base_currency} ({(total_fee/base_amount)*100:.3f}%)")
                
                # Execute the trades
                if not simulate:
                    # First sell
                    sell_order = self.exchange.execute_sell(sell_coin, amount_to_trade)
                    if not sell_order:
                        logger.error("Sell part of rotation failed")
                        return False, 0, None
                    
                    # Then buy
                    buy_order = self.exchange.execute_buy(buy_coin, buy_amount)
                    if not buy_order:
                        logger.error("Buy part of rotation failed")
                        return False, sell_fee, None
                
                # Update holdings
                self.holdings[sell_coin] = 0
                self.holdings[buy_coin] += buy_amount
                
                # Complete trade record
                trade_record.update({
                    'type': 'rotation',
                    'amount_sold': amount_to_trade,
                    'amount_bought': buy_amount,
                    'price_sold': prices[sell_coin],
                    'price_bought': prices[buy_coin],
                    'fee': total_fee,
                    'fee_currency': self.base_currency,
                    'simulated': simulate
                })
                
                # Update stats
                self.total_fees_paid += total_fee
                self.trades_executed += 1
                self.daily_trade_count += 1
                
                # Save trade to history
                self.data_manager.add_trade(trade_record)
                
                return True, total_fee, trade_record
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False, 0, None
    
    def calculate_portfolio_value(self, prices):
        """Calculate current portfolio value in base currency"""
        total_value = self.holdings[self.base_currency]
        
        for coin, amount in self.holdings.items():
            if coin != self.base_currency and coin in prices:
                coin_value = amount * prices[coin]
                total_value += coin_value
                
                if amount > 0:
                    logger.info(f"Holding {amount:.6f} {coin} worth {coin_value:.2f} {self.base_currency}")
        
        logger.info(f"Total portfolio value: {total_value:.2f} {self.base_currency}")
        return total_value
    
    def run_trading_cycle(self, simulate=True):
        """Run a complete trading cycle"""
        logger.info("Starting trading cycle")
        
        # Get current prices
        prices = self.exchange.get_current_prices(self.trade_coins)
        if not prices:
            logger.error("Failed to get prices, aborting trading cycle")
            return False
        
        # Calculate current portfolio value
        portfolio_value = self.calculate_portfolio_value(prices)
        
        # Calculate performance metrics
        performance = self.exchange.calculate_performance(self.trade_coins)
        
        # Decide on trades
        trades_to_execute = self.decide_trades(performance, prices)
        
        # Execute trades
        for sell_coin, buy_coin, expected_return in trades_to_execute:
            success, fee_paid, trade_record = self.execute_trade(
                sell_coin, buy_coin, prices, expected_return, simulate
            )
            
            if success:
                logger.info(f"Successfully executed trade: {sell_coin} -> {buy_coin}")
            else:
                logger.warning(f"Failed to execute trade: {sell_coin} -> {buy_coin}")
        
        # Save portfolio snapshot
        self.data_manager.save_portfolio_snapshot(self.holdings, prices, portfolio_value)
        
        return True