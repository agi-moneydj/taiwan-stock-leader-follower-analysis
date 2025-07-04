# SectorAnalysis - 股票資料下載工具

## 概述
本專案提供Python腳本，用於透過DJFile指令從s-vgtick01伺服器下載股票市場資料（TICK資料和TA統計資料）。此腳本可處理多個類股，並自動處理跨類股的重複股票。

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

### 基本指令結構
```bash
python GetSectorData.py --start YYYYMM --end YYYYMM --sector SECTOR_LIST
```

### 參數說明
- `--start`：開始期間，YYYYMM格式（例：202501）
- `--end`：結束期間，YYYYMM格式（例：202506）
- `--sector`：逗號分隔的類股名稱清單（例：DJ_IC基板,DJ_IC封測）

### 使用範例

#### 單一類股
```bash
python GetSectorData.py --start 202501 --end 202506 --sector DJ_IC基板
```

#### 多個類股
```bash
python GetSectorData.py --start 202501 --end 202506 --sector DJ_IC基板,DJ_IC封測,DJ_IC設計
```

#### 擴展日期範圍
```bash
python GetSectorData.py --start 202401 --end 202512 --sector DJ_IC基板,DJ_MLCC,DJ_PCB設備
```

## 資料結構

### 輸入資料結構
```
sectorInfo/
├── DJ_IC基板.txt      # 包含：3037.TW, 8046.TW, 3189.TW等
├── DJ_IC封測.txt      
├── DJ_IC設計.txt
└── ...
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