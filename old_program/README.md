# 配對交易領先-追隨分析工具

一個基於機構資金流向的股票配對交易分析系統，支援多產業分類管理和跨產業股票搜尋功能。

## 功能特色

- **領先-追隨關係分析**: 識別股票間的領先追隨關係
- **多產業分類管理**: 每個產業獨立目錄存放分析結果
- **跨產業股票搜尋**: 快速查找股票在不同產業中的角色
- **視覺化分析報告**: 自動產生圖表和詳細分析報告
- **交易信號生成**: 基於領先-追隨關係產生交易建議

## 安裝步驟

1. **安裝Python套件依賴**:
```bash
pip install -r requirements.txt
```

## 基本使用方法

### 1. 執行產業分析
```bash
python pair_trade_analyzer.py --csv 數據檔案.csv --industry 產業名稱
```

**範例**:
```bash
# 分析安控產業
python pair_trade_analyzer.py --csv BigBuySell-min.csv --industry security

# 分析USB IC產業  
python pair_trade_analyzer.py --csv USB-IC-BigBuySell-min.csv --industry usb_ic
```

### 2. 搜尋股票功能
```bash
python search_stocks.py 股票代碼
```

**範例**:
```bash
# 搜尋股票3297在各產業中的角色
python search_stocks.py 3297
```

## 輸出說明

程式會在指定的產業名稱子目錄中自動產生以下檔案：

- `leader_analysis.jpg` - 綜合領導力分析圖表
- `leader_follower_analysis.png` - 領先-追隨關係網絡圖  
- `trading_signals_summary.csv` - 交易信號摘要
- `trading_signals_detailed.csv` - 詳細交易信號
- `analysis_explanation.txt` - 分析結果說明
- `pair_chart_XXXX_YYYY.png` - 個別股票對分析圖表

系統還會在根目錄產生 `master_index.json` 作為跨產業索引檔案。

## 資料管理

### 刪除產業資料
如需刪除某個產業的分析結果，直接刪除該產業的目錄即可：
```bash
rm -rf 產業名稱/
```

### 索引檔案更新
- `master_index.json` 只在執行分析時更新
- 刪除產業目錄後，該產業的資料仍會保留在索引檔案中
- 建議刪除產業後重新執行其他產業分析，讓系統更新索引檔案

### 數據格式要求
CSV檔案需包含以下欄位（以空格分隔）：
- 股票代碼、日期、時間、收盤價、成交量、成交量比例
- 漲跌幅、中單買進、大單買進、超大單買進
- 中單賣出、大單賣出、超大單賣出等

## 範例數據

- `BigBuySell-min.csv` - 安控產業範例數據
- `USB-IC-BigBuySell-min.csv` - USB IC產業範例數據

## 注意事項

1. 確保CSV檔案格式正確，欄位以空格分隔
2. 產業名稱建議使用英文或數字，避免特殊字元
3. 程式執行時間視數據量而定，請耐心等待
4. 建議定期備份分析結果