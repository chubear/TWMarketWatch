"""
Data fetching utilities shared across measure modules
"""
from __future__ import annotations
import pandas as pd
import requests
from typing import Optional, Dict, Any, Union
from datetime import date
from sqlalchemy import text
from .config import Config

DateLike = Union[str, date, pd.Timestamp]


class DataFetcher:
    """Utility class for fetching data from API and database"""
    
    @staticmethod
    def detect_date_column(df: pd.DataFrame) -> str:
        """Detect the date column in the DataFrame"""
        datelike_columns = ['日期','年月', 'date', 'Date', 'datetime', 'Datetime', 'time', 'Time', 'trading_date', 'TradingDate']
        for col in datelike_columns:
            if col in df.columns:
                return col
        raise ValueError("No date-like column found in DataFrame")
    
    @staticmethod
    def fetch_from_api(
        stock_id: str,
        field: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.DataFrame:
        """Fetch data from the API"""
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        params = {
            'stock_id': stock_id,
            'start': start_str,
            'end': end_str,
            'fields': field,
            'format': 'json',
            'api_key': Config.API_KEY
        }

        try:
            response = requests.get(Config.API_URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API returned error status: {result.get('status')}")
            
            data = result.get("data", {}).get(stock_id, {}).get("data", [])
            df = pd.DataFrame.from_records(data)
            
            date_col = DataFetcher.detect_date_column(df)
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)

            return df

        except requests.RequestException as e:
            raise ConnectionError(f"API request failed: {e}")
    
    @staticmethod
    def fetch_from_db(
        field: str,
        query: str,
        engine,
        params: Optional[Dict[str, Any]] = None,
    ) -> pd.Series:
        """Fetch data from the database"""
        try:        
            df = pd.read_sql(text(query), engine, params=params)
            
            date_col = DataFetcher.detect_date_column(df)
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
                        
            return df[field]
        except Exception as e:
            raise RuntimeError(f"Database query failed: {e}")
