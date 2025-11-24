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
        #小數點後兩位
        series = series.round(2)
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

        df = pd.concat(series_dict.values(), axis=1, join=how).ffill() #為了解決資料間頻率不同的問題
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
    def fetch_taiwan_leading_indicator(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣領先指標 : 台灣景氣領先指標"""
        stock_id = 'TWB20'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiwan_leading_indicator returned empty data")
        return df  

    def fetch_pmi_manufacturing_index(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """PMI製造業指數 : PMI製造業指數"""
        stock_id = '70100'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_pmi_manufacturing_index returned empty data")
        return df  

    def fetch_taiwan_export_orders(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_export_orders : 台灣外銷訂單金額"""
        stock_id = 'TWG01'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiwan_export_orders returned empty data")
        return df 
    
    def fetch_taiwan_industrial_production(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_industrial_production : 工業生產指數-非季節調整"""
        stock_id = '18860'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiwan_industrial_production returned empty data")
        return df   


    def fetch_taiwan_trade_balance(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_trade_balance : 貿易收支出入超"""
        stock_id = '18700'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        df = df.div(1000)  # Convert to billions

        if df.empty: 
            raise ValueError("fetch_taiwan_trade_balance returned empty data")
        return df   
    
    def fetch_taiwan_retail_sales(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_retail_sales : 台灣零售銷售金額"""

        stock_id = '44220'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        df = df.div(1000)  # Convert to billions

        if df.empty: 
            raise ValueError("fetch_taiwan_trade_balance returned empty data")
        return df   
    
    def fetch_taiwan_unemployment_rate(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_unemployment_rate : 失業率"""
        stock_id = '19400'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiwan_unemployment_rate returned empty data")
        return df

    def fetch_taiwan_cpi(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_cpi : 消費者物價指數"""
        stock_id = '18100'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_taiwan_cpi returned empty data")
        return df
    
    def fetch_taiwan_m1b_m2(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_m1b_m2 : M1B-M2"""
        
        m1b_id = '12301'
        m2_id = '12501'
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": m1b_id,
                "start": start_str,
                "end": end_str
            }
        
        df_m1b = self.fetch_data_from_db(field, sql, self.engine, params=params)

        #取得M2
        params={
                "field": field,
                "ticker": m2_id,
                "start": start_str,
                "end": end_str
            }
        df_m2 = self.fetch_data_from_db(field, sql, self.engine, params=params)

        #計算M1B-M2
        df = df_m1b.copy()
        df = df_m1b - df_m2
        if df_m1b.empty or df_m2.empty  : 
            raise ValueError("fetch_taiwan_m1b_m2 returned empty data")
        return df

    def fetch_taiex_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_bias : 60日乖離率"""
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
        """taiex_macd : MACD線"""
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
        """taiex_dif"""
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
        """taiex_adx"""
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
        """taiex_pe"""
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
        """tw50_pe"""
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
        """mid100_pe"""
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
        """highdiv_pe"""
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
        """taiex_pb"""
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
        """tw50_pb"""
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
        """mid100_pb"""
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
        """highdiv_pb"""
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
    #海外指標
    def fetch_global_gdp_real_growth_rate(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """global_gdp_real_growth_rate : 全球GDP實質成長率"""
        stock_id = 'IMF40'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_global_gdp_real_growth_rate returned empty data")
        return df 
    
    def fetch_us_leading_indicator(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_leading_indicator : 美國領先指標"""
        stock_id = 'USA55'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("us_leading_indicator returned empty data")
        return df
    
    def fetch_us_pmi_manufacturing_index(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_pmi_manufacturing_index : 美國PMI製造業指數"""
        stock_id = 'USA04'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_us_pmi_manufacturing_index returned empty data")
        return df
    
    def fetch_us_durable_goods_orders(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_durable_goods_orders : 美國耐久財訂單金額"""
        stock_id = 'USA85'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_us_durable_goods_orders returned empty data")
        return df
    
    def fetch_us_retail_sales(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_retail_sales : 美國零售銷售金額"""
        stock_id = 'USA87'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)

        df = df.div(1000)  # Convert to billions
        if df.empty: 
            raise ValueError("fetch_us_retail_sales returned empty data")
        return df
    
    def fetch_us_employment_mom(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_employment_mom : 美國就業月變動人數"""
        stock_id = 'USA24'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_us_employment_mom returned empty data")
        return df
    
    def fetch_us_unemployment_rate(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_unemployment_rate : 美國失業率"""
        stock_id = 'USA20'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("us_unemployment_rate returned empty data")
        return df
    
    def fetch_us_cpi_yoy(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_cpi_yoy : 美國消費者物價指數年增率"""
        stock_id = 'USA39'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_us_cpi_yoy returned empty data")
        return df
    
    def fetch_us_existing_home_sales(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_existing_home_sales : 美國成屋銷售量"""
        stock_id = 'USA33'  
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        
        df = self.fetch_data_from_db(field, sql, self.engine, params=params)
        if df.empty: 
            raise ValueError("fetch_us_existing_home_sales returned empty data")
        return df

    def fetch_us_m1_m2(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_m1_m2 : m1-M2"""
        
        m1_id = 'USA57'
        m2_id = 'USA58'
        field = '數值'

        start_str = pd.to_datetime(start_date).strftime('%Y%m')
        end_str = pd.to_datetime(end_date).strftime('%Y%m')

        sql = f"""
            SELECT CONCAT(年月,'01') as 日期, {field}
            FROM `md_cm_eco_economics`
            WHERE 代號 = :ticker AND 年月 BETWEEN :start AND :end
            ORDER BY 年月 asc
        """
        params={
                "field": field,
                "ticker": m1_id,
                "start": start_str,
                "end": end_str
            }
        
        df_m1 = self.fetch_data_from_db(field, sql, self.engine, params=params)

        #取得M2
        params={
                "field": field,
                "ticker": m2_id,
                "start": start_str,
                "end": end_str
            }
        df_m2 = self.fetch_data_from_db(field, sql, self.engine, params=params)

        #計算m1-M2
        df = df_m1.copy()
        df = df_m1 - df_m2
        if df_m1.empty or df_m2.empty  : 
            raise ValueError("fetch_us_m1_m2 returned empty data")
        return df