# SectorAnalysis - 台灣股票類股領漲跟漲分析系統

## 概述
本專案提供完整的台灣股票類股分析工具，包含資料下載、轉換與進階領漲跟漲分析功能。系統可自動下載股票TICK資料，轉換為分析格式，並執行類股內的領漲跟漲關係分析。

## 系統架構

### 核心功能模組
1. **資料下載模組** (`GetSectorData.py`) - 從伺服器下載原始股票資料
2. **類股分析模組** (`SectorAnalyzer.py`) - 轉換資料並產生合併資料集
3. **領漲跟漲分析模組** (`sector_leader_follower_analyzer.py`) - 執行進階分析
4. **自動化腳本** (`analyze_sectors.sh`) - 一鍵執行完整分析流程

## 前置需求

### Windows Anaconda環境設定
1. **安裝Anaconda/Miniconda** 於Windows系統
2. **複製DJFile.exe** 至專案工作目錄
   ```
   SectorAnalysis/
   ├── djfile.exe          # 必需：從系統工具複製
   ├── GetSectorData.py    # 主要程式
   ├── sectorInfo/         # 類股定義檔案
   └── CLAUDE.md          # 本說明檔
   ```

### 必需檔案
- **DJFile.exe**：必須複製到工作資料夾才能讓程式正常運作
- **類股檔案**：位於`sectorInfo/`資料夾，使用BIG5編碼
  - 格式：`DJ_XXX.txt`包含股票代號如`3037.TW`
  - 範例：`DJ_IC基板.txt`、`DJ_IC封測.txt`

## 安裝

### 1. 設定Anaconda環境
```bash
# 建立新的conda環境
conda create -n sectoranalysis python=3.9
conda activate sectoranalysis

# 安裝必要套件（如需要超出標準函式庫）
# 所有必要套件皆為Python標準函式庫的一部分
```

### 2. 準備工作目錄
```bash
# 導航至專案目錄
cd /path/to/SectorAnalysis

# 確認djfile.exe在目前目錄中
dir djfile.exe  # 應顯示檔案存在
```

## 使用方法

### 🚀 快速開始 - 完整類股分析

#### 分析所有產業（推薦）
```bash
./analyze_sectors.sh --start 202505 --end 202506
```

#### 分析指定產業
```bash
./analyze_sectors.sh --start 202505 --end 202506 --sectors "IC基板,IC設計,散熱模組"
```

### 📊 分析輸出
每個類股分析會產生以下檔案（位於 `output/{類股名稱}/`）：

#### 核心資料檔案
- **`combined_data_debug.csv`** - 合併的原始資料（32K+ 筆記錄）
- **`analysis_summary.txt`** - 基礎統計分析摘要
- **`leader_follower_analysis_report.txt`** - 詳細領漲跟漲分析報告

#### 視覺化圖表
- **`leader_follower_analysis_relation.png`** - 🌟股票關係圖表
- **`leader_follower_comprehensive_analysis.png`** - 統計圖表
- **`interactive_multi_stock_trend_YYYYMMDD.html`** - 🌟互動式股票走勢圖

#### 數據表格
- **`leader_follower_pairs_detailed.csv`** - 詳細配對數據
- **`leader_follower_summary.csv`** - 配對摘要表
- **`signal_table_YYYYMMDD.csv`** - 信號編號說明表

### 🔧 進階使用

#### 1. 純資料下載
```bash
python GetSectorData.py --start 202505 --end 202506 --sector DJ_IC基板,DJ_IC封測
```

#### 2. 手動兩步驟分析
```bash
# Step 1: 產生 combined_data_debug.csv
python SectorAnalyzer.py --sector DJ_IC基板 --start 202505 --end 202506

# Step 2: 執行領漲跟漲分析
python sector_leader_follower_analyzer.py output/IC基板/combined_data_debug.csv
```

