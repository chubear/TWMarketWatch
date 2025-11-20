from __future__ import annotations

from typing import Union, Any
from pathlib import Path
import pandas as pd
from .base_measure import DateLike
from .measure_value import MeasureValue

class MeasureScore(MeasureValue):
    """
    Responsible for calling the corresponding measure method in this class 
    according to the settings in measure_profile.json, generating a DataFrame or CSV of measure_score.
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
        return super(MeasureValue, self).compute_one(measure_id, start_date, end_date, "func_score", **kwargs)

    def compute_all(
        self,
        start_date: DateLike,
        end_date: DateLike,
        how: str = "outer",
        frequency: str = "D"
    ) -> pd.DataFrame:
        return super(MeasureValue, self).compute_all(start_date, end_date, "func_score", how, frequency)

    def to_csv(
        self,
        start_date: DateLike,
        end_date: DateLike,
        output_path: Union[str, Path] = "measure_score.csv",
        how: str = "outer",
        frequency: str = "D",
        csv_encoding: str = "utf-8-sig",
        date_format: str = "%Y/%m/%d",
    ) -> pd.DataFrame:
        return super(MeasureValue, self).to_csv(start_date, end_date, "func_score", output_path, how, frequency, csv_encoding, date_format)

    # ==============================================
    #   Score Calculation Methods
    # ==============================================
    
    def calc_score_taiex_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """加權指數乖離率_id : 67日乖離率"""
        s = self.fetch_taiex_bias(start_date, end_date)
        # Score 1 if > 0, else 0
        return s.apply(lambda x: 1 if x > 0 else 0)

    def calc_score_otc_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數乖離率_id : 67日乖離率"""
        # Original implementation returned the value directly, not a score.
        # Preserving this behavior.
        return self.fetch_otc_bias(start_date, end_date)

# =========================
#   Example Usage
# =========================
if __name__ == "__main__":
    import os
    ms = MeasureScore(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"))

    # 1) Compute single measure
    # s = ms.compute_one("加權指數乖離率_id", "2025-07-01", "2025-12-31")
    # print(s.head())
    
    # 2) Compute all measures
    # all_df = ms.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all_df)  

    # 3) Compute all and output to CSV
    # ms.to_csv(
    #     start_date="2024-01-01",
    #     end_date="2025-12-31",
    #     output_path="measure_score.csv",
    #     frequency="Q",
    #     date_format="%Y-%m-%d",
    # )
