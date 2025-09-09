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
    
    def __init__(self, value_file: str, score_file: str, measure_profile_file: str, categories: dict,
                 display_period: tuple = None, frequency: str = 'M'):
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
        # 預設顯示區間: 去年底~今日
        import datetime
        today = datetime.date.today()
        last_year_end = datetime.date(today.year - 1, 12, 31)
        if display_period is None:
            self.display_period = (last_year_end.strftime('%Y/%m/%d'), today.strftime('%Y/%m/%d'))
        else:
            self.display_period = display_period
        self.frequency = frequency
        
    def clean_column_name(self, col_name: str) -> str:
        """Clean column names by removing extra spaces and newlines"""
        return col_name.strip().replace('\n', '')

    def load_data(self, frequency: str = "M") -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Load and clean data from input files
        
        Returns:
            Tuple of (value_df, score_df, measure_profile_dict)
        """
        # Load CSV files with big5 encoding
        value_df = pd.read_csv(self.value_file, encoding='big5')
        score_df = pd.read_csv(self.score_file, encoding='big5')

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
                            value_df: pd.DataFrame, 
                            score_df: pd.DataFrame, 
                            measure_profile: Dict) -> pd.DataFrame:
        """
        Create the main report dataframe with proper column layout
        
        Args:
            value_df: DataFrame with historical values
            score_df: DataFrame with scores
            measure_profile: Measure profile dictionary
            
        Returns:
            DataFrame ready for Excel export
        """
        report_data = []
        
        # Get date columns for historical values (J~V would be 13 columns)
        date_columns = value_df['Date'].tolist()
        
        # Process each measure
        measure_columns = [col for col in value_df.columns if col != 'Date']
        
        for measure_id in measure_columns:
            if measure_id not in measure_profile:
                continue
                
            # Get measure name from measure_profile
            measure_name = measure_profile[measure_id]['name']
            
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
        
        # Sort by category (as in categories.keys()) and then by the order in each category's list
        category_order = list(self.categories.keys()) + ["未分類"]
        measure_order_map = {}
        for cat_idx, cat in enumerate(category_order):
            measures = self.categories.get(cat, [])
            for order_idx, measure_id in enumerate(measures):
                measure_order_map[(cat, measure_id)] = order_idx

        def get_measure_order(row):
            cat = row['I']
            mid = row['G']
            if (cat, mid) in measure_order_map:
                return measure_order_map[(cat, mid)]
            return float('inf')

        report_df['category_order'] = report_df['I'].map(
            {cat: i for i, cat in enumerate(category_order)}
        )
        report_df['measure_order'] = report_df.apply(get_measure_order, axis=1)
        report_df = report_df.sort_values(['category_order', 'measure_order'])
        report_df = report_df.drop(['category_order', 'measure_order'], axis=1)
        
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
            # Set static headers
            headers = {
                'A': '', 'B': '', 'C': '', 'D': '', 'E': '', 'F': '',
                'G': '指標ID', 'H': '指標名稱', 'I': '面向分類',
                'W': '最新數值', 'X': '分數'
            }
            # 動態產生J~V等日期欄位
            import pandas as pd
            from datetime import datetime
            import calendar
            start_str, end_str = self.display_period
            freq = self.frequency
            start = pd.to_datetime(start_str)
            end = pd.to_datetime(end_str)
            date_labels = []
            if freq == '月':
                # 產生每月最後一天
                cur = start
                while cur <= end:
                    last_day = cur.replace(day=calendar.monthrange(cur.year, cur.month)[1])
                    if last_day > end:
                        last_day = end
                    date_labels.append(last_day.strftime('%Y/%m/%d'))
                    # 下個月
                    if cur.month == 12:
                        cur = cur.replace(year=cur.year+1, month=1, day=1)
                    else:
                        cur = cur.replace(month=cur.month+1, day=1)
            # 填入J~V
            col_letters = [chr(i) for i in range(ord('J'), ord('J')+len(date_labels))]
            for i, (col, date_label) in enumerate(zip(col_letters, date_labels)):
                headers[col] = date_label
            # Update header row
            for cell in ws[1]:
                col_letter = cell.column_letter
                if col_letter in headers:
                    cell.value = headers[col_letter]
        
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
    def adjust_df_frequency(self, df: pd.DataFrame, date_col: str = 'Date', frequency: str = 'M') -> pd.DataFrame:
        """Adjust DataFrame to specified frequency by resampling"""
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).resample(frequency).last().reset_index()
        return df
        
    def generate_report(self, output_file: str = "report_output.xlsx"):
        """
        Generate the complete Excel report
        
        Args:
            output_file: Output Excel file path
        """
        print("Loading data...")
        value_df, score_df, measure_profile = self.load_data()

        #調整資料
        value_df = self.adjust_df_frequency(value_df, frequency=self.frequency)
        score_df = self.adjust_df_frequency(score_df, frequency=self.frequency)

        print("Creating report sheet...")
        report_df = self.create_report_sheet(value_df, score_df, measure_profile)
        
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
    measure_profile_file = "measure_profile.json"
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
    generator.generate_report()


if __name__ == "__main__":
    main()