#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Static site generator for TWMarketWatch
Converts Flask templates to static HTML files for GitHub Pages deployment
"""

import os
import json
import pandas as pd
from excel_reader import ExcelDataReader


def create_base_html_template():
    """Create the base HTML template for static files"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.html">
                <strong>台股觀測指標 TWMarketWatch</strong>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="index.html">完整報表</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="decision.html">投資決策建議</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="analysis.html">投資評等分析</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="data.json" target="_blank">API數據</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="container-fluid mt-4">
        {content}
    </main>

    <footer class="bg-light text-center text-muted py-3 mt-5">
        <div class="container">
            <p>&copy; 2025 TWMarketWatch - 台股觀測指標系統</p>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
    // Add some interactivity
    document.addEventListener('DOMContentLoaded', function() {{
        // Add click-to-highlight functionality for table cells
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {{
            table.addEventListener('click', function(e) {{
                if (e.target.tagName === 'TD' || e.target.tagName === 'TH') {{
                    // Remove previous highlights
                    table.querySelectorAll('.cell-highlight').forEach(cell => {{
                        cell.classList.remove('cell-highlight');
                    }});
                    // Add highlight to clicked cell
                    e.target.classList.add('cell-highlight');
                }}
            }});
        }});
    }});
    </script>
</body>
</html>'''


def create_index_content(investment_decision_html, investment_analysis_html):
    """Create content for index.html"""
    return '''<div class="row">
    <div class="col-12">
        <h1 class="text-center mb-4">股市經濟及市場指標 - 2025Q2</h1>
    </div>
</div>

<!-- Investment Decision Table -->
<div class="row mb-5">
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h3 class="card-title mb-0">
                    <i class="fas fa-chart-line"></i> 國內股市當年度投資決策建議表
                </h3>
                <small class="text-light">範圍: A1:X61</small>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    {investment_decision_table}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Investment Analysis Table -->
<div class="row mb-5">
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h3 class="card-title mb-0">
                    <i class="fas fa-analytics"></i> 國外股市當年度投資評等分析表
                </h3>
                <small class="text-light">範圍: A1:X55</small>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    {investment_analysis_table}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Quick Navigation -->
<div class="row">
    <div class="col-12 text-center">
        <div class="btn-group" role="group">
            <a href="decision.html" class="btn btn-outline-primary">
                僅查看投資決策建議
            </a>
            <a href="analysis.html" class="btn btn-outline-success">
                僅查看投資評等分析
            </a>
        </div>
    </div>
</div>'''.format(
        investment_decision_table=investment_decision_html or '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> 投資決策建議表數據無法載入</div>',
        investment_analysis_table=investment_analysis_html or '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> 投資評等分析表數據無法載入</div>'
    )


def create_single_table_content(title, table_html, is_decision=True):
    """Create content for single table pages"""
    bg_class = "bg-primary" if is_decision else "bg-success"
    icon_class = "fas fa-chart-line" if is_decision else "fas fa-analytics"
    
    return '''<div class="row">
    <div class="col-12">
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                <li class="breadcrumb-item"><a href="index.html">首頁</a></li>
                <li class="breadcrumb-item active">{title}</li>
            </ol>
        </nav>
        
        <h1 class="text-center mb-4">{title}</h1>
        
        <div class="text-center mb-3">
            <a href="index.html" class="btn btn-outline-secondary btn-sm">
                <i class="fas fa-arrow-left"></i> 返回完整報表
            </a>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header {bg_class} text-white">
                <h3 class="card-title mb-0">
                    <i class="{icon_class}"></i>
                    {title}
                </h3>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    {table_content}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Quick Actions -->
<div class="row mt-4">
    <div class="col-12 text-center">
        <div class="btn-group" role="group">
            <a href="decision.html" class="btn btn-outline-primary {decision_active}">
                投資決策建議
            </a>
            <a href="analysis.html" class="btn btn-outline-success {analysis_active}">
                投資評等分析
            </a>
        </div>
    </div>
