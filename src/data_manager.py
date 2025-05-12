# data_manager.py - Data storage and retrieval
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, config):
        """Initialize data manager"""
        self.config = config
        self.data_dir = config['data_dir']
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize trade history
        self.trade_history = []
        self.load_trade_history()
        
        # Portfolio tracking
        self.portfolio_snapshots = []
        self.load_portfolio_snapshots()
        
        logger.info(f"Data manager initialized with {len(self.trade_history)} historical trades")
    
    def load_trade_history(self):
        """Load trade history from file"""
        history_file = os.path.join(self.data_dir, 'trade_history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.trade_history = json.load(f)
                logger.info(f"Loaded {len(self.trade_history)} trades from history")
            except Exception as e:
                logger.error(f"Error loading trade history: {e}")
    
    def save_trade_history(self):
        """Save trade history to file"""
        history_file = os.path.join(self.data_dir, 'trade_history.json')
        try:
            with open(history_file, 'w') as f:
                json.dump(self.trade_history, f, indent=2, default=str)
            logger.debug("Trade history saved")
        except Exception as e:
            logger.error(f"Error saving trade history: {e}")
    
    def add_trade(self, trade_data):
        """Add a trade to history and save"""
        self.trade_history.append(trade_data)
        self.save_trade_history()
    
    def load_portfolio_snapshots(self):
        """Load portfolio snapshots from file"""
        snapshot_file = os.path.join(self.data_dir, 'portfolio_snapshots.json')
        if os.path.exists(snapshot_file):
            try:
                with open(snapshot_file, 'r') as f:
                    self.portfolio_snapshots = json.load(f)
                logger.info(f"Loaded {len(self.portfolio_snapshots)} portfolio snapshots")
            except Exception as e:
                logger.error(f"Error loading portfolio snapshots: {e}")
    
    def save_portfolio_snapshot(self, holdings, prices, total_value):
        """Save a snapshot of the current portfolio"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'holdings': holdings,
            'prices': prices,
            'total_value': total_value
        }
        self.portfolio_snapshots.append(snapshot)
        
        # Save to file
        snapshot_file = os.path.join(self.data_dir, 'portfolio_snapshots.json')
        try:
            with open(snapshot_file, 'w') as f:
                json.dump(self.portfolio_snapshots, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving portfolio snapshot: {e}")