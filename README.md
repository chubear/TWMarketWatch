# TWMarketWatch - 台股觀測指標系統

這是一個將 Excel 股市分析數據轉換為靜態網頁的系統，專門用於顯示台股投資決策建議表和國外股市投資評等分析表。可部署到 GitHub Pages 進行展示。

## 功能特點

- **Excel 數據讀取**: 自動讀取 `01.股市經濟及市場指標2025Q2.xlsx` 檔案
- **靜態網頁生成**: 將 Excel 表格轉換為美觀的靜態網頁
- **GitHub Pages 支援**: 可直接部署到 GitHub Pages
- **多種查看方式**: 
  - 完整報表頁面 (包含兩個表格)
  - 投資決策建議單獨頁面
  - 投資評等分析單獨頁面
- **JSON API**: 提供 JSON 格式的數據接口
- **響應式設計**: 支援桌面和手機瀏覽

## 數據來源

系統讀取以下工作表的指定範圍：
- **國內股市當年度投資決策建議表**: Range A1:X61
- **國外股市當年度投資評等分析表**: Range A1:X55

## 使用方法

### 1. 安裝依賴
```bash
pip install pandas openpyxl
```

### 2. 生成靜態網站
```bash
python generate_static_site.py
```

### 3. 本地測試 (可選)
```bash
python -m http.server 8000
```
然後訪問 `http://localhost:8000`

### 4. 部署到 GitHub Pages
1. 將生成的 HTML 文件推送到 GitHub
2. 在 Repository 設定中啟用 GitHub Pages
3. 選擇從 main 分支部署

## 生成的檔案

- **`index.html`** - 主頁，顯示兩個完整表格
- **`decision.html`** - 僅顯示投資決策建議表
- **`analysis.html`** - 僅顯示投資評等分析表
- **`data.json`** - JSON 格式的數據接口

## 文件結構

```
TWMarketWatch/
├── generate_static_site.py                   # 靜態網站生成器
├── excel_reader.py                          # Excel 數據讀取模組
├── 01.股市經濟及市場指標2025Q2.xlsx         # 數據源文件
├── index.html                               # 生成的主頁
├── decision.html                            # 生成的決策建議頁
├── analysis.html                            # 生成的評等分析頁
├── data.json                                # 生成的JSON數據
├── static/                                 # 靜態文件
│   └── style.css                          # 樣式表
├── GITHUB_PAGES.md                         # GitHub Pages 部署說明
├── .gitignore                             # Git 忽略文件
└── README.md                              # 說明文件
```

## 技術架構

- **數據處理**: Python pandas + openpyxl
- **靜態網站生成**: 自定義 Python 腳本
- **前端**: Bootstrap 5 + 自定義 CSS
- **字體圖標**: Font Awesome
- **部署**: GitHub Pages

## 特色功能

1. **靜態網站**: 無需服務器，可直接部署到 GitHub Pages
2. **數據自動化**: 一鍵從 Excel 生成完整網站
3. **錯誤處理**: 完善的錯誤提示機制
4. **交互功能**: 點擊表格單元格可高亮顯示
5. **多語言支援**: 完整的繁體中文界面
6. **響應式設計**: 適配各種屏幕尺寸

## 更新數據

當 Excel 文件更新時，只需重新執行：
```bash
python generate_static_site.py
```
然後推送更新的 HTML 文件到 GitHub。

## 開發者

本系統基於 TWMarketWatch 專案開發，用於台股市場分析數據的可視化展示。
