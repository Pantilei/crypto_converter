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
