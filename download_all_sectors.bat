@echo off
REM Download commands for all sectors (Period: 202501-202506)
REM Total sectors: 66
REM Excluding: DJ_IC基板

REM [1/66] DJ_IC封測
echo Downloading DJ_IC封測...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_IC封測
if errorlevel 1 (
    echo ERROR: Failed to download DJ_IC封測
    pause
) else (
    echo SUCCESS: DJ_IC封測 downloaded
)

REM [2/66] DJ_IC設計
echo Downloading DJ_IC設計...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_IC設計
if errorlevel 1 (
    echo ERROR: Failed to download DJ_IC設計
    pause
) else (
    echo SUCCESS: DJ_IC設計 downloaded
)

REM [3/66] DJ_IC零組件通路商
echo Downloading DJ_IC零組件通路商...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_IC零組件通路商
if errorlevel 1 (
    echo ERROR: Failed to download DJ_IC零組件通路商
    pause
) else (
    echo SUCCESS: DJ_IC零組件通路商 downloaded
)

REM [4/66] DJ_LCD驅動IC
echo Downloading DJ_LCD驅動IC...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_LCD驅動IC
if errorlevel 1 (
    echo ERROR: Failed to download DJ_LCD驅動IC
    pause
) else (
    echo SUCCESS: DJ_LCD驅動IC downloaded
)

REM [5/66] DJ_MCU
echo Downloading DJ_MCU...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_MCU
if errorlevel 1 (
    echo ERROR: Failed to download DJ_MCU
    pause
) else (
    echo SUCCESS: DJ_MCU downloaded
)

REM [6/66] DJ_MLCC
echo Downloading DJ_MLCC...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_MLCC
if errorlevel 1 (
    echo ERROR: Failed to download DJ_MLCC
    pause
) else (
    echo SUCCESS: DJ_MLCC downloaded
)

REM [7/66] DJ_PCB設備
echo Downloading DJ_PCB設備...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_PCB設備
if errorlevel 1 (
    echo ERROR: Failed to download DJ_PCB設備
    pause
) else (
    echo SUCCESS: DJ_PCB設備 downloaded
)

REM [8/66] DJ_USB IC
echo Downloading DJ_USB IC...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_USB IC
if errorlevel 1 (
    echo ERROR: Failed to download DJ_USB IC
    pause
) else (
    echo SUCCESS: DJ_USB IC downloaded
)

REM [9/66] DJ_不織布
echo Downloading DJ_不織布...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_不織布
if errorlevel 1 (
    echo ERROR: Failed to download DJ_不織布
    pause
) else (
    echo SUCCESS: DJ_不織布 downloaded
)

REM [10/66] DJ_不鏽鋼
echo Downloading DJ_不鏽鋼...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_不鏽鋼
if errorlevel 1 (
    echo ERROR: Failed to download DJ_不鏽鋼
    pause
) else (
    echo SUCCESS: DJ_不鏽鋼 downloaded
)

REM [11/66] DJ_保健品
echo Downloading DJ_保健品...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_保健品
if errorlevel 1 (
    echo ERROR: Failed to download DJ_保健品
    pause
) else (
    echo SUCCESS: DJ_保健品 downloaded
)

REM [12/66] DJ_光固化材料
echo Downloading DJ_光固化材料...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_光固化材料
if errorlevel 1 (
    echo ERROR: Failed to download DJ_光固化材料
    pause
) else (
    echo SUCCESS: DJ_光固化材料 downloaded
)

REM [13/66] DJ_光學鏡頭
echo Downloading DJ_光學鏡頭...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_光學鏡頭
if errorlevel 1 (
    echo ERROR: Failed to download DJ_光學鏡頭
    pause
) else (
    echo SUCCESS: DJ_光學鏡頭 downloaded
)

REM [14/66] DJ_光纖產品
echo Downloading DJ_光纖產品...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_光纖產品
if errorlevel 1 (
    echo ERROR: Failed to download DJ_光纖產品
    pause
) else (
    echo SUCCESS: DJ_光纖產品 downloaded
)

REM [15/66] DJ_分離式元件
echo Downloading DJ_分離式元件...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_分離式元件
if errorlevel 1 (
    echo ERROR: Failed to download DJ_分離式元件
    pause
) else (
    echo SUCCESS: DJ_分離式元件 downloaded
)

REM [16/66] DJ_利基型記憶體IC
echo Downloading DJ_利基型記憶體IC...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_利基型記憶體IC
if errorlevel 1 (
    echo ERROR: Failed to download DJ_利基型記憶體IC
    pause
) else (
    echo SUCCESS: DJ_利基型記憶體IC downloaded
)

