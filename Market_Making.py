import requests
from time import sleep
import signal

# Initialize shutdown flag
shutdown = False

def signal_handler(signum, frame):
    global shutdown
    print("Shutdown signal received")
    shutdown = True

# Set the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# API Configuration
api_endpoint = "http://localhost:16620"
API_KEY = "----"  # Replace with your actual API key
headers = {"X-API-Key": API_KEY}

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
    session = requests.Session()

    while not shutdown:
        try:
            tenders = get_tenders(session)
            for tender in tenders:
                execute_tender_if_profitable(session, tender)
                adjust_positions_based_on_performance(session)
            
            
            sleep(1)  # Adjust based on your requirements
        except ApiException as e:
            print(f"API error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            # Add any cleanup here if needed
            pass

    print("Exiting main loop.")

if __name__ == "__main__":
    main_loop()
