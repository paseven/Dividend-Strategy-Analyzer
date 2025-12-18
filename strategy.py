import yfinance as yf
import pandas as pd
from datetime import timedelta

def fetch_data(ticker):
    """
    Fetches historical data and dividends for the given ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch 5 years of history to ensure we cover enough ground
        history = stock.history(period="5y")
        dividends = stock.dividends
        return history, dividends
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None

def calculate_scalping_strategy(ticker, max_days=14):
    """
    Calculates the net gain % for the dividend scalping strategy.
    
    Strategy:
    1. Identify Ex-Dividend Dates in the last 5 years.
    2. Buy on Ex-Date - 1 (Close Price).
    3. Sell on Ex-Date + N (Close Price), for N = 1 to max_days.
    4. Calculate Net Gain % = ((Sell + Dividend - Buy) / Buy) * 100
    """
    history, dividends = fetch_data(ticker)
    
    if history is None or history.empty or dividends is None or dividends.empty:
        return pd.DataFrame() # Retun empty DF on failure

    results = []

    # Ensure dividends index is tz-naive or consistent with history
    dividends.index = dividends.index.tz_localize(None)
    history.index = history.index.tz_localize(None)

    # Filter dividends for the last 5 years (implicitly handled by history fetch, but good to be safe)
    # We iterate through each dividend event
    for date, div_amount in dividends.items():
        # Find the Ex-Date row. Note: 'date' in dividends is the execution date (Ex-Date)
        # We need to check if this date exists in our price history
        
        # If Ex-Date is not a trading day, find the next valid trading day? 
        # Usually Ex-Date is a trading day. Let's look for exact match first.
        
        if date not in history.index:
            # If ex-date is missing (e.g. weekend/adjustment), skip or look forward.
            # strict approach: skip
            continue
            
        ex_date_idx = history.index.get_loc(date)
        
        # We need to buy on Ex-Date - 1
        if ex_date_idx < 1:
            continue # Can't buy before history starts
            
        buy_date = history.index[ex_date_idx - 1]
        buy_price = history.loc[buy_date, "Close"]
        
        # Calculate gains for selling 1 to max_days after Ex-Date
        # Note: Sell Date = Ex-Date + (day_offset - 1)? 
        # Requirement: "Number of days beyond ex-div".
        # If I sell ON ex-div, that is 0 days beyond? Or is 1 day beyond = Ex-Div + 1?
        # Interpretation: "span from 1 day to 14 days". 
        # Let's assume Day 1 = Ex-Date (Sell immediately on Ex-Date)
        # Day 2 = Ex-Date + 1
        
        # Actually usually scalping means selling ON the ex-date (capture drop) or waiting for recovery.
        # Let's iterate N from 0 to max_days-1 (representing 1 to 14 holding days starting from Ex-Date)
        # OR: N from 0 (sell on Ex-Date) to 13?
        # Let's say: "Sell after optimal number of days". 
        # Let's simply track days relative to Ex-Date.
        # Day 0 = Ex-Date. Day 1 = Ex-Date + 1.
        
        for n in range(0, max_days):
            target_sell_idx = ex_date_idx + n
            
            if target_sell_idx >= len(history):
                break # History ends
                
            sell_date = history.index[target_sell_idx]
            sell_price = history.loc[sell_date, "Close"]
            
            # Net Gain Calculation
            # Gain = (Sell + Div - Buy)
            # % Gain = (Gain / Buy) * 100
            
            net_gain_pct = ((sell_price + div_amount - buy_price) / buy_price) * 100
            div_gain_pct = (div_amount / buy_price) * 100
            
            results.append({
                "Ex-Date": date,
                "Dividend": div_amount,
                "Buy Date": buy_date.date(),
                "Buy Price": buy_price,
                "Days Held After Ex-Div": n + 1, # 1-based index (1 = Sold on Ex-Date)
                "Sell Date": sell_date.date(),
                "Sell Price": sell_price,
                "Net Gain %": net_gain_pct,
                "Dividend Gain %": div_gain_pct
            })

    return pd.DataFrame(results)
