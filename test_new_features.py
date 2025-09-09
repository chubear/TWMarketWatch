#!/usr/bin/env python3
"""
Test script for new header rename and merge cell functionality
"""

import os
import pandas as pd
from csv_to_report import CSVToReportGenerator


def test_new_features():
    """Test the new rename and col_mergecell parameters"""
    
    print("Testing new header rename and merge cell functionality...")
    
    # Check if input files exist
    required_files = ["measure_value.csv", "measure_score.csv", "measure_profile.json"]
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing required file: {file_path}")
            return False
    
    try:
        # Define categories
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
        
        # Create generator
        generator = CSVToReportGenerator(
            "measure_value.csv", 
            "measure_score.csv", 
            "measure_profile.json",
            categories
        )
        
        # Load data
        value_df, score_df, profile = generator.load_data()
        value_df = generator.adjust_df_frequency(value_df, frequency='ME')
        score_df = generator.adjust_df_frequency(score_df, frequency='ME')
        
        display_period = ('2024/12/1','2025/7/31')
        report_df = generator.create_report_sheet(display_period, value_df, score_df, profile)
        
        print(f"✅ Test data loaded: {report_df.shape} rows/cols")
        
        # Test 1: Header renaming for Excel
        print("\n=== Test 1: Excel with header renaming ===")
        rename_dict = {
            'category': '類別',
            'measure_name': '指標名稱',
            'unit': '單位',
            'score': '分數',
            'score_total': '類別總分'
        }
        
        excel_file = "test_renamed_headers.xlsx"
        generator.export_to_excel(report_df, excel_file, 
                                rename=rename_dict, 
                                col_mergecell=['category', 'score_total'])
        
        # Verify Excel output
        if os.path.exists(excel_file):
            df_test = pd.read_excel(excel_file)
            print(f"✅ Excel file created: {excel_file}")
            print(f"   Columns: {list(df_test.columns)}")
            
            # Check if renamed columns exist
            expected_renamed_cols = ['類別', '指標名稱', '單位', '分數', '類別總分']
            found_renamed = [col for col in expected_renamed_cols if col in df_test.columns]
            if len(found_renamed) == len(expected_renamed_cols):
                print("✅ All expected renamed columns found")
            else:
                print(f"❌ Some renamed columns missing. Found: {found_renamed}")
        else:
            print(f"❌ Excel file not created: {excel_file}")
            return False
            
        # Test 2: Header renaming for HTML
        print("\n=== Test 2: HTML with header renaming ===")
        html_file = "test_renamed_headers.html"
        generator.export_to_html(report_df, html_file,
                               rename=rename_dict,
                               col_mergecell=['category', 'score_total'])
        
        # Verify HTML output
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            print(f"✅ HTML file created: {html_file}")
            
            # Check if renamed headers are in HTML
            renamed_headers_found = 0
            for orig_col, renamed_col in rename_dict.items():
                if renamed_col in html_content:
                    renamed_headers_found += 1
            
            if renamed_headers_found == len(rename_dict):
                print("✅ All renamed headers found in HTML")
            else:
                print(f"❌ Some renamed headers missing in HTML. Found: {renamed_headers_found}/{len(rename_dict)}")
        else:
            print(f"❌ HTML file not created: {html_file}")
            return False
            
        # Test 3: Custom merge cells
        print("\n=== Test 3: Custom merge cell configuration ===")
        excel_file_custom = "test_custom_merge.xlsx"
        html_file_custom = "test_custom_merge.html"
        
        # Test with only category merge (not score_total)
        generator.export_to_excel(report_df, excel_file_custom, 
                                col_mergecell=['category'])
        generator.export_to_html(report_df, html_file_custom,
                               col_mergecell=['category'])
        
        if os.path.exists(excel_file_custom) and os.path.exists(html_file_custom):
            print("✅ Custom merge cell files created successfully")
        else:
            print("❌ Custom merge cell files not created")
            return False
            
        # Test 4: No merge cells
        print("\n=== Test 4: No merge cells ===")
        excel_file_no_merge = "test_no_merge.xlsx"
        html_file_no_merge = "test_no_merge.html"
        
        generator.export_to_excel(report_df, excel_file_no_merge, 
                                col_mergecell=[])
        generator.export_to_html(report_df, html_file_no_merge,
                               col_mergecell=[])
        
        if os.path.exists(excel_file_no_merge) and os.path.exists(html_file_no_merge):
            print("✅ No merge cell files created successfully")
        else:
            print("❌ No merge cell files not created")
            return False
            
        # Test 5: Backward compatibility (should work like before)
        print("\n=== Test 5: Backward compatibility ===")
        excel_file_compat = "test_backward_compat.xlsx"
        html_file_compat = "test_backward_compat.html"
        
        generator.export_to_excel(report_df, excel_file_compat)
        generator.export_to_html(report_df, html_file_compat)
        
        if os.path.exists(excel_file_compat) and os.path.exists(html_file_compat):
            print("✅ Backward compatibility works")
        else:
            print("❌ Backward compatibility broken")
            return False
            
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_new_features()
    exit(0 if success else 1)