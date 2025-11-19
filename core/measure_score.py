# measure_value.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Union, Callable
from datetime import date

import pandas as pd
import requests
from datetime import datetime
from measure_value import MeasureValue

DateLike = Union[str, date, pd.Timestamp]


class MeasureScore:
    """
    負責依照 measure_profile.json 中的設定，
    呼叫本 class 內對應的 measure method，產生 measure_score 的 DataFrame 或 CSV。
    """

    def __init__(self, profile_path: Union[str, Path], encoding: str = "utf-8-sig"):
        self.profile_path = Path(profile_path)
        self.encoding = encoding
        self.measure_profile: Dict[str, Dict[str, Any]] = self._load_measure_profile()
        self.mv = MeasureValue(profile_path)

        # 你也可以在這裡建立 DB 連線、session 等共用資源
        # self.engine = create_engine(...)

    # =========================
    #   讀取 / 解析 profile
    # =========================
    def _load_measure_profile(self) -> Dict[str, Dict[str, Any]]:
        with self.profile_path.open("r", encoding=self.encoding) as f:
            profile = json.load(f)

        # 簡單檢查 func 是否存在於本 class（選用）
        # for measure_id, cfg in profile.items():
        #     func_name = cfg.get("func")
        #     if func_name is None:
        #         raise ValueError(f"{measure_id} 在 measure_profile 中沒有 func 設定")
        return profile

    def _get_measure_func(self, measure_id: str) -> Callable[..., pd.Series]:
        """
        依照 measure_id，從 profile 中取得 func 名稱，再從本 class 找到對應的 method。
        """
        cfg = self.measure_profile.get(measure_id)
        if cfg is None:
            raise KeyError(f"measure_id {measure_id} 不存在於 measure_profile.json")

        func_name = cfg.get("func_score")
        if not isinstance(func_name, str):
            raise TypeError(f"measure_id {measure_id} 的 func 設定必須是字串 (method 名稱)")

        if not hasattr(self, func_name):
            raise AttributeError(f"MeasureScore class 中找不到名為 {func_name} 的 method（對應 {measure_id}）")

        func = getattr(self, func_name)
        return func

    # =========================
    #   對外 API
    # =========================
    def compute_one(
        self,
        measure_id: str,
        start_date: DateLike,
        end_date: DateLike,
        **kwargs: Any,
    ) -> pd.Series:
        """
        計算單一 measure：
        - 依 measure_id 找到對應的 method
        - 呼叫該 method(start_date, end_date, **kwargs)
        - 回傳一個 index 為日期的 Series
        """
        func = self._get_measure_func(measure_id)
        series = func(start_date, end_date, **kwargs)

        if not isinstance(series, pd.Series):
            raise TypeError(f"{measure_id} 對應的函數 {func.__name__} 沒有回傳 pd.Series")

        series.name = measure_id
        return series

    def compute_all(
        self,
        start_date: DateLike,
        end_date: DateLike,
        how: str = "outer",            # 'outer' 或 'inner'：日期對齊方式
        frequency: str = "D" # 重新取樣頻率，例如 'D'、'W'、'M'
    ) -> pd.DataFrame:
        """
        計算 profile 中所有 measure，組成一個 DataFrame。
        """
        series_dict: Dict[str, pd.Series] = {}

        for measure_id in self.measure_profile.keys():
            print(f"計算 {measure_id} ...")
            s = self.compute_one(measure_id, start_date, end_date)
            series_dict[measure_id] = s

        # 整併成 DataFrame
        df = pd.concat(series_dict.values(), axis=1, join=how)
        # 依 frequency 重取樣
        df = df.groupby(df.index.to_period(frequency)).tail(1)
        # 將日期index變成月底
        df.index = df.index.to_period(frequency).to_timestamp(how='end')
        
        return df

    def to_csv(
        self,
        start_date: DateLike,
        end_date: DateLike,
        output_path: Union[str, Path] = "measure_value.csv",
        how: str = "outer",
        frequency: str = "D",# 重新取樣頻率，例如 'D'、'W'、'M'
        csv_encoding: str = "utf-8-sig",
        date_format: str = "%Y/%m/%d",
    ) -> pd.DataFrame:
        """
        直接計算全部 measure 並輸出 CSV，回傳 DataFrame。
        """
        df = self.compute_all(start_date, end_date, how=how, frequency=frequency)

        # 把 index 變成 Date 欄位
        df_out = df.copy()
        if isinstance(df_out.index, pd.DatetimeIndex):
            df_out.insert(0, "Date", df_out.index.strftime(date_format))
        else:
            df_out.insert(0, "Date", df_out.index.astype(str))

        df_out.reset_index(drop=True, inplace=True)

        output_path = Path(output_path)
        df_out.to_csv(output_path, index=False, encoding=csv_encoding)
        print(f"已輸出 {output_path}")
        return df_out

    # ==============================================
    #   以下是「每個 measure 各自獨立的 method」
    # ==============================================
    
    def calc_score_taiex_bias(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        加權指數乖離率_id : 67日乖離率
        """
        s = self.mv.fetch_taiex_bias(start_date, end_date)
        #將s多一分數欄位當數值大於0時，代表股價在均線之上，給予1分；反之，給予0分
        score = s.apply(lambda x: 1 if x > 0 else 0)
        return score

    def calc_score_otc_bias(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        OTC 指數乖離率_id : 67日乖離率
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWC00',
            'start': start_str,
            'end': end_str,
            'fields': '價格_BIAS_67D',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWC00"]["data"])
           
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                series = df['價格_BIAS_67D']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_otc_bias 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_taiex_macd(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        加權指數MACD_id : MACD線
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWA00',
            'start': start_str,
            'end': end_str,
            'fields': '價格_MACD_12D_26D_9D',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWA00"]["data"])            
           
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                #MACD會傳回三欄:pandas_ta的定義為:macd,signalma,histogram。但對照中文的定義是:dif,macd,dif-macd
                series = df['價格_MACD_12D_26D_9D_2']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_taiex_macd 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_otc_macd(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        加權指數MACD_id
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWC00',
            'start': start_str,
            'end': end_str,
            'fields': '價格_MACD_12D_26D_9D',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWC00"]["data"])
            
           
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                #MACD會傳回三欄:pandas_ta的定義為:macd,signalma,histogram。但對照中文的定義是:dif,macd,dif-macd
                series = df['價格_MACD_12D_26D_9D_2']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_otc_macd 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_taiex_dif(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        加權指數DIF_id
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWA00',
            'start': start_str,
            'end': end_str,
            'fields': '價格_MACD_12D_26D_9D',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWA00"]["data"])
                       
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                #MACD會傳回三欄:pandas_ta的定義為:macd,signalma,histogram。但對照中文的定義是:dif,macd,dif-macd
                series = df['價格_MACD_12D_26D_9D_1']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_taiex_dif 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_taiex_pe(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        加權指數本益比_id
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWA00',
            'start': start_str,
            'end': end_str,
            'fields': '本益比4',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWA00"]["data"])
           
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                series = df['本益比4']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_taiex_pe 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_otc_pe(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        OTC 指數本益比_id
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWC00',
            'start': start_str,
            'end': end_str,
            'fields': '本益比4',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWC00"]["data"])
           
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                series = df['本益比4']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_otc_pe 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_taiex_pb(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        加權指數股價淨值比_id
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWA00',
            'start': start_str,
            'end': end_str,
            'fields': '股價淨值比',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWA00"]["data"])
            
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                series = df['股價淨值比']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_taiex_pb 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise
    def fetch_otc_pb(
        self,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """
        OTC 指數股價淨值比_id
        """

        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

       
        params = {
            'stock_id': 'TWC00',
            'start': start_str,
            'end': end_str,
            'fields': '股價淨值比',
            'format': 'json',
            'api_key': 'guest'
        }

        try:
            response = requests.get(self.URL, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise ValueError(f"API 回傳錯誤狀態: {result.get('status')}")
            # 將資料轉換為 DataFrame
            df = pd.DataFrame.from_records(result["data"]["TWC00"]["data"])
           
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                series = df['股價淨值比']
                series = series.dropna()  # 移除 NaN 值
                return series
            else:
                raise ValueError("fetch_otc_pb 回傳的資料為空")
                
        except requests.RequestException as e:
            print(f"API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"資料處理失敗: {e}")
            raise


# =========================
#   使用範例
# =========================
if __name__ == "__main__":
    import os,sys
    mv = MeasureScore(os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","measure_profile.json"))

    # 1) 計算單一 measure
    s = mv.compute_one("加權指數乖離率_id", "2025-07-01", "2025-12-31")
    print(s.head())
    # 2) 計算全部 measure
    # all = mv.compute_all("2024-07-01", "2025-12-31", frequency="Q")
    # print(all)  

    # 3) 計算全部 measure 並輸出成 measure_value.csv
    # mv.to_csv(
    #     start_date="2024-01-01",
    #     end_date="2025-12-31",
    #     output_path="measure_value.csv",
    #     frequency="Q",
    #     date_format="%Y-%m-%d",

    # )
