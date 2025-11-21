import unittest
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.measure_value import MeasureValue
from core.measure_score import MeasureScore
 
def test_MeasureValue():
    mv = MeasureValue(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"))
   
    # 1) Compute single measure
    # s = mv.compute_one("加權指數乖離率_id", "2025-07-01", "2025-12-31")
    # print(s.head())
    
    # 2) Compute all measures
    # all_df = mv.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all_df)  

    # 3) Compute all and output to CSV
    mv.to_csv(
        start_date="2024-01-01",
        end_date="2025-12-31",
        output_path="measure_value.csv",
        frequency="Q",
        date_format="%Y-%m-%d",
    )

if __name__ == '__main__':
    test_MeasureValue()
