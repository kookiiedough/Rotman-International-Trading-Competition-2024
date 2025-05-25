import requests
from time import sleep
import signal
import json # For loading configuration
import logging # For logging
from alpha_vantage_client import get_daily_adjusted_stock_data, calculate_simple_insights

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

# Initialize shutdown flag
shutdown = False
# Global config variable
CONFIG = None

def load_config(config_path="config.json"):
    """Loads the configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file '{config_path}' not found. Please copy 'config.template.json' to '{config_path}' and fill in your API keys and stock symbols.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Could not parse '{config_path}'. Ensure it is valid JSON.")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while loading config from {config_path}: {e}")
        return None

def signal_handler(signum, frame):
    global shutdown
    logger.info("Shutdown signal received")
    shutdown = True

# Set the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# API Configuration - will be updated by load_config
api_endpoint = "http://localhost:16620" 
# API_KEY will be loaded from config
# headers will be set after config is loaded

# Profit/Loss Tracking
# profit_loss = 0
# profit_target = 350000
# loss_limit = -50000

class ApiException(Exception):
    pass

def get_market_data(session, ticker):
    """Fetch the current bid and ask for a given ticker."""
    url = f'{api_endpoint}/v1/securities/book'
    params = {'ticker': ticker}
    response = session.get(url, params=params, headers=headers)
    if response.ok:
        book = response.json()
        bid_price = book['bids'][0]['price'] if book['bids'] else None
        ask_price = book['asks'][0]['price'] if book['asks'] else None
        return bid_price, ask_price
    else:
        raise ApiException("Failed to fetch market data.")

def execute_tender_if_profitable(session, tender):
    """Execute tender if it's profitable based on current market prices."""
    bid_price, ask_price = get_market_data(session, tender['ticker'])

    if tender['action'] == 'BUY' and bid_price is not None and tender['price'] < bid_price:
        execute_tender(session, tender)
        print(f"Accepting BUY Tender ID: {tender['tender_id']}, Price: {tender['price']}, Quantity: {tender['quantity']}")
    elif tender['action'] == 'SELL' and ask_price is not None and tender['price'] > ask_price:
        execute_tender(session, tender)
        print(f"Accepting SELL Tender ID: {tender['tender_id']}, Price: {tender['price']}, Quantity: {tender['quantity']}")

def execute_tender(session, tender):
    """Execute a given tender."""
    accept_url = f"{api_endpoint}/v1/tenders/{tender['tender_id']}"
    response = session.post(accept_url, headers=headers)
    if response.ok:
        print(f"Tender ID: {tender['tender_id']} accepted.")
    else:
        print(f"Failed to accept tender ID: {tender['tender_id']}. Response: {response.text}")

def get_tenders(session):
    """Fetch current tenders."""
    url = f"{api_endpoint}/v1/tenders"
    response = session.get(url, headers=headers)
    if response.ok:
        return response.json()
    else:
        raise ApiException("Failed to fetch tenders.")




session = requests.Session()    

def sell_ticker(session, ticker, typee, quantity, price):
    """
    Place a sell order for a specific ticker by appending parameters to the URL.

    Args:
    - session: The requests.Session() object for HTTP requests.
    - ticker: The ticker symbol as a string.
    - typee: The order type ('LIMIT', 'MARKET', etc.) as a string.
    - quantity: The quantity to sell as an integer.
    - price: The price per unit as a float for LIMIT orders; ignored for MARKET orders.

    Returns:
    - The response JSON from the API if the order is successfully placed; otherwise, None.
    """
    order_params = {
        'ticker': ticker,
        'type': typee,
        'quantity': quantity,
        'action': 'SELL',
        'price': price,
    }

    order_url = f"{api_endpoint}/v1/orders"

    try:
        # Adding the API key to the headers if not already included
        local_headers = headers.copy()
        local_headers['X-API-Key'] = API_KEY  # Ensure this is correct as per your API requirements

        # Sending the request with parameters as query parameters, not JSON payload
        response = session.post(order_url, params=order_params, headers=local_headers)
        
        if response.ok:
            print(f"Successfully placed sell order for {quantity} of {ticker} at {price}.")
            return response.json()
        else:
            print(f"Failed to place sell order for {ticker}. Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error placing sell order for {ticker}: {e}")
        return None

