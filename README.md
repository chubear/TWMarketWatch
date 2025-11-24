# TWMarketWatch 專案說明

本專案用於抓取台灣股市相關的總經、技術及評價面指標，並生成分析報告。

## 專案架構

- **core/**: 核心邏輯程式碼
  - `config.py`: 設定檔 (API URL, Key 等)
  - `data_fetcher.py`: 資料抓取工具，處理 API 與資料庫請求
  - `measure_value.py`: 負責抓取各項指標的數值
  - `measure_score.py`: 負責計算指標分數
  - `csv_to_report.py`: 產生 CSV 報告的主程式
  - `dbconfig.py`: 資料庫連線設定
- **data/**: 資料存放目錄 (CSV, JSON 設定檔)
- **docs/**: 產出的報告存放目錄
- **tests/**: 單元測試

## 安裝需求

請確保已安裝 Python 3.8+ 及以下套件：

```bash
pip install pandas requests openpyxl
```

## 使用方式

### 1. 產生分析報告

使用 `core.csv_to_report` 模組來產生報告。您可以透過命令列參數指定輸入與輸出檔案。

```bash
# 基本用法 (使用預設路徑)
python3 -m core.csv_to_report

# 指定輸出檔案與日期範圍
python3 -m core.csv_to_report --output_file docs/my_report.csv --start_date 2024/01/01
```

**參數說明:**
- `--value_file`: 數值資料 CSV 路徑 (預設: `data/measure_value.csv`)
- `--score_file`: 分數資料 CSV 路徑 (預設: `data/measure_score.csv`)
- `--profile_file`: 指標設定檔 JSON 路徑 (預設: `data/measure_profile.json`)
- `--output_file`: 輸出報告路徑 (預設: `docs/test_report.csv`)
- `--start_date`: 報告開始日期 (格式: YYYY/MM/DD)
- `--end_date`: 報告結束日期 (格式: YYYY/MM/DD)

### 2. 程式化呼叫

您也可以在 Python 程式中直接使用核心類別：

```python
from core.measure_value import MeasureValue
from core.measure_score import MeasureScore

# 初始化
mv = MeasureValue("data/measure_profile.json")

# 抓取單一指標數值
series = mv.compute_one("taiex_bias", "2024-01-01", "2024-12-31")
print(series)

# 計算所有指標並存為 CSV
mv.to_csv("2024-01-01", "2024-12-31", output_path="data/measure_value.csv")
```

## 測試

本專案包含單元測試，確保核心邏輯正確。

```bash
python3 tests/test_core.py
```

## 資料檔案說明

- **measure_value.csv**: 儲存各指標的歷史數值 (Big5 編碼)
- **measure_score.csv**: 儲存各指標的歷史分數 (Big5 編碼)
- **measure_profile.json**: 定義指標的名稱、單位與對應的函式 (UTF-8 編碼)

## 報告結構

產出的 CSV 報告包含以下資訊：
- **類別**: 指標分類 (總經面、技術面、評價面)
- **指標名稱**: 指標的中文名稱
- **單位**: 指標單位
- **歷史日期欄位**: 該日期的指標數值
- **分數**: 該指標的最新評分
- **類別總分**: 該類別所有指標的分數總和