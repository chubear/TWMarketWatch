#!/usr/bin/env python3
"""
TDCC Stockholder Structure Crawler - Example Usage
==================================================

This script demonstrates how to use the TDCCStockholderStructure class
to fetch stockholder distribution data from Taiwan Depository & Clearing Corporation.
"""

from twfincrawler.tdcc import TDCCStockholderStructure
from datetime import datetime, timedelta
import pandas as pd


def main():
    """示範TDCC股權分散表爬蟲的不同使用方式"""
    
    print("集保中心(TDCC)股權分散表爬蟲使用範例")
    print("=" * 50)
    
    # 1. 基本使用 - 獲取股權分散表資料
    print("\n1. 獲取股權分散表資料")
    crawler = TDCCStockholderStructure()
    
    # 嘗試從真實API獲取資料，失敗時自動切換到模擬資料
    df = crawler.get_stockholder_dataframe()
    
    if not df.empty:
        print(f"獲取到 {len(df)} 筆股權分散資料")
        print("\n前5筆資料:")
        print(df.head().to_string(index=False))
        
        # 儲存資料
        filename = crawler.save_to_csv(df, "stockholder_structure_example.csv")
        print(f"資料已儲存至: {filename}")
    
    # 2. 獲取特定股票的股權分散資料
    print("\n2. 獲取特定股票股權分散資料")
    popular_stocks = ['2330', '2317', '2454']  # 台積電、鴻海、聯發科
    
    for stock_code in popular_stocks:
        print(f"\n--- {stock_code} 股權分散資料 ---")
        stock_df = crawler.get_stock_stockholder_structure(stock_code)
        
        if not stock_df.empty:
            # 顯示該股票的股權分散概況
            print(f"共有 {len(stock_df)} 個持股級距")
            if '股票名稱' in stock_df.columns:
                stock_name = stock_df['股票名稱'].iloc[0]
                print(f"股票名稱: {stock_name}")
            
            # 顯示主要持股級距
            if len(stock_df) >= 3:
                print("前3個級距:")
                for idx, row in stock_df.head(3).iterrows():
                    if '持股級距' in row and '股東人數' in row and '持股比例' in row:
                        print(f"  {row['持股級距']}: {row['股東人數']} 人, 持股比例 {row['持股比例']}")
    
    # 3. 股權分散概況分析
    print("\n3. 股權分散概況分析")
    summary = crawler.analyze_stockholder_summary(df)
    
    print("股權分散表統計:")
    for key, value in summary.items():
        if isinstance(value, list) and len(value) > 3:
            print(f"  {key}: {value[:3]}... (共{len(value)}項)")
        elif isinstance(value, dict) and len(value) > 5:
            items = list(value.items())[:3]
            print(f"  {key}: {items}... (共{len(value)}項)")
        else:
            print(f"  {key}: {value}")
    
    # 4. 使用純模擬資料
    print("\n4. 使用模擬資料模式")
    mock_crawler = TDCCStockholderStructure(use_mock_data=True)
    mock_df = mock_crawler.get_stockholder_dataframe()
    
    if not mock_df.empty:
        print(f"模擬資料筆數: {len(mock_df)}")
        
        # 顯示模擬資料中的股票
        if '股票代碼' in mock_df.columns and '股票名稱' in mock_df.columns:
            stocks_info = mock_df[['股票代碼', '股票名稱']].drop_duplicates()
            print("模擬資料包含的股票:")
            for _, row in stocks_info.iterrows():
                print(f"  {row['股票代碼']}: {row['股票名稱']}")
    
    # 5. 指定日期獲取資料
    print("\n5. 獲取指定日期的股權分散資料")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    date_df = crawler.get_stockholder_dataframe(scaDates=yesterday)
    
    if not date_df.empty:
        print(f"獲取到 {yesterday} 的 {len(date_df)} 筆資料")
    else:
        print(f"未找到 {yesterday} 的資料")
    
    print("\n範例執行完成！")
    print("注意: 實際使用時，建議檢查集保中心API的資料更新頻率和可用日期範圍。")


if __name__ == "__main__":
    main()