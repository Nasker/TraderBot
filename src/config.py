# config.py - Configuration settings for the crypto trading bot

# Default configuration
DEFAULT_CONFIG = {
    # Exchange settings
    "exchange_id": "okx",
    "base_currency": "USDT",
    "trade_coins": ["BTC", "ETH", "SOL", "ADA", "DOT"],
    
    # Trading parameters
    "trade_amount": 100,
    "performance_period": "1d",
    "check_interval": 3600,  # 1 hour in seconds
    
    # Fee structure (defaults - will be updated from exchange if possible)
    "maker_fee": 0.0008,     # 0.08%
    "taker_fee": 0.0010,     # 0.10%
    "fee_discount": 0,       # No discount by default
    
    # Trading thresholds
    "min_profit_threshold": 0.005,  # 0.5% minimum profit after fees
    
    # Safety settings
    "max_trades_per_day": 5,
    "stop_loss_percent": 5.0,       # 5% stop loss
    
    # Paths
    "data_dir": "data"
}

def load_config(config_file=None):
    """Load configuration from file if exists, otherwise use defaults"""
    import os
    import json
    
    config = DEFAULT_CONFIG.copy()
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    # Create data directory if it doesn't exist
    os.makedirs(config['data_dir'], exist_ok=True)
    
    return config