def buy_ticker(session, ticker, typee, quantity, price):
    
    order_params = {
        'ticker': ticker,
        'type': typee,
        'quantity': quantity,
        'action': 'BUY',
        'price': price,
    }

    order_url = f"{api_endpoint}/v1/orders"

    try:
        # Adding the API key to the headers if not already included
        local_headers = headers.copy()
        local_headers['X-API-Key'] = API_KEY  # Ensure this is correct as per your API requirements

        # Sending the request with parameters as query parameters, not JSON payload
        response = session.post(order_url, params=order_params, headers=local_headers)
        
        if response.ok:
            print(f"Successfully placed BUY  order for {quantity} of {ticker} at {price}.")
            return response.json()
        else:
            print(f"Failed to place BUY order for {ticker}. Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error placing BUY  order for {ticker}: {e}")
        return None



def adjust_positions_based_on_performance(session):
    def get_position(session, ticker):
        position_url = f"{api_endpoint}/v1/securities?ticker={ticker}"
        try:
            response = session.get(position_url, headers=headers)
            if response.ok:
                positions = response.json()
                # If the API returns a list of positions, iterate to find the right one
                for position in positions:
                    if position['ticker'] == ticker:  # Adjust the key based on actual response structure
                        return position.get('position', 0)  # Adjust 'position' key as needed
                return 0  # Return 0 if ticker not found
            else:
                print(f"Failed to fetch position for {ticker}. Response: {response.text}")
                return 0
        except Exception as e:
            print(f"Error fetching position for {ticker}: {e}")
            return 0



    # Check RIT_U position
    rit_u_position = get_position(session, 'RIT_U')
    print(rit_u_position)

    # Check and adjust positions as per your strategy
    rit_u_position = get_position(session, 'RIT_U')
    if rit_u_position < 0:
        bid_price, ask_price = get_market_data(session, 'RIT_U')  # Fetch current market data
        # Now you have bid_price and ask_price for RIT_U, you can use them as needed
        if ask_price is not None:
          if abs(rit_u_position)<10000:
            buy_ticker(session, 'RIT_U', 'MARKET', abs(rit_u_position), ask_price)
          else:
            buy_ticker(session, 'RIT_U', 'MARKET', 10000, ask_price)
    # Similar logic for USD and CAD, adjusting with sell_ticker and potentially buy_ticker
    usd_position= get_position(session, 'USD')
    if usd_position < 0:
        bid_price, ask_price = get_market_data(session, 'RIT_U')  # Fetch current market data
        # Now you have bid_price and ask_price for RIT_U, you can use them as needed
        if ask_price is not None:
          if abs(usd_position)< 10000:
            sell_ticker(session, 'RIT_U', 'MARKET', abs(usd_position), ask_price)
          else:
            sell_ticker(session, 'RIT_U', 'MARKET',10000, ask_price)
    # Check CAD position
    cad_position = get_position(session, 'CAD')
    if cad_position < 0:
        # Logic to sell HAWK and DOVE to reduce CAD exposure
        print("Selling HAWK and DOVE to adjust CAD position")
        hawk_position = get_position(session, 'HAWK')
        dove_position = get_position(session, 'DOVE')
        Hbid_price, Hask_price = get_market_data(session, 'HAWK')
        Dbid_price, Dask_price = get_market_data(session, 'HAWK')
        if hawk_position > 0:  # Assuming we only sell if we have a long position
            sell_ticker(session, 'HAWK', hawk_position, Hbid_price)  # Placeholder for actual sell logic
        if dove_position > 0:  # Assuming we only sell if we have a long position
            sell_ticker(session, 'DOVE', dove_position, Dask_price)  # Placeholder for actual sell logic
    rit_c_position= get_position(session, 'RIT_C')
    
    if rit_c_position < 0:
        bid_price, ask_price = get_market_data(session, 'RIT_C')  # Fetch current market data
        # Now you have bid_price and ask_price for RIT_U, you can use them as needed
        if ask_price is not None:
          if abs(rit_c) < 10000:
            buy_ticker(session, 'RIT_C', 'MARKET', abs(rit_c_position), ask_price)
          else:
            buy_ticker(session, 'RIT_C', 'MARKET', 10000, ask_price)   
        
