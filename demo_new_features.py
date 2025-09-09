#!/usr/bin/env python3
"""
Demonstration script for new header rename and merge cell functionality
This script shows how to use the new parameters in export_to_excel and export_to_html
"""

import os
from csv_to_report import CSVToReportGenerator


def demo_new_features():
    """Demonstrate the new functionality"""
    
    print("=== Demo: Header Rename and Merge Cell Functionality ===\n")
    
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
    
    # Load and process data
    value_df, score_df, profile = generator.load_data()
    value_df = generator.adjust_df_frequency(value_df, frequency='ME')
    score_df = generator.adjust_df_frequency(score_df, frequency='ME')
    
    display_period = ('2024/12/1','2025/7/31')
    report_df = generator.create_report_sheet(display_period, value_df, score_df, profile)
    
    print(f"Data loaded: {report_df.shape} rows and columns")
    print(f"Original columns: {list(report_df.columns[:5])}... (showing first 5)")
    
    # Example 1: Header renaming as requested in the issue
    print("\n1. Example: Header renaming as requested in the issue")
    rename_dict = {
        'category': '類別',
        'measure_name': '指標名稱',
        'unit': '單位',
        'score': '分數',
        'score_total': '類別總分'
    }
    print(f"   Rename dictionary: {rename_dict}")
    
    # Export Excel with renamed headers
    generator.export_to_excel(
        report_df, 
        "demo_renamed.xlsx", 
        rename=rename_dict,
        col_mergecell=['category', 'score_total']
    )
    print("   ✅ Excel exported with renamed headers: demo_renamed.xlsx")
    
    # Export HTML with renamed headers
    generator.export_to_html(
        report_df, 
        "demo_renamed.html", 
        rename=rename_dict,
        col_mergecell=['category', 'score_total']
    )
    print("   ✅ HTML exported with renamed headers: demo_renamed.html")
    
    # Example 2: Custom merge cell configuration
    print("\n2. Example: Custom merge cell configuration")
    col_mergecell = ['category', 'score_total']
    print(f"   Merge cells for columns: {col_mergecell}")
    
    generator.export_to_excel(
        report_df, 
        "demo_custom_merge.xlsx", 
        col_mergecell=col_mergecell
    )
    print("   ✅ Excel with custom merge cells: demo_custom_merge.xlsx")
    
    generator.export_to_html(
        report_df, 
        "demo_custom_merge.html", 
        col_mergecell=col_mergecell
    )
    print("   ✅ HTML with custom merge cells: demo_custom_merge.html")
    
    # Example 3: Only merge category (not score_total)
    print("\n3. Example: Only merge category column")
    col_mergecell_category_only = ['category']
    print(f"   Merge cells only for: {col_mergecell_category_only}")
    
    generator.export_to_excel(
        report_df, 
        "demo_category_only_merge.xlsx", 
        col_mergecell=col_mergecell_category_only
    )
    print("   ✅ Excel with category-only merge: demo_category_only_merge.xlsx")
    
    # Example 4: No merge cells at all
    print("\n4. Example: No merge cells")
    generator.export_to_excel(
        report_df, 
        "demo_no_merge.xlsx", 
        col_mergecell=[]
    )
    print("   ✅ Excel with no merge cells: demo_no_merge.xlsx")
    
    # Example 5: Combined example (both rename and custom merge)
    print("\n5. Example: Combined rename + custom merge")
    custom_rename = {
        'category': 'Category',
        'measure_name': 'Measure Name',
        'score': 'Score'
    }
    custom_merge = ['category']
    
    generator.export_to_excel(
        report_df, 
        "demo_combined.xlsx", 
        rename=custom_rename,
        col_mergecell=custom_merge
    )
    print("   ✅ Excel with custom rename + merge: demo_combined.xlsx")
    
    print("\n✨ Demo completed! Check the generated files to see the new functionality.")
    print("\nUsage Summary:")
    print("export_to_excel(df, filename, rename=dict, col_mergecell=list)")
    print("export_to_html(df, filename, rename=dict, col_mergecell=list)")
    print("\nwhere:")
    print("- rename: dict to rename column headers")
    print("- col_mergecell: list of column names to merge identical consecutive cells")


if __name__ == "__main__":
    demo_new_features()