# Crypto Converter

There are 2 applications in this repo:

#### **Quote Consumer**

Application listens for trades in crypto exchanges (Currently Binance only) using Websocket API. Aggregates the trades
into 1 second timeframe candles and periodically stores the candles in Postgres Database. Application provides
API to get the latest candle from the memory for the ticker, API is available only internally for interservice communication
so that Currency Conversion app can get the latest fresh price of ticker.

#### **Currency Conversion**

Application provides http API to convert one crypto currency to another using for now only Binance real-time crypto prices.

## Quick Start

1. **Clone and setup**:

   ```bash
   cd /path/to/crypto_converter
   cp .env.example .env  # Copy and modify if needed env variables
   ```

2. **Build and run**:

   ```bash
   docker compose up --build
   ```

3. **Access the application docs**:
   - API: http://localhost:9000/docs

## Development

1. **Install UV package manager and packages**

   ```bash
   cd /path/to/crypto_converter
   cp .env.example .env  # Copy and modify if needed env variables
   pip install uv
   uv sync
   ```

2. **Run applications**
   ```bash
   # Run in separate terminals, currency_conversion is dependant on quote_consumer
   uv run python -m currency_conversion
   uv run python -m quote_consumer
   ```

## Linting & Formatting & Type Checking

Ruff is used for linting and formatting. Mypy for type checking

1. **Formatting**

   ```bash
   uv run scripts/format
   ```

1. **Linting**
   ```bash
   uv run scripts/lint
   ```
