#!/usr/bin/env python3
"""
TDCC (Taiwan Depository & Clearing Corporation) Stockholder Structure Crawler
=============================================================================

This module provides functionality to crawl stockholder structure data from
the Taiwan Depository & Clearing Corporation OpenAPI.

TDCC provides public APIs for stockholder distribution data:
- Stockholder Structure: https://openapi.tdcc.com.tw/v1/opendata/1-5
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import random


class TDCCStockholderStructure:
    """集保中心股權分散表爬蟲"""
    
    def __init__(self, use_mock_data: bool = False):
        """
        初始化TDCC爬蟲
        
        Args:
            use_mock_data: 是否使用模擬資料，預設為False
        """
        self.base_url = "https://openapi.tdcc.com.tw/v1/opendata/1-5"
        self.use_mock_data = use_mock_data
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _get_mock_stockholder_data(self, scaDates: str = None) -> Dict:
        """
        生成模擬集保戶股權分散表資料用於演示
        
        Args:
            scaDates: 資料日期，格式 YYYYMMDD
            
        Returns:
            Dict: 模擬的股權分散表資料
        """
        if scaDates is None:
            scaDates = datetime.now().strftime('%Y%m%d')
            
        # 模擬知名股票的股權分散數據
        stocks = [
            {'stock_code': '2330', 'stock_name': '台積電'},
            {'stock_code': '2317', 'stock_name': '鴻海'},
            {'stock_code': '2454', 'stock_name': '聯發科'},
            {'stock_code': '2881', 'stock_name': '富邦金'},
            {'stock_code': '0050', 'stock_name': '元大台灣50'},
            {'stock_code': '2382', 'stock_name': '廣達'},
            {'stock_code': '2412', 'stock_name': '中華電'},
            {'stock_code': '2308', 'stock_name': '台達電'},
            {'stock_code': '2002', 'stock_name': '中鋼'},
            {'stock_code': '1301', 'stock_name': '台塑'}
        ]
        
        mock_data = []
        
        for stock in stocks:
            # 模擬不同持股級距的股東人數和持股數
            holding_levels = [
                {'level': '1-999', 'min_shares': 1, 'max_shares': 999},
                {'level': '1,000-5,000', 'min_shares': 1000, 'max_shares': 5000},
                {'level': '5,001-10,000', 'min_shares': 5001, 'max_shares': 10000},
                {'level': '10,001-15,000', 'min_shares': 10001, 'max_shares': 15000},
                {'level': '15,001-20,000', 'min_shares': 15001, 'max_shares': 20000},
                {'level': '20,001-30,000', 'min_shares': 20001, 'max_shares': 30000},
                {'level': '30,001-50,000', 'min_shares': 30001, 'max_shares': 50000},
                {'level': '50,001-100,000', 'min_shares': 50001, 'max_shares': 100000},
                {'level': '100,001-200,000', 'min_shares': 100001, 'max_shares': 200000},
                {'level': '200,001-400,000', 'min_shares': 200001, 'max_shares': 400000},
                {'level': '400,001-600,000', 'min_shares': 400001, 'max_shares': 600000},
                {'level': '600,001-800,000', 'min_shares': 600001, 'max_shares': 800000},
                {'level': '800,001-1,000,000', 'min_shares': 800001, 'max_shares': 1000000},
                {'level': '1,000,001以上', 'min_shares': 1000001, 'max_shares': 50000000}
            ]
            
            for level in holding_levels:
                # 根據持股級距模擬股東人數（持股越多人數越少）
                if level['max_shares'] <= 1000:
                    people_count = random.randint(50000, 100000)
                elif level['max_shares'] <= 50000:
                    people_count = random.randint(10000, 50000)
                elif level['max_shares'] <= 200000:
                    people_count = random.randint(1000, 10000)
                elif level['max_shares'] <= 1000000:
                    people_count = random.randint(100, 1000)
                else:
                    people_count = random.randint(10, 100)
                
                # 計算該級距總持股數
                avg_shares = (level['min_shares'] + level['max_shares']) // 2
                total_shares = people_count * avg_shares + random.randint(-people_count*1000, people_count*1000)
                
                # 計算持股比例
                total_outstanding = 26000000000  # 假設總股數約260億股（參考台積電）
                percentage = (total_shares / total_outstanding) * 100
                
                mock_data.append({
                    'scaDates': scaDates,
                    'scaCode': stock['stock_code'],
                    'scaName': stock['stock_name'],
                    'level': level['level'],
                    'people': f"{people_count:,}",
                    'shares': f"{total_shares:,}",
                    'percentage': f"{percentage:.2f}%"
                })
        
        return {
            'data': mock_data,
            'stat': 'OK',
            'message': '模擬資料，僅供演示使用'
        }
    
    def get_stockholder_structure(self, scaDates: str = None, scaCode: str = None) -> Dict:
        """
        獲取集保戶股權分散表資料
        
        Args:
            scaDates: 資料日期，格式 YYYYMMDD (選填)
            scaCode: 股票代碼 (選填)
        
        Returns:
            Dict: 股權分散表資料
        """
        if self.use_mock_data:
            print("使用模擬資料模式...")
            return self._get_mock_stockholder_data(scaDates)
        
        try:
            params = {}
            if scaDates:
                params['scaDates'] = scaDates
            if scaCode:
                params['scaCode'] = scaCode
            
            print(f"正在從集保中心API獲取股權分散表資料...")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"成功獲取資料")
            return data
            
        except requests.RequestException as e:
            print(f"API請求失敗: {e}")
            print("正在切換至模擬資料模式...")
            return self._get_mock_stockholder_data(scaDates)
        except json.JSONDecodeError as e:
            print(f"JSON解析失敗: {e}")
            print("正在切換至模擬資料模式...")
            return self._get_mock_stockholder_data(scaDates)
        except Exception as e:
            print(f"未知錯誤: {e}")
            print("正在切換至模擬資料模式...")
            return self._get_mock_stockholder_data(scaDates)
    
    def get_stockholder_dataframe(self, scaDates: str = None, scaCode: str = None) -> pd.DataFrame:
        """
        獲取股權分散表資料並轉換為DataFrame
        
        Args:
            scaDates: 資料日期，格式 YYYYMMDD (選填)
            scaCode: 股票代碼 (選填)
            
        Returns:
            pd.DataFrame: 股權分散表DataFrame
        """
        data = self.get_stockholder_structure(scaDates, scaCode)
        
        if data and 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            
            # 重新排列欄位順序和中文化
            column_mapping = {
                'scaDates': '資料日期',
                'scaCode': '股票代碼',
                'scaName': '股票名稱',
                'level': '持股級距',
                'people': '股東人數',
                'shares': '持股股數',
                'percentage': '持股比例'
            }
            
            # 只重新命名存在的欄位
            available_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=available_columns)
            
            print(f"成功轉換 {len(df)} 筆股權分散資料")
            return df
        else:
            print("無法獲取有效的股權分散資料")
            return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """
        將股權分散表資料儲存為CSV檔案
        
        Args:
            df: 要儲存的DataFrame
            filename: 檔案名稱，如果不提供則使用日期
            
        Returns:
            str: 儲存的檔案路徑
        """
        if filename is None:
            today = datetime.now().strftime('%Y%m%d')
            filename = f"tdcc_stockholder_structure_{today}.csv"
            
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"股權分散表資料已儲存至: {filename}")
        return filename
    
    def analyze_stockholder_summary(self, df: pd.DataFrame) -> Dict:
        """
        分析股權分散表概況
        
        Args:
            df: 股權分散表DataFrame
            
        Returns:
            Dict: 分析結果
        """
        if df.empty:
            return {"錯誤": "無資料可分析"}
        
        summary = {}
        
        try:
            # 基本統計
            summary["總記錄數"] = len(df)
            
            if '股票代碼' in df.columns:
                summary["涵蓋股票數"] = df['股票代碼'].nunique()
                summary["股票清單"] = df['股票代碼'].unique().tolist()
            
            if '資料日期' in df.columns:
                dates = df['資料日期'].unique()
                summary["資料日期"] = dates.tolist()
            
            # 持股級距分析
            if '持股級距' in df.columns:
                level_counts = df['持股級距'].value_counts()
                summary["各級距記錄數"] = level_counts.to_dict()
            
        except Exception as e:
            summary["分析錯誤"] = str(e)
        
        return summary
    
    def get_stock_stockholder_structure(self, stock_code: str, scaDates: str = None) -> pd.DataFrame:
        """
        獲取特定股票的股權分散資料
        
        Args:
            stock_code: 股票代碼
            scaDates: 資料日期，格式 YYYYMMDD (選填)
            
        Returns:
            pd.DataFrame: 該股票的股權分散資料
        """
        print(f"正在獲取股票 {stock_code} 的股權分散資料...")
        
        df = self.get_stockholder_dataframe(scaDates, stock_code)
        
        if not df.empty and '股票代碼' in df.columns:
            # 篩選特定股票
            stock_df = df[df['股票代碼'] == stock_code].copy()
            
            if not stock_df.empty:
                print(f"成功獲取股票 {stock_code} 的 {len(stock_df)} 筆股權分散資料")
                return stock_df
            else:
                print(f"未找到股票 {stock_code} 的資料")
                return pd.DataFrame()
        else:
            print(f"無法獲取股票 {stock_code} 的資料")
            return pd.DataFrame()


def main():
    """示例用法"""
    print("=== TDCC集保中心股權分散表爬蟲 ===")
    
    # 建立爬蟲實例（使用模擬資料模式）
    crawler = TDCCStockholderStructure(use_mock_data=True)
    
    # 1. 獲取所有股權分散資料
    print("\n1. 獲取股權分散表資料")
    df = crawler.get_stockholder_dataframe()
    
    if not df.empty:
        print(f"成功獲取 {len(df)} 筆股權分散資料")
        print("\n前10筆資料:")
        print(df.head(10).to_string(index=False))
        
        # 儲存為CSV
        filename = crawler.save_to_csv(df)
        
        # 2. 分析股權分散概況
        print("\n2. 股權分散概況分析")
        summary = crawler.analyze_stockholder_summary(df)
        for key, value in summary.items():
            if isinstance(value, list) and len(value) > 5:
                print(f"  {key}: {value[:5]}... (顯示前5項)")
            else:
                print(f"  {key}: {value}")
    
    # 3. 獲取特定股票的股權分散資料
    print("\n3. 獲取台積電(2330)股權分散資料")
    tsmc_df = crawler.get_stock_stockholder_structure('2330')
    
    if not tsmc_df.empty:
        print("台積電股權分散資料:")
        print(tsmc_df.to_string(index=False))
    
    print("\n=== 股權分散表爬蟲示例完成 ===")


if __name__ == "__main__":
    main()