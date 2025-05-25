# Rotman-International-Trading-Competition-2024

Market making algo for RITC 2024

## Overview

This repository contains a market-making algorithm designed for the Rotman International Trading Competition (RITC). The core functionality involves interacting with the RITC trading platform to make markets, manage tenders, and adjust positions.

This version now includes an integration with Alpha Vantage to fetch and analyze external market data for additional insights.

## Features

*   Market making for specified securities.
*   Tender offer evaluation and execution.
*   Dynamic position adjustment based on proprietary logic.
*   **External Market Data Analysis:** Integration with Alpha Vantage to fetch daily stock data and calculate simple technical insights (SMA and percentage change).

## Setup and Configuration

### Dependencies

*   Python 3.x
*   `requests` library: Used for making HTTP requests to both the RITC platform and Alpha Vantage.
    ```bash
    pip install requests
    ```

### Configuration File (`config.json`)

To run the script, you need to create a `config.json` file in the root directory. This file stores your API keys and other settings.

1.  **Copy the template:**
    ```bash
    cp config.template.json config.json
    ```
2.  **Edit `config.json`:**
    Open `config.json` and fill in the required fields:

    ```json
    {
        "alpha_vantage_api_key": "YOUR_ALPHA_VANTAGE_API_KEY_HERE",
        "stocks_to_analyze": [
            {"symbol": "IBM", "n_days": 20},
            {"symbol": "MSFT", "n_days": 30}
        ],
        "trading_api_key": "YOUR_RITC_TRADING_API_KEY_HERE",
        "alpha_vantage_fetch_interval_seconds": 60
    }
    ```
    *   `alpha_vantage_api_key`: Your personal API key for Alpha Vantage.
    *   `stocks_to_analyze`: A list of stocks for which to fetch data and calculate insights from Alpha Vantage.
        *   `symbol`: The stock ticker symbol (e.g., "IBM", "MSFT").
        *   `n_days`: The period (in days) for calculating SMA and percentage change for that symbol.
    *   `trading_api_key`: Your API key for the RITC trading platform.
    *   `alpha_vantage_fetch_interval_seconds`: (Optional) How often, in seconds, the script should attempt to fetch data from Alpha Vantage. Defaults to 60 seconds if not specified.

    **Note:** `config.json` is included in `.gitignore` and should not be committed to version control as it contains sensitive API keys.

## Alpha Vantage Integration

The script now integrates with Alpha Vantage to:
1.  Fetch daily adjusted time series data for the stock symbols specified in `config.json`.
2.  Calculate the following for each stock:
    *   **N-day Simple Moving Average (SMA):** Based on the `n_days` configured for that stock.
    *   **N-day Percentage Change:** Based on the `n_days` configured for that stock.
3.  These calculated insights are logged to the console. This external data can be used to inform trading decisions, though the current script primarily logs these insights.

## Running the Script

Ensure you have created and configured `config.json` as described above.

To run the market making algorithm:

```bash
python Market_Making.py
```

The script will load its configuration from `config.json`, including API keys and stock analysis parameters. Logs, including those from the Alpha Vantage integration, will be printed to the console.

## Project Files

*   `Market_Making.py`: The main script containing the trading algorithm logic and Alpha Vantage integration.
*   `alpha_vantage_client.py`: A client module responsible for interacting with the Alpha Vantage API (fetching data and calculating basic insights).
*   `test_alpha_vantage_client.py`: Unit tests for the `alpha_vantage_client.py` module.
*   `config.template.json`: A template for the `config.json` configuration file.
*   `README.md`: This file.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.

## Logging

The script uses Python's `logging` module.
*   `alpha_vantage_client.py`: Logs API interactions and calculation steps.
*   `Market_Making.py`: Logs configuration loading, Alpha Vantage processing, and RITC platform interactions (though some RITC interaction logs might still be using `print`).

Logs are output to standard output and include timestamps, log level, and messages.

## Disclaimer

This software is for educational and experimental purposes only, specifically for the RITC competition. Trading financial markets involves risk, and this script is not financial advice.
