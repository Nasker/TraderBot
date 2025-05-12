# performance.py - Performance calculation module
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PerformanceCalculator:
    def __init__(self, exchange_handler, config):
        """Initialize performance calculator"""
        self.exchange = exchange_handler
        self.config = config
        self.performance_period = config['performance_period']
        
    def calculate_performance(self, coins):
        """
        Calculate performance metrics for all coins
        Returns dictionary of coins with their performance metrics
        """
        performance = {}
        
        for coin in coins:
            try:
                # Get historical OHLCV data
                ohlcv = self.exchange.fetch_ohlcv(coin, self.performance_period, limit=30)
                if not ohlcv:
                    continue
                    
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Calculate various performance metrics
                change_pct = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
                
                # Calculate volatility (standard deviation of returns)
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * 100
                
                # Simple momentum indicator (RSI)
                delta = df['close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).fillna(50).iloc[-1]
                
                # Volume trend
                vol_change = (df['volume'].iloc[-5:].mean() / df['volume'].iloc[-10:-5].mean() - 1) * 100
                
                # Combine metrics into a composite score
                # Higher score = better performance
                score = change_pct - volatility * 0.5 + (rsi - 50) * 0.3 + vol_change * 0.2
                
                performance[coin] = {
                    'price': df['close'].iloc[-1],
                    'change_pct': change_pct,
                    'volatility': volatility,
                    'rsi': rsi,
                    'volume_trend': vol_change,
                    'score': score
                }
                
                logger.debug(f"{coin} performance: {score:.2f}")
                
            except Exception as e:
                logger.error(f"Error calculating performance for {coin}: {str(e)}")
        
        return performance