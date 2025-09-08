#!/usr/bin/env python3
"""
Test script for CSV to Report Generator
======================================

Simple test to verify the report generation functionality
"""

import os
import pandas as pd
from csv_to_report import CSVToReportGenerator


def test_csv_to_report():
    """Test the CSV to Report Generator"""
    
    print("Testing CSV to Report Generator...")
    
    # Check if input files exist
    required_files = ["measure_value.csv", "measure_score.csv", "measure_profile.json"]
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing required file: {file_path}")
            return False
    
    try:
        # Create generator
        generator = CSVToReportGenerator(
            "measure_value.csv", 
            "measure_score.csv", 
            "measure_profile.json"
        )
        
        # Test data loading
        value_df, score_df, profile = generator.load_data()
        print(f"✅ Data loaded successfully:")
        print(f"   - Values: {value_df.shape} rows/cols")
        print(f"   - Scores: {score_df.shape} rows/cols") 
        print(f"   - Profile: {len(profile)} measures")
        
        # Test report generation
        output_file = "test_report_output.xlsx"
        generator.generate_report(output_file)
        
        # Verify output file
        if os.path.exists(output_file):
            print(f"✅ Report generated successfully: {output_file}")
            
            # Check sheets
            df_report = pd.read_excel(output_file, sheet_name="Report")
            df_summary = pd.read_excel(output_file, sheet_name="Summary")
            
            print(f"✅ Report sheet: {df_report.shape} rows/cols")
            print(f"✅ Summary sheet: {df_summary.shape} rows/cols")
            
            # Verify key columns exist
            required_cols = ['指標ID', '指標名稱', '面向分類', 'W', 'X']
            missing_cols = [col for col in required_cols if col not in df_report.columns]
            if missing_cols:
                print(f"❌ Missing columns in report: {missing_cols}")
                return False
            
            print("✅ All required columns present")
            
            # Verify categories
            categories = df_summary['面向'].tolist()
            expected_categories = ['總經面指標', '技術面指標', '評價面指標']
            if set(categories) == set(expected_categories):
                print("✅ All categories present in summary")
            else:
                print(f"❌ Category mismatch. Expected: {expected_categories}, Got: {categories}")
                return False
            
            # Clean up test file
            os.remove(output_file)
            print("✅ Test completed successfully!")
            return True
            
        else:
            print(f"❌ Output file not created: {output_file}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_csv_to_report()
    exit(0 if success else 1)