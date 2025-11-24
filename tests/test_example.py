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
        output_path="data/measure_value.csv",
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
        output_path="data/measure_score.csv",
        frequency="M",
        date_format="%Y-%m-%d",
    )

def test_CSVToReportGenerator():
    from core.csv_to_report import CSVToReportGenerator

    generator = CSVToReportGenerator(
        value_file=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_value.csv"),
        score_file=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_score.csv"),
        measure_profile_file=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"),
        frequency='M'
    )

    display_period = ("2025-01-01", "2025-12-31")
    output_file = "data/test_report_output.csv"
    generator.generate_report(display_period, output_file=output_file)
    webapi_file = "/home/chubear/QadrisWebAPI/data/tw_market_watch.csv"
    generator.generate_report(display_period, output_file=webapi_file)
if __name__ == '__main__':
    # test_MeasureValue()
    # test_MeasureScore()
    test_CSVToReportGenerator()