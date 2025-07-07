# SectorAnalysis - 台灣股票類股領漲跟漲分析系統

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 📊 概述

**SectorAnalysis** 是一套專為台灣股票市場設計的完整類股分析系統，提供從資料下載、處理到進階領漲跟漲關係分析的完整解決方案。系統可自動下載股票 TICK 資料，轉換為分析格式，並執行類股內的領漲跟漲關係分析。

### 🌟 核心功能

- **🔄 自動化資料下載** - 從伺服器批次下載股票 TICK 和 TA 資料
- **📈 類股分析** - 生成 `combined_data_debug.csv` 合併資料集
- **🎯 領漲跟漲分析** - 識別類股內股票的領漲跟漲關係
- **📊 豐富視覺化** - 生成互動式圖表和分析報告
- **⚡ 批次處理** - 支援同時分析多個類股

## 🚀 快速開始

### 分析所有產業（推薦）
```bash
./analyze_sectors.sh --start 202505 --end 202506
```

### 分析指定產業
```bash
./analyze_sectors.sh --start 202505 --end 202506 --sectors "IC基板,IC設計,散熱模組"
```

## 📁 輸出檔案

每個類股分析會產生以下檔案（位於 `output/{類股名稱}/`）：

### 📄 核心資料檔案
- **`combined_data_debug.csv`** - 🌟 合併的原始資料（30K+ 筆記錄）
- **`leader_follower_analysis_report.txt`** - 詳細領漲跟漲分析報告

### 📊 視覺化圖表
- **`leader_follower_analysis_relation.png`** - 🌟 股票關係圖表
- **`interactive_multi_stock_trend_YYYYMMDD.html`** - 🌟 互動式股票走勢圖
- **`leader_follower_comprehensive_analysis.png`** - 統計圖表

### 📋 數據表格
- **`leader_follower_pairs_detailed.csv`** - 詳細配對數據
- **`leader_follower_summary.csv`** - 配對摘要表

## 📈 分析結果示例

### 典型輸出摘要（IC基板類股）
```
✓ 發現 62 個有效的領漲跟漲配對
✓ 平均反應時間: 11.5 分鐘
✓ 平均跟漲幅度: 0.92%
✓ 最佳領漲股: 8046
✓ 最佳配對: 8046 → 6552 (成功率: 74%)
```

## 🎯 常用指令範例

### 半導體相關產業
```bash
./analyze_sectors.sh --start 202505 --end 202506 --sectors "IC基板,IC封測,IC設計,IC零組件通路商,LCD驅動IC,MCU"
```

### 被動元件產業
```bash
./analyze_sectors.sh --start 202505 --end 202506 --sectors "被動元件,MLCC,分離式元件"
```

### 快速測試單一產業
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
- **半導體**: IC基板, IC封測, IC設計, IC零組件通路商, LCD驅動IC, MCU...
- **電子材料**: 被動元件, MLCC, 分離式元件, 印刷電路板, 軟板...
- **設備製造**: 半導體設備, PCB設備, 工具機業, 設備儀器廠商...
- **傳統產業**: 營建, 資產股, 散裝航運, 貨櫃航運, 自行車...
- **新興科技**: 生物科技, 資安, 軟體, 遊戲相關, 工業電腦...

## 🔧 進階使用

### 1. 純資料下載
```bash
python GetSectorData.py --start 202505 --end 202506 --sector DJ_IC基板,DJ_IC封測
```

### 2. 手動兩步驟分析
```bash
# Step 1: 產生 combined_data_debug.csv
python SectorAnalyzer.py --sector DJ_IC基板 --start 202505 --end 202506

# Step 2: 執行領漲跟漲分析
python sector_leader_follower_analyzer.py output/IC基板/combined_data_debug.csv
```

### 3. 使用自動轉換的CSV分析（實驗性）
```bash
./csv_sector_analyze.sh --start 202505 --end 202506 --sectors "DJ_IC基板"
```

## 🔍 核心檔案：combined_data_debug.csv

