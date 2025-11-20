from __future__ import annotations

import sys, os
from typing import Union, Any
from pathlib import Path
import pandas as pd
import requests
from dbconfig import default_engine
from sqlalchemy import  text
#新增路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config
from base_measure import BaseMeasure, DateLike


class MeasureValue(BaseMeasure):
    """
    Responsible for calling the corresponding measure method in this class 
    according to the settings in measure_profile.json, generating a DataFrame or CSV of measure_value.
    """

    def __init__(self, profile_path: Union[str, Path], encoding: str = "utf-8-sig", engine=None):
        super().__init__(profile_path, encoding)
        self.engine = engine or default_engine()
    # =========================
    #   Public API
    # =========================
    def compute_one(
        self,
        measure_id: str,
        start_date: DateLike,
        end_date: DateLike,
        **kwargs: Any,
    ) -> pd.Series:
        return super().compute_one(measure_id, start_date, end_date, "func_value", **kwargs)

    def compute_all(
        self,
        start_date: DateLike,
        end_date: DateLike,
        how: str = "outer",
        frequency: str = "D"
    ) -> pd.DataFrame:
        return super().compute_all(start_date, end_date, "func_value", how, frequency)

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
        return super().to_csv(start_date, end_date, "func_value", output_path, how, frequency, csv_encoding, date_format)

    # ==============================================
    #   Individual Measure Methods
    # ==============================================
    
    def fetch_taiex_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數乖離率_id : 67日乖離率"""
        """
        Common method to fetch data from the API.
        """
        stock_id = 'TWA00'  # TAIEX
        fields = ['價格_BIAS_67D']

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
        

    def fetch_otc_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數乖離率_id : 67日乖離率"""
        df = self.fetch_data('TWC00', start_date, end_date, '價格_BIAS_67D')
        if df.empty: raise ValueError("fetch_otc_bias returned empty data")
        return df['價格_BIAS_67D'].dropna()

    def fetch_taiex_macd(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數MACD_id : MACD線"""
        df = self.fetch_data('TWA00', start_date, end_date, '價格_MACD_12D_26D_9D')
        if df.empty: raise ValueError("fetch_taiex_macd returned empty data")
        # MACD returns 3 columns: dif, macd, dif-macd. We want the 2nd one (MACD)
        return df['價格_MACD_12D_26D_9D_2'].dropna()

    def fetch_otc_macd(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數MACD_id"""
        df = self.fetch_data('TWC00', start_date, end_date, '價格_MACD_12D_26D_9D')
        if df.empty: raise ValueError("fetch_otc_macd returned empty data")
        return df['價格_MACD_12D_26D_9D_2'].dropna()

    def fetch_taiex_dif(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數DIF_id"""
        df = self.fetch_data('TWA00', start_date, end_date, '價格_MACD_12D_26D_9D')
        if df.empty: raise ValueError("fetch_taiex_dif returned empty data")
        # We want the 1st one (DIF)
        return df['價格_MACD_12D_26D_9D_1'].dropna()
    
    def fetch_taiex_adx(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數ADX_id"""
        df = self.fetch_data('TWA00', start_date, end_date, 'ADX_14D')
        if df.empty: raise ValueError("fetch_taiex_adx returned empty data")
        # We want the 1st one (ADX)
        return df['ADX_14D_1'].dropna()
    
    def fetch_taiex_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數本益比_id"""
        stock_id = 'TWA00'  # TAIEX
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        sql = text(f"""
            SELECT 日期, 本益比
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """)
        
        df = pd.read_sql(
            sql,
            self.engine,
            params={
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        )
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        
        df['日期'] = pd.to_datetime(df['日期'])        
        df = df.set_index('日期')
        return df

    def fetch_otc_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數本益比_id"""

        stock_id = 'TWC00'  # OTC
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        sql = text(f"""
            SELECT 日期, 本益比
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """)
        
        df = pd.read_sql(
            sql,
            self.engine,
            params={
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        )
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        
        df['日期'] = pd.to_datetime(df['日期'])        
        df = df.set_index('日期')
        return df

    def fetch_taiex_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數股價淨值比_id"""
        stock_id = 'TWA00'  # TAIEX
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        sql = text(f"""
            SELECT 日期, 股價淨值比
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """)
        
        df = pd.read_sql(
            sql,
            self.engine,
            params={
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        )
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        
        df['日期'] = pd.to_datetime(df['日期'])        
        df = df.set_index('日期')
        return df

    def fetch_otc_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數股價淨值比_id"""
        stock_id = 'TWC00'  # OTC
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        sql = text(f"""
            SELECT 日期, 股價淨值比
            FROM `md_cm_ta_dailyquotes`
            WHERE 股票代號 = :ticker AND 日期 BETWEEN :start AND :end
            ORDER BY 日期 asc
        """)
        
        df = pd.read_sql(
            sql,
            self.engine,
            params={
                "ticker": stock_id,
                "start": start_str,
                "end": end_str
            }
        )
        if df.empty: 
            raise ValueError("fetch_taiex_pe returned empty data")
        
        df['日期'] = pd.to_datetime(df['日期'])        
        df = df.set_index('日期')
        return df

# =========================
#   Example Usage
# =========================
if __name__ == "__main__":
    import os
    mv = MeasureValue(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"),engine=default_engine())

    # 1) Compute single measure
    s = mv.compute_one("加權指數本益比_id", "2025-07-01", "2025-12-31")
    print(s.head())
    
    # 2) Compute all measures
    # all_df = mv.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all_df)  

    # 3) Compute all and output to CSV
    # mv.to_csv(
    #     start_date="2024-01-01",
    #     end_date="2025-12-31",
    #     output_path="measure_value.csv",
    #     frequency="Q",
    #     date_format="%Y-%m-%d",
    # )