#### 3. 使用自動轉換的CSV分析（實驗性）
```bash
./csv_sector_analyze.sh --start 202505 --end 202506 --sectors "DJ_IC基板"
```

### 📈 分析結果示例

#### 典型輸出摘要（IC基板類股）
```
✓ 發現 62 個有效的領漲跟漲配對
✓ 平均反應時間: 11.5 分鐘
✓ 平均跟漲幅度: 0.92%
✓ 最佳領漲股: 8046
✓ 最佳配對: 8046 → 6552 (成功率: 74%)
```

### 🎯 常用指令範例

#### 分析半導體相關產業
```bash
./analyze_sectors.sh --start 202505 --end 202506 --sectors "IC基板,IC封測,IC設計,IC零組件通路商,LCD驅動IC,MCU"
```

#### 分析被動元件產業
```bash
./analyze_sectors.sh --start 202505 --end 202506 --sectors "被動元件,MLCC,分離式元件"
```

#### 快速測試單一產業
```bash
./analyze_sectors.sh --start 202505 --end 202505 --sectors "IC基板"
```

## 📁 可分析的產業清單

### 所有可用產業（共60+個）
```bash
# 檢視所有可用產業
ls sectorInfo/DJ_*.txt | sed 's/.*DJ_//g' | sed 's/\.txt$//g'
```

**主要產業分類**：
- **半導體**: IC基板, IC封測, IC設計, IC零組件通路商, LCD驅動IC, MCU, 利基型記憶體IC, 記憶體製造, 記憶體模組
- **電子材料**: 被動元件, MLCC, 分離式元件, 印刷電路板, 軟板, 電子化工材料
- **設備製造**: 半導體設備, PCB設備, 工具機業, 設備儀器廠商
- **傳統產業**: 營建, 資產股, 散裝航運, 貨櫃航運, 自行車, 汽車零組件
- **新興科技**: 生物科技, 資安, 軟體, 遊戲相關, 工業電腦

### 🔄 分析所有產業的完整流程

#### 自動分析所有產業
```bash
# 一鍵分析所有60+個產業
./analyze_sectors.sh --start 202505 --end 202506
```

#### 手動批次分析（分組執行）
```bash
# 半導體相關（約15個產業）
./analyze_sectors.sh --start 202505 --end 202506 --sectors "IC基板,IC封測,IC設計,IC零組件通路商,LCD驅動IC,MCU,利基型記憶體IC,半導體封測材料,半導體設備,專業晶圓代工,矽晶圓,砷化鎵相關,記憶體模組,記憶體製造,設計IP"

# 電子材料相關（約10個產業）  
./analyze_sectors.sh --start 202505 --end 202506 --sectors "被動元件,MLCC,分離式元件,印刷電路板,印刷電路板上游與材料,軟板,軟板上游材料,電子化工材料,電線電纜,電腦板卡"

# 設備製造相關（約8個產業）
./analyze_sectors.sh --start 202505 --end 202506 --sectors "PCB設備,半導體設備,工具機業,手工具機業,設備儀器廠商,面板設備,無塵室工程,機器人"
```

### 🔍 combined_data_debug.csv 核心檔案

#### 檔案產生流程
```mermaid
graph LR
    A[原始TXT檔案] --> B[SectorAnalyzer.py]
    B --> C[combined_data_debug.csv]
    C --> D[sector_leader_follower_analyzer.py]
    D --> E[分析報告 + 圖表]
```

#### 檔案內容結構
**combined_data_debug.csv** 包含以下欄位（共20欄）：
- **基礎資訊**: symbol, date, time, datetime
- **價格資料**: open, high, low, close, volume, avg_price  
- **技術指標**: volume_ratio, price_change_pct, volatility
- **大單資料**: med_buy, large_buy, xlarge_buy, med_sell, large_sell, xlarge_sell
- **累積資料**: med_buy_cum, large_buy_cum, xlarge_buy_cum (等)