REM [17/66] DJ_半導體封測材料
echo Downloading DJ_半導體封測材料...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_半導體封測材料
if errorlevel 1 (
    echo ERROR: Failed to download DJ_半導體封測材料
    pause
) else (
    echo SUCCESS: DJ_半導體封測材料 downloaded
)

REM [18/66] DJ_半導體設備
echo Downloading DJ_半導體設備...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_半導體設備
if errorlevel 1 (
    echo ERROR: Failed to download DJ_半導體設備
    pause
) else (
    echo SUCCESS: DJ_半導體設備 downloaded
)

REM [19/66] DJ_印刷電路板
echo Downloading DJ_印刷電路板...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_印刷電路板
if errorlevel 1 (
    echo ERROR: Failed to download DJ_印刷電路板
    pause
) else (
    echo SUCCESS: DJ_印刷電路板 downloaded
)

REM [20/66] DJ_印刷電路板上游與材料
echo Downloading DJ_印刷電路板上游與材料...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_印刷電路板上游與材料
if errorlevel 1 (
    echo ERROR: Failed to download DJ_印刷電路板上游與材料
    pause
) else (
    echo SUCCESS: DJ_印刷電路板上游與材料 downloaded
)

REM [21/66] DJ_原料藥
echo Downloading DJ_原料藥...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_原料藥
if errorlevel 1 (
    echo ERROR: Failed to download DJ_原料藥
    pause
) else (
    echo SUCCESS: DJ_原料藥 downloaded
)

REM [22/66] DJ_基因檢測服務
echo Downloading DJ_基因檢測服務...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_基因檢測服務
if errorlevel 1 (
    echo ERROR: Failed to download DJ_基因檢測服務
    pause
) else (
    echo SUCCESS: DJ_基因檢測服務 downloaded
)

REM [23/66] DJ_太陽能
echo Downloading DJ_太陽能...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_太陽能
if errorlevel 1 (
    echo ERROR: Failed to download DJ_太陽能
    pause
) else (
    echo SUCCESS: DJ_太陽能 downloaded
)

REM [24/66] DJ_安全監控系統
echo Downloading DJ_安全監控系統...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_安全監控系統
if errorlevel 1 (
    echo ERROR: Failed to download DJ_安全監控系統
    pause
) else (
    echo SUCCESS: DJ_安全監控系統 downloaded
)

REM [25/66] DJ_專業晶圓代工
echo Downloading DJ_專業晶圓代工...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_專業晶圓代工
if errorlevel 1 (
    echo ERROR: Failed to download DJ_專業晶圓代工
    pause
) else (
    echo SUCCESS: DJ_專業晶圓代工 downloaded
)

REM [26/66] DJ_工具機業
echo Downloading DJ_工具機業...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_工具機業
if errorlevel 1 (
    echo ERROR: Failed to download DJ_工具機業
    pause
) else (
    echo SUCCESS: DJ_工具機業 downloaded
)

REM [27/66] DJ_工業電腦
echo Downloading DJ_工業電腦...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_工業電腦
if errorlevel 1 (
    echo ERROR: Failed to download DJ_工業電腦
    pause
) else (
    echo SUCCESS: DJ_工業電腦 downloaded
)

REM [28/66] DJ_平板鋼
echo Downloading DJ_平板鋼...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_平板鋼
if errorlevel 1 (
    echo ERROR: Failed to download DJ_平板鋼
    pause
) else (
    echo SUCCESS: DJ_平板鋼 downloaded
)

REM [29/66] DJ_手工具機業
echo Downloading DJ_手工具機業...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_手工具機業
if errorlevel 1 (
    echo ERROR: Failed to download DJ_手工具機業
    pause
) else (
    echo SUCCESS: DJ_手工具機業 downloaded
)

REM [30/66] DJ_散熱模組
echo Downloading DJ_散熱模組...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_散熱模組
if errorlevel 1 (
    echo ERROR: Failed to download DJ_散熱模組
    pause
) else (
    echo SUCCESS: DJ_散熱模組 downloaded
)

REM [31/66] DJ_散裝航運
echo Downloading DJ_散裝航運...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_散裝航運
if errorlevel 1 (
    echo ERROR: Failed to download DJ_散裝航運
    pause
) else (
    echo SUCCESS: DJ_散裝航運 downloaded
)

REM [32/66] DJ_文創產業
echo Downloading DJ_文創產業...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_文創產業
if errorlevel 1 (
    echo ERROR: Failed to download DJ_文創產業
    pause
) else (
    echo SUCCESS: DJ_文創產業 downloaded
)

REM [33/66] DJ_機器人
echo Downloading DJ_機器人...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_機器人
if errorlevel 1 (
    echo ERROR: Failed to download DJ_機器人
    pause
) else (
    echo SUCCESS: DJ_機器人 downloaded
)