### 檔案產生流程
```
原始TXT檔案 → SectorAnalyzer.py → combined_data_debug.csv → sector_leader_follower_analyzer.py → 分析報告
```

### 檔案內容結構
**combined_data_debug.csv** 包含以下欄位（共20欄）：
- **基礎資訊**: symbol, date, time, datetime
- **價格資料**: open, high, low, close, volume, avg_price  
- **技術指標**: volume_ratio, price_change_pct, volatility
- **大單資料**: med_buy, large_buy, xlarge_buy, med_sell, large_sell, xlarge_sell
- **累積資料**: med_buy_cum, large_buy_cum, xlarge_buy_cum (等)

### 檔案特色
- **資料量**: 每個產業通常包含 30K+ 筆記錄
- **時間範圍**: 依指定期間，精確到分鐘級別
- **交易時段**: 自動過濾至 09:01-13:30
- **多股票**: 同一檔案包含該產業所有股票資料

## 🛠️ 安裝需求

### Windows Anaconda環境設定
```bash
# 建立新的conda環境
conda create -n sectoranalysis python=3.9
conda activate sectoranalysis

# 安裝必要套件
pip install pandas numpy matplotlib seaborn plotly
```

### 必需檔案
- **DJFile.exe** - 必須複製到工作資料夾
- **類股檔案** - 位於 `sectorInfo/` 資料夾，使用 BIG5 編碼

## 📂 專案結構

```
SectorAnalysis/
├── djfile.exe                           # 資料下載工具
├── GetSectorData.py                     # 資料下載模組
├── SectorAnalyzer.py                    # 類股分析模組
├── sector_leader_follower_analyzer.py   # 領漲跟漲分析模組
├── analyze_sectors.sh                   # 🌟 主要分析腳本
├── csv_sector_analyze.sh                # CSV分析腳本（實驗性）
├── convert_txt_to_csv.py                # TXT轉CSV工具
├── csv_based_leader_follower_analyzer.py # CSV版分析器
├── sectorInfo/                          # 類股定義檔案
│   ├── DJ_IC基板.txt
│   ├── DJ_IC封測.txt
│   └── ... (60+個產業檔案)
├── output/                              # 分析結果
│   ├── IC基板/
│   ├── 散熱模組/
│   └── ...
├── CLAUDE.md                            # 詳細技術文件
└── README.md                            # 本檔案
```

## 🏃‍♂️ 系統架構

### 核心功能模組
1. **資料下載模組** (`GetSectorData.py`) - 從伺服器下載原始股票資料
2. **類股分析模組** (`SectorAnalyzer.py`) - 轉換資料並產生合併資料集
3. **領漲跟漲分析模組** (`sector_leader_follower_analyzer.py`) - 執行進階分析
4. **自動化腳本** (`analyze_sectors.sh`) - 一鍵執行完整分析流程

### 資料流程
```
伺服器資料 → TICK/TA檔案 → 合併資料集 → 領漲跟漲分析 → 視覺化報告
```

## ❗ 疑難排解

### 常見問題

#### 找不到DJFile.exe
```
錯誤：找不到DJFile指令
解決方法：複製djfile.exe到工作目錄
```

#### 找不到類股檔案
```
錯誤：找不到類股檔案：sectorInfo/DJ_XXX.txt
解決方法：檢查類股名稱拼字和檔案是否存在
```

#### 腳本無法執行多個sectors
```
問題：analyze_sectors.sh 只執行第一個sector
解決方法：確認腳本沒有 set -e，現已修復
```

## 🔧 開發指令

### 測試
```bash
# 先以小日期範圍測試
./analyze_sectors.sh --start 202506 --end 202506 --sectors "IC基板"

# 檢查記錄檔
cat GetSectorData.log
```

### 維護
```bash
# 清理測試輸出
rm -rf output/IC基板

# 檢查所有可用產業
ls sectorInfo/DJ_*.txt | wc -l
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 貢獻

歡迎提交 Pull Request 或 Issue！

## 📞 聯絡

如有問題請透過 GitHub Issues 聯絡。

---

**SectorAnalysis v2.0** | 台灣股票市場類股分析專業工具