#### 檔案特色
- **資料量**: 每個產業通常包含 30K+ 筆記錄
- **時間範圍**: 依指定期間，精確到分鐘級別
- **交易時段**: 自動過濾至 09:01-13:30
- **多股票**: 同一檔案包含該產業所有股票資料

## 資料結構

### 輸入資料結構
```
sectorInfo/
├── DJ_IC基板.txt      # 包含：3037.TW, 8046.TW, 3189.TW等
├── DJ_IC封測.txt      
├── DJ_IC設計.txt
└── ... (共60+個產業檔案)
```

### 輸出資料結構
```
D:\lab\TASave\
├── 3037/                          # 股票資料夾（去除.TW）
│   ├── Min_202501.zip             # TICK資料
│   ├── Min_202502.zip
│   ├── TAMin_202501.zip           # TA統計資料
│   ├── TAMin_202502.zip
│   └── [解壓縮檔案]               # 下載後自動解壓縮
├── 8046/
│   ├── Min_202501.zip
│   ├── TAMin_202501.zip
│   └── [解壓縮檔案]
└── ...
```

### 遠端伺服器路徑
- **TICK資料**：`D:\SHARE\TICkSave\TW\{股號前2碼}\{股號}\{西元年}\{月份2碼}\Min_YYYYMM.zip`
- **TA資料**：`D:\SHARE\TASave\TW\{股號前2碼}\{股號}\{西元年}\{月份2碼}\TAMin_YYYYMM.zip`

## 功能特色

### 智慧處理
- **重複處理**：出現在多個類股的股票只處理一次
- **檔案存在檢查**：跳過已存在本地的檔案下載
- **自動解壓縮**：成功下載後自動解壓縮所有zip檔案
- **錯誤處理**：某一股票失敗時繼續處理其他股票

### 記錄功能
- 建立詳細執行記錄檔`GetSectorData.log`
- 主控台輸出顯示即時進度
- 完成時提供統計摘要

### 批次處理
- 單次執行處理多個類股
- 自動處理日期範圍（月份間隔）
- 為每個股票/期間下載TICK和TA資料

## 疑難排解

### 常見問題

#### 找不到DJFile.exe
```
錯誤：找不到DJFile指令
解決方法：複製djfile.exe到工作目錄
```

#### 伺服器拒絕存取
```
錯誤：無法連線到s-vgtick01
解決方法：確認網路存取和伺服器權限
```

#### 找不到類股檔案
```
錯誤：找不到類股檔案：sectorInfo/DJ_XXX.txt
解決方法：檢查類股名稱拼字和檔案是否存在
```

#### BIG5編碼問題
```
錯誤：無法讀取類股檔案
解決方法：確認類股檔案以BIG5編碼儲存
```

## 程式執行流程

1. **解析參數**：驗證日期範圍和類股參數
2. **讀取類股檔案**：從BIG5編碼檔案載入股票代號
3. **產生日期範圍**：建立開始/結束日期間的月份期間
4. **下載階段**：
   - 在D:\lab\TASave\下建立股票資料夾
   - 下載TICK資料（Min_YYYYMM.zip）
   - 下載TA資料（TAMin_YYYYMM.zip）
   - 跳過已存在檔案
5. **解壓縮階段**：解壓縮所有已下載的zip檔案
6. **摘要**：報告下載和解壓縮統計

## 效能說明

- 循序下載以避免伺服器過載
- 每個DJFile指令5分鐘逾時
- 典型類股執行處理約100-200個檔案
- 解壓縮快速（本地檔案操作）

## 開發指令

### 測試
```bash
# 先以小日期範圍測試
python GetSectorData.py --start 202506 --end 202506 --sector DJ_IC基板

# 檢查記錄檔
type GetSectorData.log
```

### 維護
```bash
# 清理測試下載
rmdir /s "D:\lab\TASave\3037"

# 驗證類股檔案編碼
# 使用支援BIG5的文字編輯器檢查類股檔案
```