#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for displaying Excel data from TWMarketWatch
"""

from flask import Flask, render_template, jsonify
import os
from excel_reader import ExcelDataReader

app = Flask(__name__)

# Configuration
EXCEL_FILE = "01.股市經濟及市場指標2025Q2.xlsx"

# Global variables to cache data
cached_data = None
reader = None

def get_excel_data():
    """Get Excel data, using cache if available"""
    global cached_data, reader
    
    if cached_data is None:
        if not os.path.exists(EXCEL_FILE):
            return None
            
        reader = ExcelDataReader(EXCEL_FILE)
        cached_data = reader.get_all_data()
    
    return cached_data

@app.route('/')
def index():
    """Main page showing both tables"""
    data = get_excel_data()
    
    if data is None:
        return render_template('error.html', 
                             error_message=f"Excel file '{EXCEL_FILE}' not found")
    
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
    
    return render_template('index.html',
                         investment_decision_table=investment_decision_html,
                         investment_analysis_table=investment_analysis_html)

@app.route('/decision')
def decision_only():
    """Page showing only investment decision table"""
    data = get_excel_data()
    
    if data is None:
        return render_template('error.html', 
                             error_message=f"Excel file '{EXCEL_FILE}' not found")
    
    investment_decision_html = ""
    if not data['investment_decision'].empty:
        investment_decision_html = reader.df_to_html_table(
            data['investment_decision'], 
            table_id="investment-decision-table",
            table_class="table table-striped table-bordered table-hover"
        )
    
    return render_template('single_table.html',
                         title="國內股市當年度投資決策建議表",
                         table_html=investment_decision_html)

@app.route('/analysis')
def analysis_only():
    """Page showing only investment analysis table"""
    data = get_excel_data()
    
    if data is None:
        return render_template('error.html', 
                             error_message=f"Excel file '{EXCEL_FILE}' not found")
    
    investment_analysis_html = ""
    if not data['investment_analysis'].empty:
        investment_analysis_html = reader.df_to_html_table(
            data['investment_analysis'],
            table_id="investment-analysis-table", 
            table_class="table table-striped table-bordered table-hover"
        )
    
    return render_template('single_table.html',
                         title="國外股市當年度投資評等分析表",
                         table_html=investment_analysis_html)

@app.route('/api/data')
def api_data():
    """API endpoint to get data as JSON"""
    data = get_excel_data()
    
    if data is None:
        return jsonify({"error": "Excel file not found"}), 404
    
    # Convert DataFrames to dict for JSON serialization
    result = {
        'investment_decision': data['investment_decision'].to_dict('records') if not data['investment_decision'].empty else [],
        'investment_analysis': data['investment_analysis'].to_dict('records') if not data['investment_analysis'].empty else []
    }
    
    return jsonify(result)

@app.route('/refresh')
def refresh_data():
    """Refresh cached data"""
    global cached_data
    cached_data = None
    return "Data refreshed successfully! <a href='/'>Go back to main page</a>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)