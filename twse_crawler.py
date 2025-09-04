#!/usr/bin/env python3
"""
Taiwan Stock Exchange (TWSE) Daily Closing Price Crawler
=========================================================

This module provides functionality to crawl daily closing prices from the
Taiwan Stock Exchange OpenAPI.

Taiwan Stock Exchange provides several public APIs:
- Daily trading data: https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
- Stock info: https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY?response=json&date={date}&stockNo={stock_code}
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class TWStockCrawler:
    """台灣證券交易所每日收盤價爬蟲"""
    
    def __init__(self):
        self.base_url = "https://www.twse.com.tw"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_daily_stock_data(self, date: str, stock_code: str = None) -> Dict:
        """
        獲取指定日期的股票資料
        
        Args:
            date: 日期格式 YYYYMMDD (例: 20241201)
            stock_code: 股票代碼 (選填，如果不提供則獲取所有股票)
        
        Returns:
            Dict: 股票資料
        """
        if stock_code:
            # 單一股票資料
            url = f"{self.base_url}/exchangeReport/STOCK_DAY"
            params = {
                'response': 'json',
                'date': date,
                'stockNo': stock_code
            }
        else:
            # 全市場股票資料
            url = f"{self.base_url}/exchangeReport/MI_INDEX"
            params = {
                'response': 'json',
                'date': date,
                'type': 'ALL'
            }
            
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"請求失敗: {e}")
            return {}
    
    def get_market_closing_prices(self, date: str = None) -> pd.DataFrame:
        """
        獲取市場收盤價資料
        
        Args:
            date: 日期格式 YYYYMMDD，如果不提供則使用今天
            
        Returns:
            pd.DataFrame: 包含股票代碼、名稱、收盤價等資訊
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在獲取 {date} 的收盤價資料...")
        
        data = self.get_daily_stock_data(date)
        
        if not data:
            print(f"無法獲取 {date} 的資料")
            return pd.DataFrame()
            
        # 解析資料
        if 'data' in data:
            df = pd.DataFrame(data['data'])
            if not df.empty:
                # 重新命名欄位為中文
                column_mapping = {
                    'Code': '股票代碼',
                    'Name': '股票名稱', 
                    'ClosingPrice': '收盤價',
                    'Change': '漲跌',
                    'ChangePercent': '漲跌幅',
                    'OpeningPrice': '開盤價',
                    'HighestPrice': '最高價',
                    'LowestPrice': '最低價',
                    'TradeVolume': '成交量'
                }
                
                # 只重新命名存在的欄位
                available_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
                df = df.rename(columns=available_columns)
                
                print(f"成功獲取 {len(df)} 筆股票資料")
                return df
        
        print(f"資料格式不符預期，原始資料: {data}")
        return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """
        將資料儲存為CSV檔案
        
        Args:
            df: 要儲存的DataFrame
            filename: 檔案名稱，如果不提供則使用日期
            
        Returns:
            str: 儲存的檔案路徑
        """
        if filename is None:
            today = datetime.now().strftime('%Y%m%d')
            filename = f"twse_closing_prices_{today}.csv"
            
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"資料已儲存至: {filename}")
        return filename
    
    def get_historical_data(self, start_date: str, end_date: str, 
                          stock_code: str = None) -> pd.DataFrame:
        """
        獲取歷史資料
        
        Args:
            start_date: 開始日期 YYYYMMDD
            end_date: 結束日期 YYYYMMDD  
            stock_code: 股票代碼 (選填)
            
        Returns:
            pd.DataFrame: 歷史資料
        """
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        all_data = []
        current_date = start
        
        while current_date <= end:
            # 跳過週末
            if current_date.weekday() < 5:  # 0-4 是週一到週五
                date_str = current_date.strftime('%Y%m%d')
                print(f"正在處理日期: {date_str}")
                
                data = self.get_daily_stock_data(date_str, stock_code)
                if data and 'data' in data:
                    for item in data['data']:
                        item['日期'] = date_str
                        all_data.append(item)
                
                # 避免請求過於頻繁
                time.sleep(1)
            
            current_date += timedelta(days=1)
        
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame()


def main():
    """示例用法"""
    crawler = TWStockCrawler()
    
    # 獲取今日收盤價
    print("=== 獲取今日市場收盤價 ===")
    today_data = crawler.get_market_closing_prices()
    
    if not today_data.empty:
        print("\n前10筆資料:")
        print(today_data.head(10))
        
        # 儲存為CSV
        crawler.save_to_csv(today_data)
    else:
        print("今日尚無資料或非交易日")
    
    # 獲取特定股票的資料 (台積電 2330)
    print("\n=== 獲取台積電(2330)資料 ===")
    tsmc_data = crawler.get_daily_stock_data(
        datetime.now().strftime('%Y%m%d'), 
        '2330'
    )
    print(json.dumps(tsmc_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()