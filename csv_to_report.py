#!/usr/bin/env python3
"""
CSV to Excel Report Generator
============================

This script processes measure data from CSV files and JSON profile to generate
an Excel report with historical values, latest values, scores, and summary.

Requirements:
- measure_value.csv: Historical values for each measure
- measure_score.csv: Scores for each measure  
- measure_profile.json: Measure metadata (name, unit)

Output:
- report_output.csv: CSV file with Report and Summary sheets
"""

import pandas as pd
import json
from openpyxl.utils.dataframe import dataframe_to_rows
from typing import Dict, List, Tuple
import os
from datetime import datetime
import html as ihtml
from typing import Dict, List, Optional

class CSVToReportGenerator:
    
    def __init__(self, value_file: str, score_file: str, measure_profile_file: str, categories: dict,
                  frequency: str = 'ME'):
        """
        Initialize the generator with input files
        
        Args:
            value_file: Path to measure_value.csv
            score_file: Path to measure_score.csv  
            measure_profile_file: Path to measure_profile.json
            categories: Dictionary of measure categories
            display_period: Tuple of (start_date, end_date) as 'YYYY/MM/DD' strings, default: 去年底~今日
            frequency: Data frequency, e.g. '月', default: '月'
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
        
        Returns:
            Tuple of (value_df, score_df, measure_profile_dict)
        """
        # Load CSV files with big5 encoding
        value_df = pd.read_csv(self.value_file, encoding='big5')
        score_df = pd.read_csv(self.score_file, encoding='big5')
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
        
        Args:
            display_period: Tuple of (start_date, end_date) as 'YYYY/MM/DD' strings
            value_df: DataFrame with historical values
            score_df: DataFrame with scores
            measure_profile: Measure profile dictionary
            
        Returns:
            DataFrame ready for display
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

            row['score'] = score_df[measure_id].iloc[-1]                
            report_data.append(row)
        

        # Convert to DataFrame
        report_df = pd.DataFrame(report_data)
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
        
        Args:
            display_period: Tuple of (start_date, end_date) as 'YYYY/MM/DD' strings
            output_file: Output html file path
        """
        print("Loading data...")
        value_df, score_df, measure_profile = self.load_data()

        #調整資料
        value_df = self.adjust_df_frequency(value_df, frequency=self.frequency)
        score_df = self.adjust_df_frequency(score_df, frequency=self.frequency)

        print("Creating report sheet...")
        # Create the report DataFrame
        report_df = self.create_report_sheet(display_period, value_df, score_df, measure_profile)

        rename_dict = {
            'category': '類別',
            'measure_name': '指標名稱',
            'unit': '單位',
            'score': '分數',
            'score_total': '類別總分'
        }
        report_df = report_df.rename(columns=rename_dict)
        report_df.to_csv(output_file, index=False, encoding='utf-8-sig')

def main():
    """Main function to run the report generator"""
    
    # Input
    display_period = ('2024/12/1',datetime.now().strftime('%Y/%m/%d'))
    value_file = "data/measure_value.csv"
    score_file = "data/measure_score.csv"
    measure_profile_file = "data/measure_profile.json"
    categories = {
            "總經面指標": [
                "台灣領先指標_id", "ISM製造業指數_id", "台灣外銷訂單_id", 
                "台灣工業生產指數_id", "台灣貿易收支_id", "台灣零售銷售_id", 
                "台灣失業率_id", "台灣CPI_id", "台灣M1B-M2_id"
            ],
            "技術面指標": [
                "加權指數乖離率_id", "OTC指數乖離率_id", "加權指數MACD_id", 
                "OTC指數MACD_id", "加權指數DIF_id", "加權指數ADX_id"
            ],
            "評價面指標": [
                "加權指數本益比_id", "台灣50指數本益比_id", "台灣中型100指數本益比_id", 
                "台灣高股息指數本益比_id", "OTC指數本益比_id", "加權指數股價淨值比_id", 
                "台灣50指數股價淨值比_id", "台灣中型100指數股價淨值比_id", 
                "台灣高股息指數股價淨值比_id", "OTC指數股價淨值比_id"
            ]
        }
    # Check if files exist
    for file_path in [value_file, score_file, measure_profile_file]:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
    
    # Generate report
    generator = CSVToReportGenerator(value_file, score_file, measure_profile_file, categories)
    generator.generate_report(display_period, output_file="docs/test_report.csv")


if __name__ == "__main__":
    main()