</div>'''.format(
        title=title,
        bg_class=bg_class,
        icon_class=icon_class,
        table_content=table_html or '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> 數據無法載入</div>',
        decision_active="active" if is_decision else "",
        analysis_active="active" if not is_decision else ""
    )


def generate_static_site():
    """Generate static HTML files from Excel data"""
    
    # Configuration
    EXCEL_FILE = "01.股市經濟及市場指標2025Q2.xlsx"
    
    print("正在讀取Excel數據...")
    
    # Check if Excel file exists
    if not os.path.exists(EXCEL_FILE):
        print(f"錯誤: Excel文件 '{EXCEL_FILE}' 不存在")
        return False
    
    # Read Excel data
    try:
        reader = ExcelDataReader(EXCEL_FILE)
        data = reader.get_all_data()
        
        # Convert DataFrames to HTML
        investment_decision_html = ""
        investment_analysis_html = ""
        
        if not data['investment_decision'].empty:
            investment_decision_html = reader.df_to_html_table(
                data['investment_decision'], 
                table_id="investment-decision-table",
                table_class="table table-striped table-bordered table-hover"
            )
        
        if not data['investment_analysis'].empty:
            investment_analysis_html = reader.df_to_html_table(
                data['investment_analysis'],
                table_id="investment-analysis-table", 
                table_class="table table-striped table-bordered table-hover"
            )
        
        # Create base template
        base_template = create_base_html_template()
        
        print("正在生成HTML文件...")
        
        # Generate index.html
        index_content = create_index_content(investment_decision_html, investment_analysis_html)
        index_html = base_template.format(
            title="完整報表 - 台股觀測指標",
            content=index_content
        )
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("✓ 已生成 index.html")
        
        # Generate decision.html
        decision_content = create_single_table_content(
            "國內股市當年度投資決策建議表", 
            investment_decision_html, 
            is_decision=True
        )
        decision_html = base_template.format(
            title="國內股市當年度投資決策建議表 - 台股觀測指標",
            content=decision_content
        )
        
        with open('decision.html', 'w', encoding='utf-8') as f:
            f.write(decision_html)
        print("✓ 已生成 decision.html")
        
        # Generate analysis.html
        analysis_content = create_single_table_content(
            "國外股市當年度投資評等分析表", 
            investment_analysis_html, 
            is_decision=False
        )
        analysis_html = base_template.format(
            title="國外股市當年度投資評等分析表 - 台股觀測指標",
            content=analysis_content
        )
        
        with open('analysis.html', 'w', encoding='utf-8') as f:
            f.write(analysis_html)
        print("✓ 已生成 analysis.html")
        
        # Generate data.json - convert datetime objects to strings
        def convert_to_json_serializable(df):
            """Convert DataFrame to JSON serializable format"""
            if df.empty:
                return []
            
            # Convert to records and handle datetime objects
            records = df.to_dict('records')
            for record in records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif hasattr(value, 'isoformat'):  # datetime objects
                        record[key] = value.isoformat()
                    elif isinstance(value, (pd.Timestamp, pd.NaT.__class__)):
                        record[key] = str(value) if not pd.isna(value) else None
            return records
        
        json_data = {
            'investment_decision': convert_to_json_serializable(data['investment_decision']),
            'investment_analysis': convert_to_json_serializable(data['investment_analysis'])
        }
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
        print("✓ 已生成 data.json")
        
        print("\n🎉 靜態網站生成完成!")
        print("現在可以將這些文件部署到GitHub Pages:")
        print("- index.html (主頁)")
        print("- decision.html (投資決策建議)")
        print("- analysis.html (投資評等分析)")
        print("- data.json (API數據)")
        print("- static/style.css (樣式文件)")
        
        return True
        
    except Exception as e:
        print(f"錯誤: 生成靜態網站時發生錯誤: {e}")
        return False


if __name__ == "__main__":
    generate_static_site()