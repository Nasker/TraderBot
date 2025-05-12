# fee_calculator.py - Fee calculation utilities
import logging

logger = logging.getLogger(__name__)

class FeeCalculator:
    def __init__(self, exchange_handler, config):
        """Initialize fee calculator"""
        self.exchange = exchange_handler
        self.config = config
        self.maker_fee = exchange_handler.maker_fee
        self.taker_fee = exchange_handler.taker_fee
        self.fee_discount = config['fee_discount']
        
        # Calculate effective fees
        self.effective_maker_fee = self.maker_fee * (1 - self.fee_discount)
        self.effective_taker_fee = self.taker_fee * (1 - self.fee_discount)
        
        # For most market orders, we'll use taker fee
        self.standard_fee = self.effective_taker_fee
        
        # Calculate minimum profit threshold with fees
        self.min_profit_threshold = config['min_profit_threshold']
        
        logger.info(f"Fee calculator initialized - Effective fees: Maker {self.effective_maker_fee*100:.4f}%, " +
                   f"Taker {self.effective_taker_fee*100:.4f}%")
    
    def calculate_buy_fee(self, amount):
        """Calculate fee for buying an asset"""
        return amount * self.standard_fee
    
    def calculate_sell_fee(self, amount):
        """Calculate fee for selling an asset"""
        return amount * self.standard_fee
    
    def calculate_round_trip_fee(self, amount):
        """Calculate round-trip fee (buy + sell)"""
        return amount * self.standard_fee * 2
    
    def calculate_fee_adjusted_return(self, from_coin, to_coin, performance_data, base_currency):
        """
        Calculate the fee-adjusted expected return for a trade
        Returns expected percentage gain/loss after fees
        """
        if from_coin == base_currency:
            # We're just buying, so expected return is the performance score
            # minus one fee (we're not selling yet)
            expected_return = performance_data[to_coin]['score'] / 100  # Convert to decimal
            fee_impact = self.standard_fee
            
        elif to_coin == base_currency:
            # We're just selling, so no expected future return beyond selling fee
            # If the coin has negative performance, selling is beneficial
            expected_return = -performance_data[from_coin]['score'] / 100 if performance_data[from_coin]['score'] < 0 else 0
            fee_impact = self.standard_fee
            
        else:
            # Trading between two cryptos
            # Expected return is the difference in performance minus round-trip fees
            from_score = performance_data[from_coin]['score']
            to_score = performance_data[to_coin]['score']
            performance_diff = (to_score - from_score) / 100  # Convert to decimal
            fee_impact = self.standard_fee * 2  # Two trades: sell first coin, buy second coin
            
            expected_return = performance_diff
        
        # Net return after fees
        net_return = expected_return - fee_impact
        
        return net_return