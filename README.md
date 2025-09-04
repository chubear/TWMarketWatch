# TWMarketWatch
台股觀測指標

## 專案介紹
本專案提供台灣證券交易所(TWSE)每日收盤價爬蟲功能，能夠從證交所OpenAPI獲取股票市場資料。

## 功能特色
- 📈 獲取每日股票收盤價資料
- 📊 支援全市場或個股資料查詢
- 🏢 獲取集保中心股權分散表資料
- 💾 自動儲存為CSV格式
- 📱 市場概況分析
- 🔄 網路連線失敗時自動切換至模擬資料模式

## 安裝與設定

### 1. 安裝相依套件
```bash
pip install -r requirements.txt
```

### 2. 基本使用
```python
# TWSE 股票收盤價爬蟲
from twse_crawler_demo import TWStockCrawlerDemo

# 建立爬蟲實例
crawler = TWStockCrawlerDemo()

# 獲取今日市場收盤價
market_data = crawler.get_market_closing_prices()
print(market_data)

# 儲存為CSV檔案
crawler.save_to_csv(market_data)
```

```python
# TDCC 集保中心股權分散表爬蟲
from twfincrawler.tdcc import TDCCStockholderStructure

# 建立爬蟲實例
tdcc_crawler = TDCCStockholderStructure()

# 獲取股權分散表資料
stockholder_data = tdcc_crawler.get_stockholder_dataframe()
print(stockholder_data)

# 儲存為CSV檔案
tdcc_crawler.save_to_csv(stockholder_data)
```

## 使用範例

### 執行完整示範
```bash
python twse_crawler_demo.py
```

### 執行使用範例
```bash
# TWSE 股票收盤價爬蟲範例
python example_usage.py

# TDCC 股權分散表爬蟲範例  
python tdcc_example_usage.py
```

## 資料來源
- 台灣證券交易所OpenAPI
- 集保中心(TDCC)OpenAPI
- 當API無法連線時會自動切換至模擬資料模式進行展示

## 輸出格式

### TWSE股票收盤價資料
爬蟲會產生包含以下欄位的CSV檔案：
- 股票代碼
- 股票名稱
- 收盤價
- 漲跌
- 漲跌幅
- 開盤價
- 最高價
- 最低價
- 成交量

### TDCC股權分散表資料
爬蟲會產生包含以下欄位的CSV檔案：
- 資料日期
- 股票代碼
- 股票名稱
- 持股級距
- 股東人數
- 持股股數
- 持股比例

## 檔案說明
- `twse_crawler.py` - 基本爬蟲模組
- `twse_crawler_demo.py` - 含模擬資料的示範版本
- `example_usage.py` - TWSE爬蟲使用範例
- `twfincrawler/tdcc/tdcc_stockholder_structure.py` - TDCC股權分散表爬蟲
- `tdcc_example_usage.py` - TDCC爬蟲使用範例
- `requirements.txt` - 相依套件清單

## 注意事項
- 證交所API僅在交易日提供當日資料
- 集保中心API提供股權分散表資料，更新頻率請參考官方說明
- 建議在API請求間加入適當延遲避免過度請求
- 模擬資料僅供展示功能使用

## 授權
本專案僅供學習研究使用
