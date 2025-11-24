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
    # s = mv.compute_one("taiwan_m1b_m2", "2024-07-01", "2025-12-31")
    # print(s.tail(10))
    
    # 2) Compute all measures
    # all_df = mv.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all_df)  

    # 3) Compute all and output to CSV
    mv.to_csv(
        start_date="2024-01-01",
        end_date="2025-12-31",
        output_path="measure_value.csv",
        frequency="M",
        date_format="%Y-%m-%d",
    )
def test_MeasureScore():
    ms = MeasureScore(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"))
   
    # 1) Compute single measure
    # s = ms.compute_one("taiwan_m1b_m2", "2024-07-01", "2025-12-31")
    # print(s.tail(10))
    
    # 2) Compute all measures
    # all_df = ms.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all_df)  

    # 3) Compute all and output to CSV
    ms.to_csv(
        start_date="2024-01-01",
        end_date="2025-12-31",
        output_path="measure_score.csv",
        frequency="M",
        date_format="%Y-%m-%d",
    )
if __name__ == '__main__':
    test_MeasureValue()
    test_MeasureScore()
