import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DividendService:
    def __init__(self):
        pass

    @st.cache_data(ttl=3600)
    def get_dividend_history(_self, portfolio_items: List[Any]) -> pd.DataFrame:
        """
        Fetches dividend history for the portfolio items using yfinance.
        Returns a DataFrame with: Date, Ticker, DividendPerShare, Quantity, TotalReceived
        """
        if not portfolio_items:
            return pd.DataFrame()

        data = []
        
        # Calculate start date (e.g., 2 years ago to have good history)
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        tickers_map = {item.ticker: item.quantity for item in portfolio_items}
        
        # Optimize: fetch all at once if possible, but yfinance handles single tickers better for dividends
        for item in portfolio_items:
            ticker_sa = f"{item.ticker}.SA"
            try:
                # Use Ticker object to get dividends
                stock = yf.Ticker(ticker_sa)
                # history(period="max") or specific start
                divs = stock.dividends
                
                # Filter by date
                # Ensure start_date is timezone-aware if divs index is, or naive if divs index is
                if divs.index.tz is not None:
                     # Convert to naive to simplify comparison or localize start_date
                     # Easier: Convert divs index to naive
                     divs.index = divs.index.tz_localize(None)
                
                divs = divs[divs.index >= pd.to_datetime(start_date)]
                
                for date, value in divs.items():
                    data.append({
                        "Date": date,
                        "Ticker": item.ticker,
                        "DividendPerShare": value,
                        "Quantity": item.quantity, # Using current quantity as proxy
                        "TotalReceived": value * item.quantity,
                        "Type": "Dividendo" # FIIs usually pay dividends (rendimentos)
                    })
            except Exception as e:
                print(f"Error fetching dividends for {item.ticker}: {e}")
                continue
                
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        # Ensure Date is timezone-naive for consistency
        if df['Date'].dt.tz is not None:
             df['Date'] = df['Date'].dt.tz_localize(None)
             
        df['MonthYear'] = df['Date'].dt.strftime('%m/%Y')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        
        return df.sort_values(by='Date', ascending=False)

    def get_monthly_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        
        # Group by MonthYear and sum TotalReceived
        monthly = df.groupby(['Year', 'Month', 'MonthYear'])['TotalReceived'].sum().reset_index()
        monthly = monthly.sort_values(by=['Year', 'Month'])
        return monthly

    def get_asset_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        
        # Last 12 months
        last_12m = datetime.now() - timedelta(days=365)
        df_12m = df[df['Date'] >= last_12m]
        
        dist = df_12m.groupby('Ticker')['TotalReceived'].sum().reset_index()
        dist = dist.sort_values(by='TotalReceived', ascending=False)
        return dist

    def get_last_dividends(self, tickers: List[str]) -> Dict[str, float]:
        """
        Fetches the last paid dividend for a list of tickers.
        Returns a dictionary {ticker: last_dividend_value}
        """
        result = {}
        for ticker in tickers:
            ticker_sa = f"{ticker}.SA"
            try:
                stock = yf.Ticker(ticker_sa)
                divs = stock.dividends
                if not divs.empty:
                    # Get last dividend
                    last_div = divs.iloc[-1]
                    result[ticker] = float(last_div)
                else:
                    result[ticker] = 0.0
            except Exception:
                result[ticker] = 0.0
        return result
