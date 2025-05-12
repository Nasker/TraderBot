# Fee-Aware Crypto Trading Bot

A cryptocurrency trading bot that makes trading decisions based on performance metrics while accounting for exchange fees.

## Features

- Compares performance across multiple cryptocurrencies
- Fee-aware trading decisions to ensure profitability
- Supports multiple exchanges through the CCXT library
- Simulation mode for testing strategies without real trades
- Detailed logging and trade history
# Fee-Aware Crypto Trading Bot

A cryptocurrency trading bot that makes trading decisions based on performance metrics while accounting for exchange fees.

## Features

- Compares performance across multiple cryptocurrencies
- Fee-aware trading decisions to ensure profitability
- Supports multiple exchanges through the CCXT library
- Simulation mode for testing strategies without real trades
- Detailed logging and trade history

## Installation

1. Clone this repository:
git clone https://github.com/yourusername/crypto-trading-bot.git cd crypto-trading-bot


2. Install dependencies:
pip install -r requirements.txt

3. Create a `.env` file with your API keys:
API_KEY=your_api_key_here API_SECRET=your_api_secret_here API_PASSPHRASE=your_api_passphrase_here # Required for some exchanges like OKX

## Usage

### Running in Simulation Mode

To run the bot in simulation mode (no real trades):
python main.py --simulate


### Running a Single Cycle

To run a single trading cycle and exit:
python main.py --once

### Running in Live Trading Mode

To run the bot with real trading:
python main.py

**WARNING**: Live trading involves financial risk. Use at your own risk.

## Configuration

Edit the `config.py` file to customize:

- Exchange settings
- Trading pairs
- Trade amount
- Performance metrics
- Fee settings

## License

CREATIVE COMMMONS

## Personal Disclaimer

- IMHO Cryptos are a scam and kinda evil too, but if you can make yourself some money out of them, go on, this bot is for free and public forever
