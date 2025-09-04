#!/usr/bin/env python3
"""
Taiwan Stock Exchange (TWSE) Daily Closing Price Crawler - Demo Version
======================================================================

This module provides functionality to crawl daily closing prices from the
Taiwan Stock Exchange API. Since the actual API may not be accessible in 
all environments, this demo version includes mock data functionality.
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import random


class TWStockCrawlerDemo:
    """台灣證券交易所每日收盤價爬蟲 - 演示版本"""
    
    def __init__(self, use_mock_data: bool = False):
        self.base_url = "https://www.twse.com.tw"
        self.use_mock_data = use_mock_data
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _get_mock_market_data(self, date: str) -> Dict:
        """生成模擬市場資料用於演示"""
        stocks = [
            {'Code': '2330', 'Name': '台積電', 'base_price': 500},
            {'Code': '2317', 'Name': '鴻海', 'base_price': 100},
            {'Code': '2454', 'Name': '聯發科', 'base_price': 800},
            {'Code': '2881', 'Name': '富邦金', 'base_price': 60},
            {'Code': '0050', 'Name': '元大台灣50', 'base_price': 140},
            {'Code': '2382', 'Name': '廣達', 'base_price': 200},
            {'Code': '2412', 'Name': '中華電', 'base_price': 120},
            {'Code': '2308', 'Name': '台達電', 'base_price': 300},
            {'Code': '2002', 'Name': '中鋼', 'base_price': 25},
            {'Code': '1301', 'Name': '台塑', 'base_price': 80}
        ]
        
        data = []
        for stock in stocks:
            # 模擬價格波動
            change_percent = random.uniform(-5, 5)
            closing_price = stock['base_price'] * (1 + change_percent / 100)
            opening_price = closing_price * random.uniform(0.98, 1.02)
            highest_price = max(opening_price, closing_price) * random.uniform(1.0, 1.02)
            lowest_price = min(opening_price, closing_price) * random.uniform(0.98, 1.0)
            volume = random.randint(1000, 50000) * 1000
            
            data.append({
                'Code': stock['Code'],
                'Name': stock['Name'],
                'ClosingPrice': f"{closing_price:.2f}",
                'Change': f"{closing_price - stock['base_price']:.2f}",
                'ChangePercent': f"{change_percent:.2f}%",
                'OpeningPrice': f"{opening_price:.2f}",
                'HighestPrice': f"{highest_price:.2f}",
                'LowestPrice': f"{lowest_price:.2f}",
                'TradeVolume': f"{volume:,}"
            })
        
        return {
            'stat': 'OK',
            'date': date,
            'title': f'{date[:4]}/{date[4:6]}/{date[6:]} 證券總表',
            'fields': ['證券代號', '證券名稱', '收盤價', '漲跌', '漲跌幅', '開盤價', '最高價', '最低價', '成交量'],
            'data': data
        }
    
    def _get_mock_single_stock_data(self, date: str, stock_code: str) -> Dict:
        """生成模擬單一股票資料"""
        stock_names = {
            '2330': '台積電',
            '2317': '鴻海', 
            '2454': '聯發科',
            '2881': '富邦金'
        }
        
        if stock_code not in stock_names:
            return {'stat': 'ERROR', 'message': '查無此股票代碼'}
        
        base_price = {'2330': 500, '2317': 100, '2454': 800, '2881': 60}.get(stock_code, 100)
        change_percent = random.uniform(-5, 5)
        closing_price = base_price * (1 + change_percent / 100)
        
        return {
            'stat': 'OK',
            'date': date,
            'title': f'{stock_code} {stock_names[stock_code]} 個股日成交資訊',
            'fields': ['日期', '證券代號', '證券名稱', '收盤價', '漲跌', '漲跌幅'],
            'data': [{
                'Date': date,
                'Code': stock_code,
                'Name': stock_names[stock_code],
                'ClosingPrice': f"{closing_price:.2f}",
                'Change': f"{closing_price - base_price:.2f}",
                'ChangePercent': f"{change_percent:.2f}%"
            }]
        }
    
    def get_daily_stock_data(self, date: str, stock_code: str = None) -> Dict:
        """
        獲取指定日期的股票資料
        
        Args:
            date: 日期格式 YYYYMMDD (例: 20241201)
            stock_code: 股票代碼 (選填，如果不提供則獲取所有股票)
        
        Returns:
            Dict: 股票資料
        """
        if self.use_mock_data:
            if stock_code:
                return self._get_mock_single_stock_data(date, stock_code)
            else:
                return self._get_mock_market_data(date)
        
        # 實際API請求邏輯
        if stock_code:
            url = f"{self.base_url}/exchangeReport/STOCK_DAY"
            params = {
                'response': 'json',
                'date': date,
                'stockNo': stock_code
            }
        else:
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
            print(f"API請求失敗: {e}")
            print("正在切換至模擬資料模式...")
            self.use_mock_data = True
            return self.get_daily_stock_data(date, stock_code)
    
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
        if self.use_mock_data:
            print("(使用模擬資料)")
        
        data = self.get_daily_stock_data(date)
        
        if not data or data.get('stat') != 'OK':
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
    
    def analyze_market_summary(self, df: pd.DataFrame) -> Dict:
        """
        分析市場概況
        
        Args:
            df: 股票資料DataFrame
            
        Returns:
            Dict: 市場分析結果
        """
        if df.empty:
            return {}
        
        # 計算市場統計數據
        total_stocks = len(df)
        
        # 嘗試分析漲跌情況
        rising_stocks = 0
        falling_stocks = 0
        unchanged_stocks = 0
        
        if '漲跌' in df.columns:
            for change in df['漲跌']:
                try:
                    change_val = float(str(change).replace('+', ''))
                    if change_val > 0:
                        rising_stocks += 1
                    elif change_val < 0:
                        falling_stocks += 1
                    else:
                        unchanged_stocks += 1
                except:
                    unchanged_stocks += 1
        
        summary = {
            '總股票數': total_stocks,
            '上漲股票數': rising_stocks,
            '下跌股票數': falling_stocks,
            '平盤股票數': unchanged_stocks,
            '上漲比例': f"{(rising_stocks/total_stocks)*100:.1f}%" if total_stocks > 0 else "0%"
        }
        
        return summary


def main():
    """示例用法"""
    # 初始化爬蟲 (自動檢測網路狀況，如無法連線會使用模擬資料)
    crawler = TWStockCrawlerDemo()
    
    # 獲取今日收盤價
    print("=== 台灣證券交易所每日收盤價爬蟲 ===")
    print("正在嘗試連接台灣證券交易所API...")
    
    today_data = crawler.get_market_closing_prices()
    
    if not today_data.empty:
        print("\n=== 市場收盤價資料 ===")
        print(today_data.to_string(index=False))
        
        # 分析市場概況
        summary = crawler.analyze_market_summary(today_data)
        print("\n=== 市場概況分析 ===")
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        # 儲存為CSV
        filename = crawler.save_to_csv(today_data)
        print(f"\n資料已匯出為CSV檔案: {filename}")
    
    # 獲取特定股票的資料 (台積電 2330)
    print("\n=== 獲取台積電(2330)個股資料 ===")
    tsmc_data = crawler.get_daily_stock_data(
        datetime.now().strftime('%Y%m%d'), 
        '2330'
    )
    
    if tsmc_data and tsmc_data.get('stat') == 'OK':
        print("台積電資料:")
        print(json.dumps(tsmc_data, indent=2, ensure_ascii=False))
    else:
        print("無法獲取台積電資料")
    
    print("\n=== 爬蟲執行完成 ===")


if __name__ == "__main__":
    main()