REM [34/66] DJ_汽車零組件
echo Downloading DJ_汽車零組件...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_汽車零組件
if errorlevel 1 (
    echo ERROR: Failed to download DJ_汽車零組件
    pause
) else (
    echo SUCCESS: DJ_汽車零組件 downloaded
)

REM [35/66] DJ_消費用電池
echo Downloading DJ_消費用電池...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_消費用電池
if errorlevel 1 (
    echo ERROR: Failed to download DJ_消費用電池
    pause
) else (
    echo SUCCESS: DJ_消費用電池 downloaded
)

REM [36/66] DJ_無塵室工程
echo Downloading DJ_無塵室工程...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_無塵室工程
if errorlevel 1 (
    echo ERROR: Failed to download DJ_無塵室工程
    pause
) else (
    echo SUCCESS: DJ_無塵室工程 downloaded
)

REM [37/66] DJ_營建
echo Downloading DJ_營建...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_營建
if errorlevel 1 (
    echo ERROR: Failed to download DJ_營建
    pause
) else (
    echo SUCCESS: DJ_營建 downloaded
)

REM [38/66] DJ_玻纖布
echo Downloading DJ_玻纖布...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_玻纖布
if errorlevel 1 (
    echo ERROR: Failed to download DJ_玻纖布
    pause
) else (
    echo SUCCESS: DJ_玻纖布 downloaded
)

REM [39/66] DJ_生物科技
echo Downloading DJ_生物科技...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_生物科技
if errorlevel 1 (
    echo ERROR: Failed to download DJ_生物科技
    pause
) else (
    echo SUCCESS: DJ_生物科技 downloaded
)

REM [40/66] DJ_石英元件
echo Downloading DJ_石英元件...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_石英元件
if errorlevel 1 (
    echo ERROR: Failed to download DJ_石英元件
    pause
) else (
    echo SUCCESS: DJ_石英元件 downloaded
)

REM [41/66] DJ_矽晶圓
echo Downloading DJ_矽晶圓...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_矽晶圓
if errorlevel 1 (
    echo ERROR: Failed to download DJ_矽晶圓
    pause
) else (
    echo SUCCESS: DJ_矽晶圓 downloaded
)

REM [42/66] DJ_砷化鎵相關
echo Downloading DJ_砷化鎵相關...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_砷化鎵相關
if errorlevel 1 (
    echo ERROR: Failed to download DJ_砷化鎵相關
    pause
) else (
    echo SUCCESS: DJ_砷化鎵相關 downloaded
)

REM [43/66] DJ_肥料
echo Downloading DJ_肥料...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_肥料
if errorlevel 1 (
    echo ERROR: Failed to download DJ_肥料
    pause
) else (
    echo SUCCESS: DJ_肥料 downloaded
)

REM [44/66] DJ_自行車
echo Downloading DJ_自行車...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_自行車
if errorlevel 1 (
    echo ERROR: Failed to download DJ_自行車
    pause
) else (
    echo SUCCESS: DJ_自行車 downloaded
)

REM [45/66] DJ_被動元件
echo Downloading DJ_被動元件...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_被動元件
if errorlevel 1 (
    echo ERROR: Failed to download DJ_被動元件
    pause
) else (
    echo SUCCESS: DJ_被動元件 downloaded
)

REM [46/66] DJ_記憶體模組
echo Downloading DJ_記憶體模組...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_記憶體模組
if errorlevel 1 (
    echo ERROR: Failed to download DJ_記憶體模組
    pause
) else (
    echo SUCCESS: DJ_記憶體模組 downloaded
)

REM [47/66] DJ_記憶體製造
echo Downloading DJ_記憶體製造...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_記憶體製造
if errorlevel 1 (
    echo ERROR: Failed to download DJ_記憶體製造
    pause
) else (
    echo SUCCESS: DJ_記憶體製造 downloaded
)

REM [48/66] DJ_設備儀器廠商
echo Downloading DJ_設備儀器廠商...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_設備儀器廠商
if errorlevel 1 (
    echo ERROR: Failed to download DJ_設備儀器廠商
    pause
) else (
    echo SUCCESS: DJ_設備儀器廠商 downloaded
)

REM [49/66] DJ_設計IP
echo Downloading DJ_設計IP...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_設計IP
if errorlevel 1 (
    echo ERROR: Failed to download DJ_設計IP
    pause
) else (
    echo SUCCESS: DJ_設計IP downloaded
)

