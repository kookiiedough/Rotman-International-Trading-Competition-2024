import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

# TODO: API key should ideally be managed via a configuration file or environment variables
ALPHA_VANTAGE_API_URL = "https://www.alphavantage.co/query"

def get_daily_adjusted_stock_data(api_key: str, symbol: str):
    """
    Fetches the daily adjusted time series data for a given stock symbol from Alpha Vantage.

    Args:
        api_key: Your Alpha Vantage API key.
        symbol: The stock symbol (e.g., "IBM").

    Returns:
        A dictionary containing the time series data if successful, None otherwise.
    """
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact"  # Or "full" for more data
    }

    try:
        response = requests.get(ALPHA_VANTAGE_API_URL, params=params, timeout=10) # Added timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        data = response.json()

        if "Error Message" in data:
            logger.error(f"Alpha Vantage API Error for {symbol}: {data['Error Message']}")
            return None
        
        if "Time Series (Daily)" not in data:
            logger.error(f"Unexpected response format for {symbol}: 'Time Series (Daily)' key not found. Full response: {data}")
            return None
        
        logger.info(f"Successfully fetched daily adjusted data for {symbol}.")
        return data["Time Series (Daily)"]

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while fetching data for {symbol}.")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error occurred while fetching data for {symbol}.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {symbol}: {e}")
        return None
    except Exception as e: # Catching other potential errors like JSONDecodeError if response is not JSON
        logger.error(f"An unexpected error occurred during API call for {symbol}: {e}")
        return None

def calculate_simple_insights(time_series_data: dict, n_days: int):
    """
    Calculates simple financial insights from daily adjusted time series data.

    Args:
        time_series_data: A dictionary from Alpha Vantage's "Time Series (Daily)" key.
                          Example: {"2023-10-20": {"1. open": "...", "4. close": "150.00", ...}, ...}
        n_days: The period for calculations (e.g., 20 for 20-day SMA).

    Returns:
        A dictionary with calculated insights, or None if data is insufficient.
        Example: {"n_day_sma": 145.50, "n_day_percentage_change": 3.0}
    """
    if not time_series_data:
        logger.warning("Time series data is empty or None. Cannot calculate insights.")
        return None
    
    if len(time_series_data) < n_days:
        logger.warning(f"Insufficient data for {n_days}-day calculations. Need at least {n_days} days, got {len(time_series_data)}.")
        return None

    # Alpha Vantage returns dates as keys, most recent first.
    # We need to sort them to ensure correct chronological order for calculations.
    # However, for SMA and N-day change, we typically use the most recent N days.
    # The default order (most recent first) is suitable if we take the first N entries.
    
    dates = list(time_series_data.keys())
    
    # Ensure dates are sorted from most recent to oldest if not already guaranteed
    # For AlphaVantage, this is usually the case, but explicit sort adds robustness
    try:
        # Attempt to sort dates; can fail if date strings are inconsistent (though unlikely for AV)
        sorted_dates = sorted(dates, reverse=True)
    except Exception as e: # Catching potential errors during sort
        logger.error(f"Could not sort dates due to: {e}. Assuming default order is most recent first.")
        sorted_dates = dates # Proceed with unsorted (original order) if sort fails

    closing_prices = []
    for i in range(n_days):
        if i >= len(sorted_dates):
            logger.error(f"Ran out of dates while collecting closing prices for {n_days}-day calculation. Only {len(sorted_dates)} dates available.")
            return None
        
        date = sorted_dates[i]
        try:
            daily_data = time_series_data[date]
            closing_prices.append(float(daily_data['4. close']))
        except KeyError:
            logger.error(f"'4. close' or date '{date}' not found in time_series_data for a day within the {n_days}-day range.")
            return None
        except ValueError:
            logger.error(f"Could not parse closing price for {date} as float: {time_series_data[date].get('4. close')}")
            return None
            
    if len(closing_prices) < n_days:
        logger.warning(f"Insufficient valid closing prices for {n_days}-day SMA. Found {len(closing_prices)} after processing.")
        return None

    # 1. N-day Simple Moving Average (SMA)
    # Uses the n_days most recent prices (which are at the start of closing_prices list)
    n_day_sma = sum(closing_prices) / n_days

    # 2. N-day Percentage Change
    # closing_prices[0] is the most recent, closing_prices[n_days-1] is the price from n_days ago.
    most_recent_close = closing_prices[0]
    close_n_days_ago = closing_prices[n_days-1]
    
    if close_n_days_ago == 0: # Avoid division by zero
        logger.warning(f"Cannot calculate N-day percentage change for period ending {sorted_dates[0]}: price {n_days} days ago was zero.")
        n_day_percentage_change = float('inf') if most_recent_close > 0 else (float('-inf') if most_recent_close < 0 else 0.0)
    else:
        n_day_percentage_change = ((most_recent_close - close_n_days_ago) / close_n_days_ago) * 100

    insights_result = {
        "n_day_sma": round(n_day_sma, 2),
        "n_day_percentage_change": round(n_day_percentage_change, 2)
    }
    logger.info(f"Successfully calculated insights for {n_days} days, ending {sorted_dates[0]}: {insights_result}")
    return insights_result

