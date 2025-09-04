#!/usr/bin/env python3
"""
Taiwan Stock Exchange Crawler - Example Usage
=============================================

This script demonstrates how to use the TWStockCrawlerDemo class
to fetch daily closing prices from Taiwan Stock Exchange.
"""

from twse_crawler_demo import TWStockCrawlerDemo
from datetime import datetime, timedelta
import pandas as pd


def main():
    """示範不同的使用方式"""
    
    print("台灣證券交易所爬蟲使用範例")
    print("=" * 40)
    
    # 1. 基本使用 - 獲取今日資料
    print("\n1. 獲取今日市場收盤價")
    crawler = TWStockCrawlerDemo()
    today_data = crawler.get_market_closing_prices()
    
    if not today_data.empty:
        print(f"獲取到 {len(today_data)} 筆股票資料")
        print("\n前5筆資料:")
        print(today_data.head().to_string(index=False))
        
        # 儲存資料
        filename = crawler.save_to_csv(today_data, "market_data_example.csv")
    
    # 2. 獲取特定股票資料
    print("\n2. 獲取特定股票資料")
    stocks = ['2330', '2317', '2454']  # 台積電、鴻海、聯發科
    
    for stock_code in stocks:
        stock_data = crawler.get_daily_stock_data(
            datetime.now().strftime('%Y%m%d'), 
            stock_code
        )
        
        if stock_data and stock_data.get('stat') == 'OK':
            data = stock_data['data'][0]
            print(f"{data['Name']} ({data['Code']}): 收盤價 {data['ClosingPrice']}, 漲跌 {data['Change']}")
    
    # 3. 市場分析
    print("\n3. 市場概況分析")
    summary = crawler.analyze_market_summary(today_data)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 4. 使用純模擬資料
    print("\n4. 使用模擬資料模式")
    mock_crawler = TWStockCrawlerDemo(use_mock_data=True)
    mock_data = mock_crawler.get_market_closing_prices()
    print(f"模擬資料筆數: {len(mock_data)}")
    
    print("\n範例執行完成！")


if __name__ == "__main__":
    main()