import unittest
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.measure_value import MeasureValue
from core.measure_score import MeasureScore
 
def test_MeasureValue(type: str = "tw"):
    mv = MeasureValue(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data",f"measure_profile_{type}.json"))
   
    # 1) Compute single measure
    s = mv.compute_one("eu_economic_sentiment", "2024-07-01", "2025-12-31")
    print(s.tail(10))
    
    # 2) Compute all measures
    # all_df = mv.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all_df)  

    # 3) Compute all and output to CSV
    # mv.to_csv(
    #     start_date="2024-01-01",
    #     end_date="2025-12-31",
    #     output_path=f"data/measure_value_{type}.csv",
    #     frequency="M",
    #     date_format="%Y-%m-%d",
    # )
def test_MeasureScore(type: str = "tw"):
    ms = MeasureScore(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data",f"measure_profile_{type}.json"))
   
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
        output_path=f"data/measure_score_{type}.csv",
        frequency="M",
        date_format="%Y-%m-%d",
    )

def test_CSVToReportGenerator(type: str = "tw"):
    from core.csv_to_report import CSVToReportGenerator

    generator = CSVToReportGenerator(
        value_file=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data",f"measure_value_{type}.csv"),
        score_file=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data",f"measure_score_{type}.csv"),
        measure_profile_file=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data",f"measure_profile_{type}.json"),
        frequency='M'
    )

    display_period = ("2025-01-01", "2025-12-31")
    output_file = f"data/test_report_output_{type}.csv"
    generator.generate_report(display_period, output_file=output_file)
    webapi_file = f"/home/chubear/QadrisWebAPI/data/{type}_market_watch.csv"
    generator.generate_report(display_period, output_file=webapi_file)
if __name__ == '__main__':
    type ="overseas" 
    # type ="tw"
    test_MeasureValue(type)
    # test_MeasureScore(type)
    # test_CSVToReportGenerator(type)