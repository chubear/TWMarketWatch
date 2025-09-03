# TWMarketWatch - 台股觀測指標系統

這是一個將 Excel 股市分析數據轉換為網頁顯示的系統，專門用於顯示台股投資決策建議表和國外股市投資評等分析表。

## 功能特點

- **Excel 數據讀取**: 自動讀取 `01.股市經濟及市場指標2025Q2.xlsx` 檔案
- **網頁顯示**: 將 Excel 表格轉換為美觀的網頁界面
- **多種查看方式**: 
  - 完整報表頁面 (包含兩個表格)
  - 投資決策建議單獨頁面
  - 投資評等分析單獨頁面
- **API 接口**: 提供 JSON 格式的數據接口
- **響應式設計**: 支援桌面和手機瀏覽

## 數據來源

系統讀取以下工作表的指定範圍：
- **國內股市當年度投資決策建議表**: Range A1:X61
- **國外股市當年度投資評等分析表**: Range A1:X55

## 安裝與運行

### 1. 安裝依賴
```bash
pip install pandas openpyxl flask
```

### 2. 運行應用
```bash
python app.py
```

### 3. 瀏覽器訪問
打開瀏覽器，訪問 `http://localhost:5000`

## 頁面說明

- **`/`** - 主頁，顯示兩個完整表格
- **`/decision`** - 僅顯示投資決策建議表
- **`/analysis`** - 僅顯示投資評等分析表
- **`/api/data`** - JSON 格式的數據接口
- **`/refresh`** - 重新載入 Excel 數據

## 文件結構

```
TWMarketWatch/
├── app.py                                    # Flask 主應用程式
├── excel_reader.py                          # Excel 數據讀取模組
├── 01.股市經濟及市場指標2025Q2.xlsx         # 數據源文件
├── templates/                               # HTML 模板
│   ├── base.html                           # 基礎模板
│   ├── index.html                          # 主頁模板
│   ├── single_table.html                   # 單表模板
│   └── error.html                          # 錯誤頁面模板
├── static/                                 # 靜態文件
│   └── style.css                          # 樣式表
├── .gitignore                             # Git 忽略文件
└── README.md                              # 說明文件
```

## 技術架構

- **後端**: Python Flask
- **數據處理**: pandas + openpyxl
- **前端**: Bootstrap 5 + 自定義 CSS
- **字體圖標**: Font Awesome

## 特色功能

1. **數據緩存**: 避免重複讀取 Excel 文件
2. **錯誤處理**: 完善的錯誤提示機制
3. **交互功能**: 點擊表格單元格可高亮顯示
4. **多語言支援**: 完整的繁體中文界面
5. **響應式設計**: 適配各種屏幕尺寸

## 開發者

本系統基於 TWMarketWatch 專案開發，用於台股市場分析數據的可視化展示。