if __name__ == '__main__':
    # --- IMPORTANT ---
    # Replace "YOUR_ACTUAL_API_KEY" with your real Alpha Vantage API key for testing.
    # For the purpose of this exercise, if you have a key, you can uncomment and test.
    
    # logger.info("Starting Alpha Vantage client test...")
    # test_api_key = "YOUR_ACTUAL_API_KEY" 
    # if test_api_key == "YOUR_ACTUAL_API_KEY":
    #     logger.warning("Using placeholder API key for testing. Please replace with your actual key.")

    # test_symbol = "IBM"
    # n_days_for_insights = 20

    # logger.info(f"Attempting to fetch data for {test_symbol}...")
    # stock_data_ts = get_daily_adjusted_stock_data(test_api_key, test_symbol)

    # if stock_data_ts:
    #     logger.info(f"Successfully fetched data for {test_symbol}.")
    #     # Example: logger.debug(f"Sample of data points (first 5): {dict(list(stock_data_ts.items())[:5])}")
        
    #     logger.info(f"Calculating {n_days_for_insights}-day insights for {test_symbol}...")
    #     insights = calculate_simple_insights(stock_data_ts, n_days_for_insights)
    #     if insights:
    #         logger.info(f"Insights for {test_symbol}: "
    #                     f"{n_days_for_insights}-Day SMA: {insights.get('n_day_sma')}, "
    #                     f"{n_days_for_insights}-Day Percentage Change: {insights.get('n_day_percentage_change')}%")
    #     else:
    #         logger.warning(f"Could not calculate insights for {test_symbol}.")
    # else:
    #     logger.error(f"Failed to fetch data for {test_symbol}.")

    # Example with a 'demo' key
    logger.info("Attempting to fetch data for MSFT with a 'demo' key (expected to be limited or fail)...")
    demo_api_key = "demo"
    demo_symbol = "MSFT"
    n_days_demo = 20

    demo_stock_data_ts = get_daily_adjusted_stock_data(demo_api_key, demo_symbol)

    if demo_stock_data_ts:
        logger.info(f"Successfully fetched data for {demo_symbol} using '{demo_api_key}' key (data might be limited/cached).")
        
        logger.info(f"Calculating {n_days_demo}-day insights for {demo_symbol} with '{demo_api_key}' key...")
        demo_insights = calculate_simple_insights(demo_stock_data_ts, n_days_demo)
        if demo_insights:
            logger.info(f"Insights for {demo_symbol} (demo key): "
                        f"{n_days_demo}-Day SMA: {demo_insights.get('n_day_sma')}, "
                        f"{n_days_demo}-Day Percentage Change: {demo_insights.get('n_day_percentage_change')}%")
        else:
            logger.warning(f"Could not calculate insights for {demo_symbol} with '{demo_api_key}' key (likely due to limited data with demo key).")
    else:
        logger.error(f"Failed to fetch data for {demo_symbol} using '{demo_api_key}' key, as can happen with restricted keys or rate limits.")
    
    logger.info("Alpha Vantage client test finished.")
