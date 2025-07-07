#!/usr/bin/env python3
"""
台灣股票資料轉換器
將原始的 Min_*.txt 和 TAMin_*.txt 檔案轉換為 CSV 格式
供 CSV-based leader follower analyzer 使用
"""

import os
import sys
import glob
import pandas as pd
import re
from datetime import datetime
import argparse

def parse_txt_file(file_path, file_type="Min"):
    """解析 TXT 檔案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None
            
        # 解析標頭
        header_line = lines[0].strip()
        if not header_line.startswith('#'):
            return None
            
        # 提取股票代號和日期
        stock_match = re.search(r'ID=([^;]+)', header_line)
        date_match = re.search(r'TDate=([^;]+)', header_line)
        
        if not stock_match or not date_match:
            return None
            
        stock_id = stock_match.group(1)
        trade_date = date_match.group(1)
        
        # 解析欄位名稱
        field_match = re.search(r'Field=([^;]+)', header_line)
        if not field_match:
            return None
            
        field_names = field_match.group(1).split(',')
        
        # 解析資料行
        data_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith('#'):
                data_lines.append(line.split(','))
        
        if not data_lines:
            return None
            
        # 建立 DataFrame
        df = pd.DataFrame(data_lines, columns=field_names)
        
        # 添加股票代號欄位
        df['symbol'] = stock_id
        
        # 轉換資料類型
        if file_type == "Min":
            # 基本價量資料
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Vol']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        elif file_type == "TAMin":
            # 技術分析資料，包含大單進出
            numeric_cols = ['AvgPrice', 'UpVolume', 'DownVolume', 'VolumeRatio',
                          'XLOrderOutVolume', 'XLOrderInVolume', 'LOrderOutVolume', 'LOrderInVolume',
                          'MOrderOutVolume', 'MOrderInVolume', 'SOrderOutVolume', 'SOrderInVolume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 合併日期時間 - 保持原始格式供分析器使用
        if 'Date' in df.columns and 'Time' in df.columns:
            df['date'] = df['Date']
            df['time'] = df['Time']
            # 不提供 datetime 欄位，讓分析器自己建構
        
        return df
        
    except Exception as e:
        print(f"解析檔案錯誤 {file_path}: {e}")
        return None

def convert_to_csv_format(min_df, ta_df, stock_id, date_str):
    """轉換為 CSV 分析器期望的格式"""
    if min_df is None or ta_df is None:
        return None
        
    try:
        # 合併 Min 和 TAMin 資料
        merged_df = pd.merge(min_df, ta_df, on=['Date', 'Time'], how='inner', suffixes=('_min', '_ta'))
        
        if merged_df.empty:
            return None
        
        # 建立分析器期望的欄位
        result_df = pd.DataFrame({
            'symbol': merged_df['symbol_min'],
            'date': merged_df['Date'],
            'time': merged_df['Time'],
            'close_price': merged_df['Close'],
            'volume': merged_df['Vol'],
            'volume_ratio': merged_df.get('VolumeRatio', 0),
            'price_change_pct': 0,  # 需要計算
            'med_buy': merged_df.get('MOrderInVolume', 0),
            'large_buy': merged_df.get('LOrderInVolume', 0),
            'xlarge_buy': merged_df.get('XLOrderInVolume', 0),
            'med_sell': merged_df.get('MOrderOutVolume', 0),
            'large_sell': merged_df.get('LOrderOutVolume', 0),
            'xlarge_sell': merged_df.get('XLOrderOutVolume', 0),
            'med_buy_cum': merged_df.get('MOrderInVolume', 0).cumsum(),
            'large_buy_cum': merged_df.get('LOrderInVolume', 0).cumsum(),
            'xlarge_buy_cum': merged_df.get('XLOrderInVolume', 0).cumsum(),
            'med_sell_cum': merged_df.get('MOrderOutVolume', 0).cumsum(),
            'large_sell_cum': merged_df.get('LOrderOutVolume', 0).cumsum(),
            'xlarge_sell_cum': merged_df.get('XLOrderOutVolume', 0).cumsum(),
        })
        
        # 計算價格變化百分比
        result_df['price_change_pct'] = result_df['close_price'].pct_change() * 100
        result_df['price_change_pct'] = result_df['price_change_pct'].fillna(0)
        
        # 確保數值欄位
        numeric_cols = ['close_price', 'volume', 'volume_ratio', 'price_change_pct',
                       'med_buy', 'large_buy', 'xlarge_buy', 'med_sell', 'large_sell', 'xlarge_sell',
                       'med_buy_cum', 'large_buy_cum', 'xlarge_buy_cum', 'med_sell_cum', 'large_sell_cum', 'xlarge_sell_cum']
        
        for col in numeric_cols:
            result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
        
        return result_df
        
    except Exception as e:
        print(f"轉換格式錯誤 {stock_id} {date_str}: {e}")
        return None

def convert_stock_data(stock_dir, output_dir):
    """轉換單一股票的所有資料"""
    stock_id = os.path.basename(stock_dir)
    print(f"轉換股票 {stock_id} 資料...")
    
    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 找出所有 Min 檔案
    min_files = glob.glob(os.path.join(stock_dir, "Min_*.txt"))
    converted_count = 0
    
    for min_file in min_files:
        # 提取日期
        filename = os.path.basename(min_file)
        date_match = re.search(r'Min_(\d{8})\.txt', filename)
        if not date_match:
            continue
            
        date_str = date_match.group(1)
        
        # 找對應的 TAMin 檔案
        ta_file = os.path.join(stock_dir, f"TAMin_{date_str}.txt")
        if not os.path.exists(ta_file):
            continue
        
        # 解析檔案
        min_df = parse_txt_file(min_file, "Min")
        ta_df = parse_txt_file(ta_file, "TAMin")
        
        if min_df is None or ta_df is None:
            continue
        
        # 轉換格式
        csv_df = convert_to_csv_format(min_df, ta_df, stock_id, date_str)
        if csv_df is None:
            continue
        
        # 輸出 CSV
        output_file = os.path.join(output_dir, f"{stock_id}_{date_str}.csv")
        csv_df.to_csv(output_file, index=False)
        converted_count += 1
    
    print(f"股票 {stock_id} 轉換完成: {converted_count} 個檔案")
    return converted_count

def main():
    parser = argparse.ArgumentParser(description='轉換台灣股票資料為CSV格式')
    parser.add_argument('--input-dir', default='csv', help='輸入目錄 (預設: csv)')
    parser.add_argument('--output-dir', default='csv_converted', help='輸出目錄 (預設: csv_converted)')
    parser.add_argument('--stocks', help='指定股票代號，以逗號分隔')
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    output_dir = args.output_dir
    
    if not os.path.exists(input_dir):
        print(f"錯誤: 輸入目錄 {input_dir} 不存在")
        return 1
    
    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 取得要轉換的股票清單
    if args.stocks:
        stock_list = args.stocks.split(',')
        stock_dirs = [os.path.join(input_dir, stock.strip()) for stock in stock_list]
        stock_dirs = [d for d in stock_dirs if os.path.exists(d)]
    else:
        stock_dirs = [d for d in glob.glob(os.path.join(input_dir, "*")) if os.path.isdir(d)]
    
    if not stock_dirs:
        print("沒有找到可轉換的股票資料")
        return 1
    
    print(f"開始轉換 {len(stock_dirs)} 個股票的資料...")
    
    total_converted = 0
    for stock_dir in stock_dirs:
        stock_id = os.path.basename(stock_dir)
        stock_output_dir = os.path.join(output_dir, stock_id)
        converted = convert_stock_data(stock_dir, stock_output_dir)
        total_converted += converted
    
    print(f"轉換完成! 總共轉換 {total_converted} 個檔案")
    return 0

if __name__ == "__main__":
    sys.exit(main())