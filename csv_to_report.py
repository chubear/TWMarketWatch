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
- report_output.xlsx: Excel file with Report and Summary sheets
"""

import pandas as pd
import json
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from typing import Dict, List, Tuple
import os


class CSVToReportGenerator:
    """Generate Excel report from CSV and JSON files"""
    
    def __init__(self, value_file: str, score_file: str, profile_file: str):
        """
        Initialize the generator with input files
        
        Args:
            value_file: Path to measure_value.csv
            score_file: Path to measure_score.csv  
            profile_file: Path to measure_profile.json
        """
        self.value_file = value_file
        self.score_file = score_file
        self.profile_file = profile_file
        
        # Define measure categories
        self.categories = {
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
        
    def clean_column_name(self, col_name: str) -> str:
        """Clean column names by removing extra spaces and newlines"""
        return col_name.strip().replace('\n', '')
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Load and clean data from input files
        
        Returns:
            Tuple of (value_df, score_df, profile_dict)
        """
        # Load CSV files with big5 encoding
        value_df = pd.read_csv(self.value_file, encoding='big5')
        score_df = pd.read_csv(self.score_file, encoding='big5')
        
        # Clean column names
        value_df.columns = [self.clean_column_name(col) for col in value_df.columns]
        score_df.columns = [self.clean_column_name(col) for col in score_df.columns]
        
        # Load JSON profile with utf-8 encoding
        with open(self.profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            
        return value_df, score_df, profile
    
    def get_measure_category(self, measure_id: str) -> str:
        """Get the category of a measure"""
        for category, measures in self.categories.items():
            if measure_id in measures:
                return category
        return "未分類"
    
    def create_report_sheet(self, value_df: pd.DataFrame, score_df: pd.DataFrame, 
                          profile: Dict) -> pd.DataFrame:
        """
        Create the main report dataframe with proper column layout
        
        Args:
            value_df: DataFrame with historical values
            score_df: DataFrame with scores
            profile: Measure profile dictionary
            
        Returns:
            DataFrame ready for Excel export
        """
        report_data = []
        
        # Get date columns for historical values (J~V would be 13 columns)
        date_columns = value_df['Date'].tolist()
        
        # Process each measure
        measure_columns = [col for col in value_df.columns if col != 'Date']
        
        for measure_id in measure_columns:
            if measure_id not in profile:
                continue
                
            # Get measure name from profile
            measure_name = profile[measure_id]['name']
            
            # Get historical values
            historical_values = value_df[measure_id].tolist()
            
            # Get latest value and score
            latest_value = value_df[measure_id].iloc[-1]
            latest_score = score_df[measure_id].iloc[-1]
            
            # Get category
            category = self.get_measure_category(measure_id)
            
            # Create row data following the specified column layout
            # A-G: Empty columns for flexibility
            # H: 指標名稱 (measure name)
            # I: 面向分類 (category)
            # J~V: 歷史數值 (historical values)
            # W: 最新數值 (latest value)
            # X: 分數 (score)
            
            row = {
                'A': '',
                'B': '',
                'C': '',
                'D': '',
                'E': '',
                'F': '',
                'G': measure_id,  # 指標ID for reference
                'H': measure_name,  # 指標名稱
                'I': category,  # 面向分類
            }
            
            # Add historical values (columns J~V, max 13 columns)
            col_letters = ['J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V']
            for i, (date, value) in enumerate(zip(date_columns, historical_values)):
                if i < len(col_letters):
                    row[col_letters[i]] = value
                    
            # W: Latest value, X: Score
            row['W'] = latest_value
            row['X'] = latest_score
                
            report_data.append(row)
        
        # Convert to DataFrame
        report_df = pd.DataFrame(report_data)
        
        # Sort by category and then by measure name
        category_order = ["總經面指標", "技術面指標", "評價面指標", "未分類"]
        report_df['category_order'] = report_df['I'].map(
            {cat: i for i, cat in enumerate(category_order)}
        )
        report_df = report_df.sort_values(['category_order', 'H'])
        report_df = report_df.drop('category_order', axis=1)
        
        return report_df
    
    def create_summary_sheet(self, report_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create summary sheet with category score totals
        
        Args:
            report_df: Main report dataframe
            
        Returns:
            Summary DataFrame
        """
        summary_data = []
        
        for category in ["總經面指標", "技術面指標", "評價面指標"]:
            category_df = report_df[report_df['I'] == category]
            total_score = category_df['X'].sum()
            
            summary_data.append({
                '面向': category,
                '分數總和': total_score,
                '指標數量': len(category_df)
            })
        
        return pd.DataFrame(summary_data)
    
    def format_excel_sheet(self, ws, df: pd.DataFrame, sheet_name: str):
        """Format Excel sheet with headers and styling"""
        
        # Add proper column headers for Report sheet
        if sheet_name == "Report":
            # Set meaningful headers instead of just letters
            headers = {
                'A': '', 'B': '', 'C': '', 'D': '', 'E': '', 'F': '',
                'G': '指標ID', 'H': '指標名稱', 'I': '面向分類',
                'J': '2024/12/31', 'K': '2025/1/31', 'L': '2025/2/28', 
                'M': '2025/3/31', 'N': '2025/4/30', 'O': '2025/5/31', 
                'P': '2025/6/30', 'W': '最新數值', 'X': '分數'
            }
            
            # Update header row
            for col_letter, header_text in headers.items():
                if header_text:  # Only update non-empty headers
                    for cell in ws[1]:
                        if cell.column_letter == col_letter:
                            cell.value = header_text
                            break
        
        # Set header font and alignment
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # Format headers
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def generate_report(self, output_file: str = "report_output.xlsx"):
        """
        Generate the complete Excel report
        
        Args:
            output_file: Output Excel file path
        """
        print("Loading data...")
        value_df, score_df, profile = self.load_data()
        
        print("Creating report sheet...")
        report_df = self.create_report_sheet(value_df, score_df, profile)
        
        print("Creating summary sheet...")
        summary_df = self.create_summary_sheet(report_df)
        
        print("Writing Excel file...")
        # Create workbook
        wb = Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create Report sheet
        ws_report = wb.create_sheet("Report")
        for row in dataframe_to_rows(report_df, index=False, header=True):
            ws_report.append(row)
        self.format_excel_sheet(ws_report, report_df, "Report")
        
        # Create Summary sheet
        ws_summary = wb.create_sheet("Summary")
        for row in dataframe_to_rows(summary_df, index=False, header=True):
            ws_summary.append(row)
        self.format_excel_sheet(ws_summary, summary_df, "Summary")
        
        # Save workbook
        wb.save(output_file)
        print(f"Report saved to: {output_file}")
        
        # Print summary
        print(f"\n=== Report Summary ===")
        print(f"Total measures processed: {len(report_df)}")
        print(f"Categories: {summary_df['面向'].tolist()}")
        for _, row in summary_df.iterrows():
            print(f"  {row['面向']}: {row['指標數量']} 指標, 總分 {row['分數總和']}")


def main():
    """Main function to run the report generator"""
    
    # Input files
    value_file = "measure_value.csv"
    score_file = "measure_score.csv"
    profile_file = "measure_profile.json"
    
    # Check if files exist
    for file_path in [value_file, score_file, profile_file]:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
    
    # Generate report
    generator = CSVToReportGenerator(value_file, score_file, profile_file)
    generator.generate_report()


if __name__ == "__main__":
    main()