#!/usr/bin/env python3
"""
CSV to Excel Report Generator
============================

This script processes measure data from CSV files and JSON profile to generate
an Excel report with historical values, latest values, scores, and summary.
"""

import pandas as pd
import json
import os
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from .config import Config

class CSVToReportGenerator:
    
    def __init__(self, value_file: str, score_file: str, measure_profile_file: str, categories: dict,
                  frequency: str = 'M'):
        """
        Initialize the generator with input files
        """
        self.value_file = value_file
        self.score_file = score_file
        self.measure_profile_file = measure_profile_file
        self.categories = categories
        self.frequency = frequency
        
    def clean_column_name(self, col_name: str) -> str:
        """Clean column names by removing extra spaces and newlines"""
        return col_name.strip().replace('\n', '')

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Load and clean data from input files
        """
        # Load CSV files with big5 encoding
        try:
            value_df = pd.read_csv(self.value_file, encoding='big5')
            score_df = pd.read_csv(self.score_file, encoding='big5')
        except Exception as e:
            # Try utf-8-sig if big5 fails
            print(f"Failed to load with big5, trying utf-8-sig: {e}")
            value_df = pd.read_csv(self.value_file, encoding='utf-8-sig')
            score_df = pd.read_csv(self.score_file, encoding='utf-8-sig')

        # Ensure 'Date' column is present
        if 'Date' not in value_df.columns or 'Date' not in score_df.columns:
            raise ValueError("Both CSV files must contain a 'Date' column.")
        
        #Date column should be in datetime format
        value_df['Date'] = pd.to_datetime(value_df['Date'])
        score_df['Date'] = pd.to_datetime(score_df['Date'])

        # Clean column names
        value_df.columns = [self.clean_column_name(col) for col in value_df.columns]
        score_df.columns = [self.clean_column_name(col) for col in score_df.columns]
        
        # Load JSON measure_profile with utf-8 encoding
        with open(self.measure_profile_file, 'r', encoding='utf-8') as f:
            measure_profile = json.load(f)
            
        return value_df, score_df, measure_profile
    
    def get_measure_category(self, measure_id: str) -> str:
        """Get the category of a measure"""
        for category, measures in self.categories.items():
            if measure_id in measures:
                return category
        return "未分類"
    
    def create_report_sheet(self, 
                            display_period: tuple,
                            value_df: pd.DataFrame, 
                            score_df: pd.DataFrame, 
                            measure_profile: Dict) -> pd.DataFrame:
        """
        Create the main report dataframe with proper column layout
        """
        report_data = []
        # filter value_df and score_df by display_period
        start_date, end_date = pd.to_datetime(display_period[0]), pd.to_datetime(display_period[1])
        value_df = value_df[(pd.to_datetime(value_df['Date']) >= start_date) & (pd.to_datetime(value_df['Date']) <= end_date)]
        score_df = score_df[(pd.to_datetime(score_df['Date']) >= start_date) & (pd.to_datetime(score_df['Date']) <= end_date)]

        # Get date columns for historical values
        date_columns = value_df['Date'].tolist()
        
        # Process each measure
        measure_columns = [col for col in value_df.columns if col != 'Date']
        
        for measure_id in measure_columns:
            if measure_id not in measure_profile:
                continue               
           
            # Get historical values
            historical_values = value_df[measure_id].tolist()            
           
            row = {
                'category': self.get_measure_category(measure_id),
                'measure_name': measure_profile[measure_id]['name'],
                'unit': measure_profile[measure_id].get('unit', ''),
            }

            for date, value in zip(date_columns, historical_values):
                row[datetime.strftime(date, '%Y-%m-%d')] = value

            # Get latest score
            if not score_df.empty and measure_id in score_df.columns:
                 row['score'] = score_df[measure_id].iloc[-1]
            else:
                 row['score'] = 0

            report_data.append(row)
        

        # Convert to DataFrame
        report_df = pd.DataFrame(report_data)
        if report_df.empty:
            return pd.DataFrame()

        # sum of scores by category
        report_df['score_total'] = report_df.groupby('category')['score'].transform('sum')

        # Sort by category (as in categories.keys()) and then by the order in each category's list
        category_order = {cat: i for i, cat in enumerate(self.categories.keys())}
        measure_order = {}
        for cat, measures in self.categories.items():
            for i, measure in enumerate(measures):
                measure_order[measure] = i  
        report_df['category_order'] = report_df['category'].map(category_order).fillna(999)
        report_df['measure_order'] = report_df['measure_name'].map(measure_order).fillna(999)
        report_df = report_df.sort_values(by=['category_order', 'measure_order'])
        report_df = report_df.drop(columns=['category_order', 'measure_order'])

        return report_df


    def adjust_df_frequency(self, df: pd.DataFrame, date_col: str = 'Date', frequency: str = 'M') -> pd.DataFrame:
        """Adjust DataFrame to specified frequency by resampling"""
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).resample(frequency).last().reset_index()
        return df
        
    def generate_report(self, display_period: tuple, output_file: str = "report_output.csv"):
        """
        Generate the complete Html report
        """
        print("Loading data...")
        value_df, score_df, measure_profile = self.load_data()

        #調整資料
        value_df = self.adjust_df_frequency(value_df, frequency=self.frequency)
        score_df = self.adjust_df_frequency(score_df, frequency=self.frequency)

        print("Creating report sheet...")
        # Create the report DataFrame
        report_df = self.create_report_sheet(display_period, value_df, score_df, measure_profile)

        if report_df.empty:
            print("Report DataFrame is empty.")
            return

        rename_dict = {
            'category': '類別',
            'measure_name': '指標名稱',
            'unit': '單位',
            'score': '分數',
            'score_total': '類別總分'
        }
        report_df = report_df.rename(columns=rename_dict)
        report_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Report generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate CSV Report")
    parser.add_argument("--value_file", default="data/measure_value.csv", help="Path to measure_value.csv")
    parser.add_argument("--score_file", default="data/measure_score.csv", help="Path to measure_score.csv")
    parser.add_argument("--profile_file", default="data/measure_profile.json", help="Path to measure_profile.json")
    parser.add_argument("--output_file", default="docs/test_report.csv", help="Output file path")
    parser.add_argument("--start_date", default="2024/12/1", help="Start date (YYYY/MM/DD)")
    parser.add_argument("--end_date", default=datetime.now().strftime('%Y/%m/%d'), help="End date (YYYY/MM/DD)")
    
    args = parser.parse_args()

    # Input
    display_period = (args.start_date, args.end_date)
    
    categories = {
            "總經面指標": [
                "taiwan_leading_indicator", "ISM製造業指數_id", "taiwan_export_orders", 
                "taiwan_industrial_production", "taiwan_trade_balance", "taiwan_retail_sales", 
                "taiwan_unemployment_rate", "taiwan_cpi", "taiwan_m1b_m2"
            ],
            "技術面指標": [
                "taiex_bias", "otc_bias", "taiex_macd", 
                "otc_macd", "taiex_dif", "taiex_adx"
            ],
            "評價面指標": [
                "taiex_pe", "tw50_pe", "mid100_pe", 
                "highdiv_pe", "otc_pe", "taiex_pb", 
                "tw50_pb", "mid100_pb", 
                "highdiv_pb", "otc_pb"
            ]
        }
    
    # Check if files exist
    for file_path in [args.value_file, args.score_file, args.profile_file]:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
    
    # Generate report
    generator = CSVToReportGenerator(args.value_file, args.score_file, args.profile_file, categories)
    generator.generate_report(display_period, output_file=args.output_file)


if __name__ == "__main__":
    main()