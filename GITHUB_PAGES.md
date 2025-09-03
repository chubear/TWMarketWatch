# GitHub Pages Setup

本專案已轉換為靜態網站，可以直接部署到GitHub Pages。

## 文件說明

- `index.html` - 主頁面，顯示完整的雙表報表
- `decision.html` - 投資決策建議表
- `analysis.html` - 投資評等分析表  
- `data.json` - JSON格式的數據API
- `static/style.css` - 自定義樣式表

## 如何更新數據

1. 確保最新的Excel文件 `01.股市經濟及市場指標2025Q2.xlsx` 在根目錄中
2. 執行靜態網站生成器：
   ```bash
   pip install pandas openpyxl
   python generate_static_site.py
   ```
3. 生成的HTML文件會自動包含最新的Excel數據

## GitHub Pages 部署

1. 將生成的HTML文件推送到main分支
2. 在GitHub Repository設定中啟用GitHub Pages
3. 選擇從main分支部署
4. 網站會自動部署到 `https://[username].github.io/[repository-name]/`

## 本地測試

可以使用Python內建的HTTP服務器來本地測試：

```bash
python -m http.server 8000
```

然後訪問 `http://localhost:8000`

## 文件架構

```
.
├── index.html              # 主頁面
├── decision.html           # 投資決策建議
├── analysis.html           # 投資評等分析
├── data.json              # JSON API數據
├── static/
│   └── style.css          # 自定義樣式
├── generate_static_site.py # 靜態網站生成器
├── excel_reader.py        # Excel數據讀取器
└── 01.股市經濟及市場指標2025Q2.xlsx # Excel數據源
```