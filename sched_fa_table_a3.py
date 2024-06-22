import requests
import pandas as pd
from datetime import datetime, timedelta

# Alpha Vantage API Key - Replace with your own API key
ALPHA_VANTAGE_API_KEY = 'YOUR_API_KEY'

# Function to fetch daily stock market data (Google) and filter to 2023
def fetch_daily_stock_data():
    endpoint = f'https://www.alphavantage.co/query'
    function = 'TIME_SERIES_DAILY'
    symbol = 'GOOG'
    params = {
        'function': function,
        'symbol': symbol,
        'outputsize': 'full',
        'apikey': ALPHA_VANTAGE_API_KEY,
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    # Convert JSON response to DataFrame
    df = pd.DataFrame(data['Time Series (Daily)']).T
    df.index = pd.to_datetime(df.index)  # Convert index to datetime if not already
    df.sort_index(inplace=True)
    
    # Filter data to year 2023
    df = df[df.index.year == 2023]

    return df

# Function to fetch daily USD to INR exchange rates and filter to 2023
def fetch_daily_exchange_rates():
    endpoint = f'https://www.alphavantage.co/query'
    function = 'FX_DAILY'
    from_currency = 'USD'
    to_currency = 'INR'
    params = {
        'function': function,
        'from_symbol': from_currency,
        'to_symbol': to_currency,
        'outputsize': 'full',  # Get all data
        'apikey': ALPHA_VANTAGE_API_KEY,
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    # Convert JSON response to DataFrame
    df = pd.DataFrame(data['Time Series FX (Daily)']).T
    df.index = pd.to_datetime(df.index)  # Convert index to datetime if not already
    df.sort_index(inplace=True)
    
    # Filter data to year 2023
    df = df[df.index.year == 2023]

    return df

# Function to find next available trading date
def find_next_trading_date(stock_data, target_date):
    next_date = target_date + timedelta(days=1)
    while next_date <= stock_data.index[-1]:  # Check until the last date in stock_data
        if next_date in stock_data.index:
            return next_date
        next_date += timedelta(days=1)
    return None

# Function to find peak value from a given date to end of year (using vectorized operations)
def find_peak_value(stock_data, exchange_rates, start_date):
    # Filter data from start_date to end of year
    filtered_stock_data = stock_data.loc[start_date:]
    
    # Extract relevant columns
    prices = filtered_stock_data['4. close'].astype(float)
    exchange_rate = float(exchange_rates.loc[start_date]['4. close'])
    
    # Calculate peak value using vectorized operations
    peak_value = (prices * exchange_rate).max()
    
    return peak_value

# Function to generate output for a given date
def generate_output(investment_value, peak_investment_value, closing_value, target_date, num_stocks, exchange_rate, stock_price, closing_stock_price, peak_value, post_taxed_stocks):
    output = []
    formatted_date = target_date.strftime('%B %d, %A, %Y')
        
    output.append(f"Date: {formatted_date}, Stocks vested: {num_stocks}, Stocks withheld: {post_taxed_stocks}, Stocks Taxed: {num_stocks - post_taxed_stocks}")
    output.append(f"Investment Value: ₹{investment_value:.2f} at FMV {stock_price}")
    investment_value_taxed = stock_price * post_taxed_stocks * exchange_rate
    output.append(f"Investment Value (Taxed): ₹{investment_value_taxed:.2f} at FMV {stock_price}")
    output.append(f"Taxed Amount: ₹{(investment_value - investment_value_taxed):.2f} at FMV {stock_price}")
    output.append(f"Peak Values of investment: ₹{peak_investment_value:.2f} at FMV {peak_value}")
    output.append(f"Closing Value: ₹{closing_value:.2f} at FMV {closing_stock_price}")
    output.append(f"INR/USD Conversion Rate: {exchange_rate:.4f}")
    output.append("")  # Add a blank line for better readability
    
    return output


# Function to process data and generate required output
def process_data(stock_data, exchange_rates, num_stocks, net_stocks):
    output = []
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

    for month in months:
        target_date = pd.Timestamp(f'2023-{month}-24')

        # Check if data for 24th of the month is available
        if target_date not in stock_data.index or target_date not in exchange_rates.index:
            # If data for 24th of the month is not available, find next available trading date
            next_date = find_next_trading_date(stock_data, target_date)
            if next_date:
                # Update target_date to next available trading date
                target_date = next_date
            else:
                # Handle no next trading date found case
                output.append(f"No data available for 24/{month}/23.")  
                output.append("")  # Add a blank line for better readability
                continue
        
        # Get necessary data for generating output
        stock_price = float(stock_data.loc[target_date]['4. close'])
        exchange_rate = float(exchange_rates.loc[target_date]['4. close'])
        peak_value = find_peak_value(stock_data, exchange_rates, target_date)
        individual_stocks = float(num_stocks[months.index(month)])
        post_taxed_stocks = float(net_stocks[months.index(month)])
        closing_stock_price = float(stock_data.iloc[-1]['4. close'])
        closing_exchange_rate = float(exchange_rates.iloc[-1]['4. close'])

        # Calculate investment-related details
        investment_value = stock_price * individual_stocks * exchange_rate
        closing_value = closing_stock_price * post_taxed_stocks * closing_exchange_rate
        peak_investment_value = peak_value * post_taxed_stocks
        
        # Generate output for the updated target_date
        output.extend(generate_output(investment_value, peak_investment_value, closing_value, target_date, individual_stocks, exchange_rate, stock_price, closing_stock_price, peak_value, post_taxed_stocks))

    return output

if __name__ == "__main__":
    # Input
    num_stocks = ['200', '250', '300', '350', '400', '450', '500', '550', '600', '650', '230', '123']
    net_stocks = ['5.504', '5.504', '5.504', '5.505', '4.817', '5.504', '5.505', '5.504', '5.504', '5.504', '5.504', '5.504']

    # Fetch and filter daily stock market data for year 2023
    stock_data = fetch_daily_stock_data()
    
    # Fetch and filter daily exchange rates data for year 2023
    exchange_rates = fetch_daily_exchange_rates()
    
    # Process data and generate output
    output = process_data(stock_data, exchange_rates, num_stocks, net_stocks)
    
    # Print the output
    for line in output:
        print(line)