REM [50/66] DJ_貨櫃航運
echo Downloading DJ_貨櫃航運...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_貨櫃航運
if errorlevel 1 (
    echo ERROR: Failed to download DJ_貨櫃航運
    pause
) else (
    echo SUCCESS: DJ_貨櫃航運 downloaded
)

REM [51/66] DJ_資安
echo Downloading DJ_資安...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_資安
if errorlevel 1 (
    echo ERROR: Failed to download DJ_資安
    pause
) else (
    echo SUCCESS: DJ_資安 downloaded
)

REM [52/66] DJ_資產股
echo Downloading DJ_資產股...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_資產股
if errorlevel 1 (
    echo ERROR: Failed to download DJ_資產股
    pause
) else (
    echo SUCCESS: DJ_資產股 downloaded
)

REM [53/66] DJ_軟板
echo Downloading DJ_軟板...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_軟板
if errorlevel 1 (
    echo ERROR: Failed to download DJ_軟板
    pause
) else (
    echo SUCCESS: DJ_軟板 downloaded
)

REM [54/66] DJ_軟板上游材料
echo Downloading DJ_軟板上游材料...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_軟板上游材料
if errorlevel 1 (
    echo ERROR: Failed to download DJ_軟板上游材料
    pause
) else (
    echo SUCCESS: DJ_軟板上游材料 downloaded
)

REM [55/66] DJ_軟體
echo Downloading DJ_軟體...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_軟體
if errorlevel 1 (
    echo ERROR: Failed to download DJ_軟體
    pause
) else (
    echo SUCCESS: DJ_軟體 downloaded
)

REM [56/66] DJ_遊戲相關
echo Downloading DJ_遊戲相關...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_遊戲相關
if errorlevel 1 (
    echo ERROR: Failed to download DJ_遊戲相關
    pause
) else (
    echo SUCCESS: DJ_遊戲相關 downloaded
)

REM [57/66] DJ_重電業
echo Downloading DJ_重電業...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_重電業
if errorlevel 1 (
    echo ERROR: Failed to download DJ_重電業
    pause
) else (
    echo SUCCESS: DJ_重電業 downloaded
)

REM [58/66] DJ_電子化工材料
echo Downloading DJ_電子化工材料...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_電子化工材料
if errorlevel 1 (
    echo ERROR: Failed to download DJ_電子化工材料
    pause
) else (
    echo SUCCESS: DJ_電子化工材料 downloaded
)

REM [59/66] DJ_電子驗證相關
echo Downloading DJ_電子驗證相關...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_電子驗證相關
if errorlevel 1 (
    echo ERROR: Failed to download DJ_電子驗證相關
    pause
) else (
    echo SUCCESS: DJ_電子驗證相關 downloaded
)

REM [60/66] DJ_電池材料相關
echo Downloading DJ_電池材料相關...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_電池材料相關
if errorlevel 1 (
    echo ERROR: Failed to download DJ_電池材料相關
    pause
) else (
    echo SUCCESS: DJ_電池材料相關 downloaded
)

REM [61/66] DJ_電線電纜
echo Downloading DJ_電線電纜...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_電線電纜
if errorlevel 1 (
    echo ERROR: Failed to download DJ_電線電纜
    pause
) else (
    echo SUCCESS: DJ_電線電纜 downloaded
)

REM [62/66] DJ_電腦板卡
echo Downloading DJ_電腦板卡...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_電腦板卡
if errorlevel 1 (
    echo ERROR: Failed to download DJ_電腦板卡
    pause
) else (
    echo SUCCESS: DJ_電腦板卡 downloaded
)

REM [63/66] DJ_面板設備
echo Downloading DJ_面板設備...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_面板設備
if errorlevel 1 (
    echo ERROR: Failed to download DJ_面板設備
    pause
) else (
    echo SUCCESS: DJ_面板設備 downloaded
)

REM [64/66] DJ_類比IC
echo Downloading DJ_類比IC...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_類比IC
if errorlevel 1 (
    echo ERROR: Failed to download DJ_類比IC
    pause
) else (
    echo SUCCESS: DJ_類比IC downloaded
)

REM [65/66] DJ_飛機零組件
echo Downloading DJ_飛機零組件...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_飛機零組件
if errorlevel 1 (
    echo ERROR: Failed to download DJ_飛機零組件
    pause
) else (
    echo SUCCESS: DJ_飛機零組件 downloaded
)

REM [66/66] DJ_高爾夫球
echo Downloading DJ_高爾夫球...
python GetSectorData.py --start 202501 --end 202506 --sector DJ_高爾夫球
if errorlevel 1 (
    echo ERROR: Failed to download DJ_高爾夫球
    pause
) else (
    echo SUCCESS: DJ_高爾夫球 downloaded
)

echo All downloads completed!
pause
