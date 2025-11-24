from __future__ import annotations

import json
from typing import Union, Any, Dict, Callable
from pathlib import Path
import pandas as pd
from .data_fetcher import  DateLike
from .dbconfig import default_engine
from .measure_value import MeasureValue


class MeasureScore:
    """
    Responsible for calling the corresponding measure method in this class 
    according to the settings in measure_profile.json, generating a DataFrame or CSV of measure_score.
    """

    def __init__(self, profile_path: Union[str, Path], encoding: str = "utf-8-sig", engine=None):
        self.profile_path = Path(profile_path)
        self.encoding = encoding
        self.engine = engine or default_engine()
        self.measure_profile: Dict[str, Dict[str, Any]] = self._load_measure_profile()
        self.mv = MeasureValue(profile_path, encoding, engine or default_engine())

    def _load_measure_profile(self) -> Dict[str, Dict[str, Any]]:
        """Load measure profile from JSON file"""
        with self.profile_path.open("r", encoding=self.encoding) as f:
            return json.load(f)

    def _get_measure_func(self, measure_id: str) -> Callable[..., pd.Series]:
        """Get the method corresponding to the measure_id"""
        cfg = self.measure_profile.get(measure_id)
        if cfg is None:
            raise KeyError(f"measure_id {measure_id} does not exist in measure_profile.json")

        func_name = cfg.get("func_score")
        if not isinstance(func_name, str):
            raise TypeError(f"measure_id {measure_id} 'func_score' setting must be a string (method name)")

        if not hasattr(self, func_name):
            raise AttributeError(f"{self.__class__.__name__} does not have method '{func_name}' (for {measure_id})")

        return getattr(self, func_name)

    # =========================
    #   Public API
    # =========================
    def compute_one(
        self,
        measure_id: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> pd.Series:
        """Compute a single measure score"""
        func = self._get_measure_func(measure_id)
        series = func(start_date, end_date)

        if not isinstance(series, pd.Series):
            raise TypeError(f"{measure_id} function {func.__name__} did not return pd.Series")

        series.name = measure_id
        return series

    def compute_all(
        self,
        start_date: DateLike,
        end_date: DateLike,
        how: str = "outer",
        frequency: str = "D"
    ) -> pd.DataFrame:
        """Compute all measure scores in the profile"""
        series_dict: Dict[str, pd.Series] = {}

        for measure_id in self.measure_profile.keys():
            # Check if the measure has func_score
            if "func_score" not in self.measure_profile[measure_id]:
                continue
                 
            print(f"Computing {measure_id} ...")
            try:
                s = self.compute_one(measure_id, start_date, end_date)
                series_dict[measure_id] = s
            except Exception as e:
                print(f"Error computing {measure_id}: {e}")

        if not series_dict:
            return pd.DataFrame()

        df = pd.concat(series_dict.values(), axis=1, join=how).ffill()#為了解決資料間頻率不同的問題
        df = df.groupby(df.index.to_period(frequency)).tail(1)
        df.index = df.index.to_period(frequency).to_timestamp(how='end')
        
        return df

    def to_csv(
        self,
        start_date: DateLike,
        end_date: DateLike,
        output_path: Union[str, Path] = "measure_score.csv",
        how: str = "outer",
        frequency: str = "D",
        csv_encoding: str = "utf-8-sig",
        date_format: str = "%Y/%m/%d",
    ) -> pd.DataFrame:
        """Compute all and save to CSV"""
        df = self.compute_all(
            start_date=start_date,
            end_date=end_date,
            how=how,
            frequency=frequency
        )

        df_out = df.copy()
        if isinstance(df_out.index, pd.DatetimeIndex):
            df_out.insert(0, "Date", df_out.index.strftime(date_format))
        else:
            df_out.insert(0, "Date", df_out.index.astype(str))

        df_out.reset_index(drop=True, inplace=True)

        output_path = Path(output_path)
        df_out.to_csv(output_path, index=False, encoding=csv_encoding)
        print(f"Saved to {output_path}")
        return df_out

    # ==============================================
    #   Score Calculation Methods
    # ==============================================
    def calc_score_taiwan_leading_indicator(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_leading_indicator : 台灣領先指標"""
        s = self.mv.fetch_taiwan_leading_indicator(start_date, end_date)
        return s.apply(lambda x: 4 if x > 105.954 else (3 if x > 87.392 else 0))
    
    def calc_score_pmi_manufacturing_index(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """pmi_manufacturing_index : PMI製造業指數"""
        s = self.mv.fetch_pmi_manufacturing_index(start_date, end_date)
        return s.apply(lambda x: 4 if x > 52.6 else (3 if x > 47.3 else 0))

    def calc_score_taiwan_export_orders(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_export_orders : 台灣外銷訂單"""
        s = self.mv.fetch_taiwan_export_orders(start_date, end_date)
        return s.apply(lambda x: 4 if x > 37625.2 else (3 if x > 31362.6 else 0))
    
    def calc_score_taiwan_industrial_production(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_industrial_production : 台灣工業生產指數"""
        s = self.mv.fetch_taiwan_industrial_production(start_date, end_date)
        return s.apply(lambda x: 4 if x > 104.63 else (3 if x > 89.39 else 0))

    def calc_score_taiwan_trade_balance(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_trade_balance : 台灣貿易收支"""
        s = self.mv.fetch_taiwan_trade_balance(start_date, end_date)
        return s.apply(lambda x: 4 if x > 3.49 else (3 if x > 1.52 else 0))

    def calc_score_taiwan_retail_sales(self, start_date: DateLike, end_date: DateLike) -> pd.Series:    
        """台灣零售銷售額_id : 台灣零售銷售額"""
        s = self.mv.fetch_taiwan_retail_sales(start_date, end_date)
        return s.apply(lambda x: 4 if x > 328.75 else (3 if x > 279.9 else 0))

    def calc_score_taiwan_unemployment_rate(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_unemployment_rate : 失業率"""
        s = self.mv.fetch_taiwan_unemployment_rate(start_date, end_date)
        return s.apply(lambda x: 4 if x < 3.94 else (3 if x < 4.3 else 0))

    def calc_score_taiwan_cpi(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_cpi : 消費者物價指數"""
        s = self.mv.fetch_taiwan_cpi(start_date, end_date)
        return s.apply(lambda x: 4 if x > 1.66 else (3 if x > 0.072 else 0))

    def calc_score_taiwan_m1b_m2(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiwan_m1b_m2 : M1B-M2"""
        s = self.mv.fetch_taiwan_m1b_m2(start_date, end_date)
        return s.apply(lambda x: 4 if x > 0.03 else (3 if x > -0.01 else 0))
    
    def calc_score_taiex_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_bias : 67日乖離率"""
        s = self.mv.fetch_taiex_bias(start_date, end_date)
        return s.apply(lambda x: 4 if x > 2.72 else (3 if x > -2.68 else 0))

    def calc_score_otc_bias(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數乖離率_id : 67日乖離率"""
        s = self.mv.fetch_otc_bias(start_date, end_date)
        return s.apply(lambda x: 4 if x > 3.0 else (3 if x > -3.94 else 0))

    def calc_score_taiex_macd(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_macd : MACD"""
        s = self.mv.fetch_taiex_macd(start_date, end_date)
        return s.apply(lambda x: 4 if x > 283.34 else (3 if x > -29.68 else 0))
    
    def calc_score_otc_macd(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC MACD_id : MACD"""
        s = self.mv.fetch_otc_macd(start_date, end_date)
        return s.apply(lambda x: 4 if x > 3.57 else (3 if x > -5.68 else 0))    
    
    def calc_score_taiex_dif(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_dif : DIF"""
        s = self.mv.fetch_taiex_dif(start_date, end_date)
        return s.apply(lambda x: 4 if x > 283.34 else (3 if x > -29.68 else 0))
    
    def calc_score_taiex_adx(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_adx : ADX"""
        s = self.mv.fetch_taiex_adx(start_date, end_date)
        return s.apply(lambda x: 4 if x > 19.61 else (3 if x > 12.2 else 0))

    def calc_score_taiex_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_pe : 本益比"""
        s = self.mv.fetch_taiex_pe(start_date, end_date)
        return s.apply(lambda x: 4 if x < 13.4 else (3 if x < 15.52 else 0))    

    def calc_score_tw50_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """tw50_pe : 本益比"""
        s = self.mv.fetch_tw50_pe(start_date, end_date)
        return s.apply(lambda x: 4 if x < 13.5 else (3 if x < 15.4 else 0))        
    
    def calc_score_mid100_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣中型100指數本益比 : 本益比"""
        s = self.mv.fetch_mid100_pe(start_date, end_date)
        return s.apply(lambda x: 4 if x < 13.8 else (3 if x < 15.7 else 0))

    def calc_score_highdiv_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣高股息指數本益比 : 本益比"""
        s = self.mv.fetch_highdiv_pe(start_date, end_date)
        return s.apply(lambda x: 4 if x < 11.8 else (3 if x < 14.34 else 0))    
    
    def calc_score_otc_pe(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數本益比 : 本益比"""
        s = self.mv.fetch_otc_pe(start_date, end_date)
        return s.apply(lambda x: 4 if x < 17.64 else (3 if x < 22.2 else 0)) 
    
    def calc_score_taiex_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """taiex_pb : 股價淨值比"""
        s = self.mv.fetch_taiex_pb(start_date, end_date)
        return s.apply(lambda x: 4 if x < 1.63 else (3 if x < 1.76 else 0)) 

    def calc_score_tw50_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣50指數股價淨值比_id : 股價淨值比"""
        s = self.mv.fetch_tw50_pb(start_date, end_date)
        return s.apply(lambda x: 4 if x < 1.81 else (3 if x < 1.96 else 0)) 

    def calc_score_mid100_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣中型100指數股價淨值比_id : 股價淨值比"""
        s = self.mv.fetch_mid100_pb(start_date, end_date)
        return s.apply(lambda x: 4 if x < 1.36 else (3 if x < 1.55 else 0)) 
    
    def calc_score_highdiv_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """台灣高股息指數股價淨值比_id : 股價淨值比"""
        s = self.mv.fetch_highdiv_pb(start_date, end_date)
        return s.apply(lambda x: 4 if x < 1.44 else (3 if x < 1.84 else 0)) 
    
    def calc_score_otc_pb(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """OTC 指數股價淨值比_id : 股價淨值比"""
        s = self.mv.fetch_otc_pb(start_date, end_date)
        return s.apply(lambda x: 4 if x < 1.64 else (3 if x < 1.97 else 0))
    #海外指標
    def calc_score_global_gdp_real_growth_rate(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """global_gdp_real_growth_rate : 實質GDP成長率"""
        s = self.mv.fetch_global_gdp_real_growth_rate(start_date, end_date)
        return s.apply(lambda x: 4 if x > 4.11 else (3 if x > 1.6 else 0))
    
    def calc_score_us_leading_indicator(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_leading_indicator : 美國領先指標"""
        s = self.mv.fetch_us_leading_indicator(start_date, end_date)
        return s.apply(lambda x: 4 if x > 118.3 else (3 if x > 100.98 else 0))
    
    def calc_score_us_pmi_manufacturing_index(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_pmi_manufacturing_index : ISM製造業指數"""
        s = self.mv.fetch_us_pmi_manufacturing_index(start_date, end_date)
        return s.apply(lambda x: 4 if x > 55.06 else (3 if x > 49.82 else 0))
    
    def calc_score_us_durable_goods_orders(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_durable_goods_orders : 美國耐久財訂單"""
        s = self.mv.fetch_us_durable_goods_orders(start_date, end_date)
        return s.apply(lambda x: 4 if x > 229818 else (3 if x > 194326 else 0))
    
    def calc_score_us_retail_sales(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_retail_sales : 美國零售銷售"""
        s = self.mv.fetch_us_retail_sales(start_date, end_date)
        return s.apply(lambda x: 4 if x > 435.2128 else (3 if x > 360.208 else 0))
    
    def calc_score_us_employment_mom(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_employment_mom : 美國就業數據(MOM)"""
        s = self.mv.fetch_us_employment_mom(start_date, end_date)
        return s.apply(lambda x: 4 if x > 225.2 else (3 if x > -68 else 0))
    
    def calc_score_us_unemployment_rate(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_unemployment_rate : 美國失業率"""
        s = self.mv.fetch_us_unemployment_rate(start_date, end_date)
        return s.apply(lambda x: 4 if x < 5 else (3 if x < 8.3 else 0))
    
    def calc_score_us_cpi_yoy(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_cpi_yoy : 美國CPI年增率"""
        s = self.mv.fetch_us_cpi_yoy(start_date, end_date)
        return s.apply(lambda x: 4 if x > 0.02 else (3 if x > 0.01 else 0))
    
    def calc_score_us_existing_home_sales(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_existing_home_sales : 成屋銷售量"""
        s = self.mv.fetch_us_existing_home_sales(start_date, end_date)
        return s.apply(lambda x: 4 if x > 5.09 else (3 if x > 4.17 else 0))
    
    def calc_score_us_m1_m2(self, start_date: DateLike, end_date: DateLike) -> pd.Series:
        """us_m1_m2 : 美國M1-M2"""
        s = self.mv.fetch_us_m1_m2(start_date, end_date)
        return s.apply(lambda x: 4 if x > 0.0506977982101653 else (3 if x > 0.00914105740191716 else 0))