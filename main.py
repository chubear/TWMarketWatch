
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.measure_value import MeasureValue
from core.measure_score import MeasureScore
from core.csv_to_report import CSVToReportGenerator

def main_tw(start_date: str, end_date: str, data_dir: str = "data"):
    #資料起始日為前一年同月1日
    start_date_data = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=365)).replace(day=1).strftime('%Y-%m-%d')

    mv = MeasureValue(os.path.join( data_dir, "measure_profile_tw.json"))
    mv.to_csv(
        start_date=start_date_data,
        end_date=end_date,
        output_path=os.path.join(data_dir, "measure_value_tw.csv"),
        frequency="M",
        date_format="%Y-%m-%d",
    )

    ms = MeasureScore(os.path.join(data_dir, "measure_profile_tw.json"))
    ms.to_csv(
        start_date=start_date_data,
        end_date=end_date,
        output_path=os.path.join(data_dir, "measure_score_tw.csv"),
        frequency="M",
        date_format="%Y-%m-%d",
    )

    generator = CSVToReportGenerator(
        value_file=os.path.join(data_dir, "measure_value_tw.csv"),
        score_file=os.path.join(data_dir, "measure_score_tw.csv"),
        measure_profile_file=os.path.join(data_dir, "measure_profile_tw.json"),
        frequency='M'
    )

    display_period = (start_date, end_date)
    output_file = os.path.join(data_dir, "test_report_output_tw.csv")
    generator.generate_report(display_period, output_file=output_file)

    webapi_file = "/home/chubear/QadrisWebAPI/data/tw_market_watch.csv"
    generator.generate_report(display_period, output_file=webapi_file)

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    #display_end = end_of_month
    display_end = (datetime.today().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    display_start = (display_end - timedelta(days=361)).replace(day=1)

    main_tw(display_start.strftime('%Y-%m-%d'), display_end.strftime('%Y-%m-%d'), data_dir=data_dir)