def tender_process(s):
    tender = get_tender(s)
    if tender:  # if tender offer contains orders operate on those orders
        for i in tender:  # Operate on each dictionary
            execute_tender(s,i)
            time.sleep(1)
                    
        portfolio = get_securities(s)
        for i in portfolio:
            if i['position'] != 0:
                exit_position(s, i['ticker'],i['position'])
def main_loop():
    """Main trading loop."""
    global CONFIG, headers # Allow modification of global headers

    if not CONFIG:
        logger.error("Configuration not loaded. Exiting main_loop.")
        return

    # Use trading_api_key from config for RITC platform
    ritc_api_key = CONFIG.get("trading_api_key", "----") 
    if ritc_api_key == "YOUR_TRADING_API_KEY_HERE" or ritc_api_key == "----":
        logger.warning("RITC Trading API key is not set in config.json or is still the default placeholder.")
    headers = {"X-API-Key": ritc_api_key} # Define headers here for global use if needed, or pass to functions

    alpha_vantage_api_key = CONFIG.get("alpha_vantage_api_key")
    if not alpha_vantage_api_key or alpha_vantage_api_key == "YOUR_API_KEY_HERE":
        logger.warning("Alpha Vantage API key is not set in config.json. External data fetching will fail.")
    
    stocks_to_analyze = CONFIG.get("stocks_to_analyze", [])
    if not stocks_to_analyze:
        logger.info("No stocks specified for Alpha Vantage analysis in config.json.")

    session = requests.Session()
    alpha_vantage_fetch_counter = 0
    iterations_per_av_fetch = CONFIG.get("alpha_vantage_fetch_interval_seconds", 60) # Default to 60s

    while not shutdown:
        try:
            # Existing tender processing logic
            tenders = get_tenders(session) 
            for tender in tenders:
                execute_tender_if_profitable(session, tender) # Assumes this function uses global `headers` or has it passed
            
            adjust_positions_based_on_performance(session) # Same assumption for headers

            # Alpha Vantage data fetching and insights
            if alpha_vantage_api_key and alpha_vantage_api_key != "YOUR_API_KEY_HERE" and stocks_to_analyze:
                if alpha_vantage_fetch_counter % iterations_per_av_fetch == 0:
                    for stock_info in stocks_to_analyze:
                        symbol = stock_info.get("symbol")
                        n_days = stock_info.get("n_days")

                        if not symbol or not n_days:
                            logger.warning(f"Skipping invalid stock entry in config: {stock_info}")
                            continue
                        
                        logger.info(f"Attempting to fetch Alpha Vantage data for {symbol}...")
                        try:
                            time_series_data = get_daily_adjusted_stock_data(alpha_vantage_api_key, symbol)
                            if time_series_data:
                                logger.info(f"Successfully fetched Alpha Vantage data for {symbol}.")
                                logger.info(f"Calculating {n_days}-day insights for {symbol}...")
                                insights = calculate_simple_insights(time_series_data, n_days)
                                if insights:
                                    logger.info(f"Insights for {symbol}: {n_days}-Day SMA: {insights.get('n_day_sma')}, {n_days}-Day % Change: {insights.get('n_day_percentage_change')}%")
                                else:
                                    logger.warning(f"Could not calculate insights for {symbol} from fetched data.")
                            else:
                                logger.warning(f"Failed to fetch Alpha Vantage data for {symbol}.")
                        except Exception as e: # Catch-all for this specific stock's AV processing
                            logger.exception(f"Unexpected error processing Alpha Vantage stock {symbol}: {e}")
            
            alpha_vantage_fetch_counter += 1
            sleep(1)
        except ApiException as e:
            logger.error(f"RITC API error in main_loop: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in main_loop: {e}")
        finally:
            pass

    logger.info("Exiting main loop.")

if __name__ == "__main__":
    logger.info("Application starting...")
    CONFIG = load_config()
    if CONFIG:
        API_KEY = CONFIG.get("trading_api_key", "----") 
        # headers will be set in main_loop after CONFIG is confirmed
        main_loop()
    else:
        logger.error("Could not start the application due to configuration errors.")
        # Consider sys.exit(1) here if appropriate for your deployment strategy
