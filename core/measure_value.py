from __future__ import annotations

from typing import Union, Any
from pathlib import Path
import pandas as pd
#新增路徑

from .base_measure import BaseMeasure, DateLike

class MeasureValue(BaseMeasure):
    """
    Responsible for calling the corresponding measure method in this class 
    according to the settings in measure_profile.json, generating a DataFrame or CSV of measure_value.
    """

    def __init__(self, profile_path: Union[str, Path], encoding: str = "utf-8-sig"):
        super().__init__(profile_path, encoding)

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
        df = self.fetch_data('TWA00', start_date, end_date, '價格_BIAS_67D')
        if df.empty: raise ValueError("fetch_taiex_bias returned empty data")
        return df['價格_BIAS_67D'].dropna()

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

    def fetch_taiex_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數本益比_id"""
        df = self.fetch_data('TWA00', start_date, end_date, '本益比4')
        if df.empty: raise ValueError("fetch_taiex_pe returned empty data")
        return df['本益比4'].dropna()

    def fetch_otc_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數本益比_id"""
        df = self.fetch_data('TWC00', start_date, end_date, '本益比4')
        if df.empty: raise ValueError("fetch_otc_pe returned empty data")
        return df['本益比4'].dropna()

    def fetch_taiex_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數股價淨值比_id"""
        df = self.fetch_data('TWA00', start_date, end_date, '股價淨值比')
        if df.empty: raise ValueError("fetch_taiex_pb returned empty data")
        return df['股價淨值比'].dropna()

    def fetch_otc_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數股價淨值比_id"""
        df = self.fetch_data('TWC00', start_date, end_date, '股價淨值比')
        if df.empty: raise ValueError("fetch_otc_pb returned empty data")
        return df['股價淨值比'].dropna()

# =========================
#   Example Usage
# =========================
if __name__ == "__main__":
    import os
    mv = MeasureValue(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"))

    # 1) Compute single measure
    s = mv.compute_one("加權指數乖離率_id", "2025-07-01", "2025-12-31")
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
