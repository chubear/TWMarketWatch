# CSV to Report Generator Usage Guide

## Overview
The `csv_to_report.py` script generates Excel reports from CSV data files and JSON measure profiles.

## Input Files Required
1. **measure_value.csv** - Historical values for each measure (big5 encoding)
2. **measure_score.csv** - Scores for each measure (big5 encoding)  
3. **measure_profile.json** - Measure metadata with name and unit (utf-8 encoding)

## Output
**report_output.xlsx** with two sheets:
- **Report**: Detailed measure data with historical values, latest values, and scores
- **Summary**: Category totals showing score sums for each measure category

## Usage

### Basic Usage
```bash
python csv_to_report.py
```

### Programmatic Usage
```python
from csv_to_report import CSVToReportGenerator

# Create generator
generator = CSVToReportGenerator(
    "measure_value.csv", 
    "measure_score.csv", 
    "measure_profile.json"
)

# Generate report
generator.generate_report("custom_output.xlsx")
```

## Report Structure

### Report Sheet Layout
- **Column G**: 指標ID (Measure ID)
- **Column H**: 指標名稱 (Measure Name from profile)
- **Column I**: 面向分類 (Category classification)
- **Columns J-P**: 歷史數值 (Historical values from CSV)
- **Column W**: 最新數值 (Latest value)
- **Column X**: 分數 (Latest score)

### Categories
Measures are automatically classified into three categories:
- **總經面指標** (Macro-economic indicators): 9 measures
- **技術面指標** (Technical indicators): 6 measures  
- **評價面指標** (Valuation indicators): 10 measures

### Summary Sheet
Shows total scores for each category with measure counts.

## Testing
Run the test script to verify functionality:
```bash
python test_csv_to_report.py
```

## Requirements
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- json5 >= 0.9.0

The script automatically handles:
- Big5 encoding for CSV files
- UTF-8 encoding for JSON files
- Column name cleaning (removes extra spaces and newlines)
- Proper Excel formatting with headers and styling