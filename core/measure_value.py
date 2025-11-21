from __future__ import annotations

import sys, os
import json
from typing import Union, Any, Dict, Callable
from pathlib import Path
import pandas as pd
from .dbconfig import default_engine
from .config import Config
from .data_fetcher import DataFetcher, DateLike


class MeasureValue:
    """
    Responsible for calling the corresponding measure method in this class 
    according to the settings in measure_profile.json, generating a DataFrame or CSV of measure_value.
    """

    def __init__(self, profile_path: Union[str, Path], encoding: str = "utf-8-sig", engine=None):
        self.profile_path = Path(profile_path)
        self.encoding = encoding
        self.engine = engine or default_engine()
        self.measure_profile: Dict[str, Dict[str, Any]] = self._load_measure_profile()

    def _load_measure_profile(self) -> Dict[str, Dict[str, Any]]:
        """Load measure profile from JSON file"""
        with self.profile_path.open("r", encoding=self.encoding) as f:
            return json.load(f)

    def _get_measure_func(self, measure_id: str) -> Callable[..., pd.Series]:
        """Get the method corresponding to the measure_id"""
        cfg = self.measure_profile.get(measure_id)
        if cfg is None:
            raise KeyError(f"measure_id {measure_id} does not exist in measure_profile.json")

        func_name = cfg.get("func_value")
        if not isinstance(func_name, str):
            raise TypeError(f"measure_id {measure_id} 'func_value' setting must be a string (method name)")

        if not hasattr(self, func_name):
            raise AttributeError(f"{self.__class__.__name__} does not have method '{func_name}' (for {measure_id})")

        return getattr(self, func_name)

    # =========================
    #   Public API
    # =========================
    def compute_one(
        self,
        measure_id: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """Compute a single measure"""
        func = self._get_measure_func(measure_id)
        series = func(start_date, end_date)

        if not isinstance(series, pd.Series):
            raise TypeError(f"{measure_id} function {func.__name__} did not return pd.Series")

        series.name = measure_id
        return series

    def compute_all(
        self,
        start_date: DateLike,
        end_date: DateLike,
        how: str = "outer",
        frequency: str = "D"
    ) -> pd.DataFrame:
        """Compute all measures in the profile"""
        series_dict: Dict[str, pd.Series] = {}

        for measure_id in self.measure_profile.keys():
            # Check if the measure has func_value
            if "func_value" not in self.measure_profile[measure_id]:
                continue
                 
            print(f"Computing {measure_id} ...")
            try:
                s = self.compute_one(measure_id, start_date, end_date)
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
        output_path: Union[str, Path] = "measure_value.csv",
        how: str = "outer",
        frequency: str = "D",
        csv_encoding: str = "utf-8-sig",
        date_format: str = "%Y/%m/%d",
    ) -> pd.DataFrame:
        """Compute all and save to CSV"""
        df = self.compute_all(
            start_date=start_date,
            end_date=end_date,
            how=how,
            frequency=frequency
        )

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

    # =========================
    #   Helper Methods
    # =========================
    def fetch_data_from_api(
        self,
        stock_id: str,
        field: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.DataFrame:
        """Fetch data from API using DataFetcher utility"""
        return DataFetcher.fetch_from_api(stock_id, field, start_date, end_date)
    
    def fetch_data_from_db(
        self,
        field: str,
        query: str,
        engine,
        params: Dict[str, Any] = None,
    ) -> pd.Series:
        """Fetch data from database using DataFetcher utility"""
        return DataFetcher.fetch_from_db(field, query, engine, params)

    # ==============================================
    #   Individual Measure Methods
    # ==============================================

    def fetch_taiex_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數乖離率_id : 60日乖離率"""
        stock_id = 'TWA00'  # TAIEX
        field = '乖離率60日'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailystatistics`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_bias returned empty data")
        return df   
        

    def fetch_otc_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數乖離率_id : 60日乖離率"""
        stock_id = 'TWC00'  # OTC
        field = '乖離率60日'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailystatistics`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_otc_bias returned empty data")
        return df

    def fetch_taiex_macd(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數MACD_id : MACD線"""
        stock_id = 'TWA00'  # TAIEX
        field = '月MACD'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailystatistics`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_macd returned empty data")
        return df

    def fetch_otc_macd(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數MACD_id"""
        stock_id = 'TWC00'  # OTC
        field = '月MACD'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailystatistics`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_otc_macd returned empty data")
        return df

    def fetch_taiex_dif(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數DIF_id"""
        stock_id = 'TWA00'  # TAIEX
        field = '月DIF'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailystatistics`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_dif returned empty data")
        return df
    
    def fetch_taiex_adx(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數ADX_id"""
        stock_id = 'TWA00'  # TAIEX
        field = '月ADX14'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailystatistics`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_adx returned empty data")
        return df
    
    def fetch_taiex_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數本益比_id"""
        stock_id = 'TWA00'  # TAIEX
        field = '本益比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df
    def fetch_tw50_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣50指數本益比_id"""
        stock_id = 'TWA50'  # TAIEX
        field = '本益比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df
    def fetch_mid100_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣中型100指數本益比_id"""
        stock_id = 'TWA51'  
        field = '本益比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df
    def fetch_highdiv_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣高股息指數本益比_id"""
        stock_id = 'TWA54'  
        field = '本益比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df
    def fetch_otc_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數本益比_id"""

        stock_id = 'TWC00'  # OTC
        field = '本益比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df

    def fetch_taiex_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數股價淨值比_id"""
        stock_id = 'TWA00'  # TAIEX
        field = '股價淨值比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df

    def fetch_tw50_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣50指數股價淨值比_id"""
        stock_id = 'TWA50'  # TAIEX
        field = '股價淨值比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df

    def fetch_mid100_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣中型100指數股價淨值比_id"""
        stock_id = 'TWA51'  # TAIEX
        field = '股價淨值比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df

    def fetch_highdiv_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣高股息指數股價淨值比_id"""
        stock_id = 'TWA54'  # TAIEX
        field = '股價淨值比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df

    def fetch_otc_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數股價淨值比_id"""
        stock_id = 'TWC00'  # OTC
        field = '股價淨值比'

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        sql = f"""
            SELECT 日期, {field}
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        return df


