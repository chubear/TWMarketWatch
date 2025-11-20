from __future__ import annotations

import json
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Union, Callable, Optional
from datetime import date, datetime
from .config import Config

DateLike = Union[str, date, pd.Timestamp]

class BaseMeasure:
    """
    Base class for MeasureValue and MeasureScore.
    Handles profile loading, API requests, and common computation logic.
    """
    
    def __init__(self, profile_path: Union[str, Path], encoding: str = Config.DEFAULT_ENCODING):
        self.profile_path = Path(profile_path)
        self.encoding = encoding
        self.measure_profile: Dict[str, Dict[str, Any]] = self._load_measure_profile()

    def _load_measure_profile(self) -> Dict[str, Dict[str, Any]]:
        with self.profile_path.open("r", encoding=self.encoding) as f:
            return json.load(f)

    def _get_measure_func(self, measure_id: str, func_key: str) -> Callable[..., pd.Series]:
        """
        Get the method corresponding to the measure_id based on the function key (func_value or func_score).
        """
        cfg = self.measure_profile.get(measure_id)
        if cfg is None:
            raise KeyError(f"measure_id {measure_id} does not exist in measure_profile.json")

        func_name = cfg.get(func_key)
        if not isinstance(func_name, str):
            raise TypeError(f"measure_id {measure_id} '{func_key}' setting must be a string (method name)")

        if not hasattr(self, func_name):
            raise AttributeError(f"{self.__class__.__name__} does not have method '{func_name}' (for {measure_id})")

        return getattr(self, func_name)

    def fetch_data(self, stock_id: str, start_date: DateLike, end_date: DateLike, fields: str) -> pd.DataFrame:
        """
        Common method to fetch data from the API.
        """
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        params = {
            'stock_id': stock_id,
            'start': start_str,
            'end': end_str,
            'fields': fields,
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
            
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                return df
            else:
                # Return empty DataFrame with correct index name if possible, or just empty
                return pd.DataFrame()
                
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            raise
        except Exception as e:
            print(f"Data processing failed: {e}")
            raise

    def compute_one(
        self,
        measure_id: str,
        start_date: DateLike,
        end_date: DateLike,
        func_key: str,
        **kwargs: Any,
    ) -> pd.Series:
        """
        Compute a single measure.
        """
        func = self._get_measure_func(measure_id, func_key)
        series = func(start_date, end_date, **kwargs)

        if not isinstance(series, pd.Series):
            raise TypeError(f"{measure_id} function {func.__name__} did not return pd.Series")

        series.name = measure_id
        return series

    def compute_all(
        self,
        start_date: DateLike,
        end_date: DateLike,
        func_key: str,
        how: str = "outer",
        frequency: str = "D"
    ) -> pd.DataFrame:
        """
        Compute all measures in the profile.
        """
        series_dict: Dict[str, pd.Series] = {}

        for measure_id in self.measure_profile.keys():
            # Check if the measure has the required function key
            if func_key not in self.measure_profile[measure_id]:
                 continue
                 
            print(f"Computing {measure_id} ...")
            try:
                s = self.compute_one(measure_id, start_date, end_date, func_key)
                series_dict[measure_id] = s
            except Exception as e:
                print(f"Error computing {measure_id}: {e}")

        if not series_dict:
            return pd.DataFrame()

        df = pd.concat(series_dict.values(), axis=1, join=how)
        df = df.groupby(df.index.to_period(frequency)).tail(1)
        df.index = df.index.to_period(frequency).to_timestamp(how='end')
        
        return df

    def to_csv(
        self,
        start_date: DateLike,
        end_date: DateLike,
        func_key: str,
        output_path: Union[str, Path],
        how: str = "outer",
        frequency: str = "D",
        csv_encoding: str = Config.DEFAULT_ENCODING,
        date_format: str = Config.DEFAULT_DATE_FORMAT,
    ) -> pd.DataFrame:
        """
        Compute all and save to CSV.
        """
        df = self.compute_all(start_date, end_date, func_key, how=how, frequency=frequency)

        df_out = df.copy()
        if isinstance(df_out.index, pd.DatetimeIndex):
            df_out.insert(0, "Date", df_out.index.strftime(date_format))
        else:
            df_out.insert(0, "Date", df_out.index.astype(str))

        df_out.reset_index(drop=True, inplace=True)

        output_path = Path(output_path)
        df_out.to_csv(output_path, index=False, encoding=csv_encoding)
        print(f"Saved to {output_path}")
        return df_out
