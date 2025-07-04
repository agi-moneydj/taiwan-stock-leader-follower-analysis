#!/usr/bin/env python3
"""
CSV-Based Leader-Follower Analysis Tool
Based on enhanced_leader_follower_analyzer.py but reads from csv directory data.
Analyzes leader-follower relationships in stock data based on institutional order flow.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.offline import plot
from datetime import datetime, timedelta
import warnings
import os
import json
import glob
from pathlib import Path
import argparse
warnings.filterwarnings('ignore')

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 確保中文字體可用
import matplotlib.font_manager as fm
available_fonts = [f.name for f in fm.fontManager.ttflist]
if 'SimHei' in available_fonts:
    plt.rcParams['font.sans-serif'] = ['SimHei']
elif 'Arial Unicode MS' in available_fonts:
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else:
    # 使用系統默認字體，但圖表標題用英文
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

class CsvBasedLeaderFollowerAnalyzer:
    def __init__(self, start_period, end_period, sector, base_dir=None):
        """Initialize analyzer with parameters for reading CSV data."""
        self.start_period = start_period  # YYYYMM format
        self.end_period = end_period      # YYYYMM format
        self.sector = sector              # DJ_IC基板 format
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.csv_dir = self.base_dir / "csv"
        self.sector_info_dir = self.base_dir / "sectorInfo"
        self.output_dir = self.base_dir / "output" / sector.replace("DJ_", "")
        
        self.sector_stocks = []
        self.data = None
        self.stocks = []
        self.results = {}
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {self.output_dir}")
        
    def load_sector_stocks(self):
        """Load stock list from sector info file."""
        sector_file = self.sector_info_dir / f"{self.sector}.txt"
        if not sector_file.exists():
            raise FileNotFoundError(f"Sector file not found: {sector_file}")
        
        with open(sector_file, 'r', encoding='big5') as f:
            stocks = [line.strip() for line in f if line.strip()]
        
        # Remove .TW suffix and filter out empty lines
        self.sector_stocks = [stock.replace('.TW', '') for stock in stocks if stock]
        print(f"Loaded {len(self.sector_stocks)} stocks for sector {self.sector}: {self.sector_stocks}")
        
        return self.sector_stocks
    
    def generate_date_range(self):
        """Generate list of trading dates in the specified period range."""
        start_year = int(self.start_period[:4])
        start_month = int(self.start_period[4:])
        end_year = int(self.end_period[:4])
        end_month = int(self.end_period[4:])
        
        dates = []
        current_year = start_year
        current_month = start_month
        
        while current_year < end_year or (current_year == end_year and current_month <= end_month):
            # Find all csv files for this month
            for stock in self.sector_stocks:
                stock_dir = self.csv_dir / stock
                if stock_dir.exists():
                    pattern = f"*{current_year:04d}{current_month:02d}*.csv"
                    files = list(stock_dir.glob(pattern))
                    for file in files:
                        # Extract date from filename
                        date_str = file.stem.split('_')[-1]  # Gets date part
                        if date_str.isdigit() and len(date_str) == 8:
                            if date_str not in dates:
                                dates.append(date_str)
            
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        dates.sort()
        print(f"Found {len(dates)} trading dates in range {self.start_period}-{self.end_period}")
        return dates
    
    def load_data(self):
        """Load and preprocess the CSV data from csv directory."""
        print("載入CSV目錄數據...")
        
        # First load sector stocks
        self.load_sector_stocks()
        
        # Generate date range
        dates = self.generate_date_range()
        
        if not dates:
            print("No data found for the specified period and sector.")
            return None
        
        all_data = []
        
        for date in dates:
            print(f"Processing date: {date}")
            
            for stock in self.sector_stocks:
                stock_dir = self.csv_dir / stock
                if not stock_dir.exists():
                    continue
                
                # Look for CSV files containing this date
                pattern = f"*{date}*.csv"
                csv_files = list(stock_dir.glob(pattern))
                
                for csv_file in csv_files:
                    try:
                        # Read CSV file
                        df = pd.read_csv(csv_file)
                        
                        # Check if the DataFrame has the expected columns
                        if 'symbol' in df.columns:
                            # This is already in the correct format
                            stock_data = df.copy()
                        else:
                            # Skip if no recognizable format
                            continue
                        
                        # Standardize column names to match enhanced_leader_follower_analyzer format
                        column_mapping = {
                            'close': 'close_price',
                            'medium_buy': 'med_buy',
                            'medium_sell': 'med_sell',
                            'medium_buy_cum': 'med_buy_cum',
                            'medium_sell_cum': 'med_sell_cum'
                        }
                        
                        stock_data = stock_data.rename(columns=column_mapping)
                        
                        # Ensure all required columns exist
                        required_columns = [
                            'symbol', 'date', 'time', 'close_price', 'volume', 'volume_ratio', 
                            'price_change_pct', 'med_buy', 'large_buy', 'xlarge_buy',
                            'med_sell', 'large_sell', 'xlarge_sell', 'med_buy_cum', 
                            'large_buy_cum', 'xlarge_buy_cum', 'med_sell_cum', 
                            'large_sell_cum', 'xlarge_sell_cum'
                        ]
                        
                        for col in required_columns:
                            if col not in stock_data.columns:
                                stock_data[col] = 0.0
                        
                        # Select only required columns
                        stock_data = stock_data[required_columns]
                        
                        all_data.append(stock_data)
                        
                    except Exception as e:
                        print(f"Error reading {csv_file}: {e}")
                        continue
        
        if not all_data:
            print("No valid data found.")
            return None
        
        # Combine all data
        self.data = pd.concat(all_data, ignore_index=True)
        print(f"載入 {len(self.data):,} 筆記錄，共 {self.data.shape[1]} 個欄位")
        
        # Process datetime
        if 'datetime' not in self.data.columns:
            # Handle time format - might be integer or string
            self.data['time'] = self.data['time'].astype(str)
            # Ensure time is 6 digits
            self.data['time'] = self.data['time'].str.zfill(6)
            time_formatted = self.data['time'].str[:2] + ':' + self.data['time'].str[2:4] + ':' + self.data['time'].str[4:6]
            
            # Combine date and time
            datetime_str = self.data['date'].astype(str) + ' ' + time_formatted
            self.data['datetime'] = pd.to_datetime(datetime_str, format='%Y/%m/%d %H:%M:%S')
        else:
            self.data['datetime'] = pd.to_datetime(self.data['datetime'])
        
        # Filter to trading hours: 09:01:00 - 13:30:00
        self.data['hour'] = self.data['datetime'].dt.hour
        self.data['minute'] = self.data['datetime'].dt.minute
        
        # Keep only trading hours (09:01 to 13:30)
        trading_mask = (
            ((self.data['hour'] == 9) & (self.data['minute'] >= 1)) |
            ((self.data['hour'] >= 10) & (self.data['hour'] <= 12)) |
            ((self.data['hour'] == 13) & (self.data['minute'] <= 30))
        )
        
        self.data = self.data[trading_mask].reset_index(drop=True)
        print(f"過濾至交易時段 (09:01-13:30): {len(self.data):,} 筆記錄")
        
        # Calculate net institutional flow (大單+特大單)
        self.data['large_net'] = (self.data['large_buy'] + self.data['xlarge_buy']) - \
                                (self.data['large_sell'] + self.data['xlarge_sell'])
        
        # Calculate total large order amount
        self.data['large_total'] = self.data['large_buy'] + self.data['xlarge_buy']
        
        # Sort by datetime
        self.data = self.data.sort_values(['symbol', 'datetime']).reset_index(drop=True)
        
        # Get unique stocks
        self.stocks = sorted(self.data['symbol'].unique())
        print(f"分析股票: {len(self.stocks)} 檔：{[s.replace('.TW', '') for s in self.stocks]}")
        
        return self.data
    
    def calculate_price_movements(self):
        """Calculate price movements and momentum indicators."""
        print("計算價格動向指標...")
        
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol].copy()
            
            # Calculate returns
            stock_data['return_1min'] = stock_data['close_price'].pct_change()
            stock_data['return_5min'] = stock_data['close_price'].pct_change(5)
            
            # Calculate rolling highs/lows
            stock_data['daily_high'] = stock_data.groupby(stock_data['datetime'].dt.date)['close_price'].transform('max')
            stock_data['daily_low'] = stock_data.groupby(stock_data['datetime'].dt.date)['close_price'].transform('min')
            
            # Rolling max for 30 minutes (approximate)
            stock_data['rolling_max_30min'] = stock_data['close_price'].rolling(window=30, min_periods=1).max()
            
            # New high/low flags
            stock_data['is_daily_high'] = stock_data['close_price'] >= stock_data['daily_high']
            stock_data['is_daily_low'] = stock_data['close_price'] <= stock_data['daily_low']
            stock_data['is_30min_high'] = stock_data['close_price'] >= stock_data['rolling_max_30min']
            
            # Calculate moving averages for signal strength
            stock_data['large_total_ma30'] = stock_data['large_total'].rolling(window=30, min_periods=1).mean()
            
            # Update main dataframe
            self.data.loc[self.data['symbol'] == symbol, stock_data.columns] = stock_data
    
    def identify_leader_signals(self, money_multiplier=2.0, min_amount=1000000, min_price_change=0.01):
        """識別領漲信號 - 改良版本"""
        print(f"識別領漲信號...")
        print(f"條件: 大單金額 > {min_amount:,}, 資金倍數 > {money_multiplier}x, 價格變化 > {min_price_change*100}%")
        
        # Enhanced signal detection
        self.data['leader_signal'] = (
            # 資金條件: 大單總額超過歷史平均的倍數
            (self.data['large_total'] > self.data['large_total_ma30'] * money_multiplier) & 
            (self.data['large_total'] > min_amount) &
            # 淨流入為正
            (self.data['large_net'] > 0) &
            # 價格上漲
            (self.data['return_1min'] > min_price_change) &
            # 創新高（日內或30分鐘）
            (self.data['is_daily_high'] | self.data['is_30min_high'])
        )
        
        # Enhanced signals with stricter conditions
        self.data['enhanced_leader_signal'] = (
            self.data['leader_signal'] & 
            (self.data['large_total'] > self.data['large_total_ma30'] * money_multiplier * 1.5) &
            (self.data['is_daily_high'])
        )
        
        # Print signal summary
        total_signals = 0
        total_enhanced = 0
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol]
            signals = stock_data['leader_signal'].sum()
            enhanced = stock_data['enhanced_leader_signal'].sum()
            total_signals += signals
            total_enhanced += enhanced
            print(f"{symbol.replace('.TW', '')}: 領漲信號={signals}, 強化信號={enhanced}")
        
        print(f"\n總計: 領漲信號={total_signals}, 強化信號={total_enhanced}")
        
        # Store signals for analysis
        self.results['leader_signals'] = self.data[self.data['leader_signal']].copy()
        return total_signals
    
    def analyze_leader_follower_relationships(self, max_lag_minutes=30, min_gain=0.5):
        """分析領漲跟漲關係 - 核心算法"""
        print("分析領漲跟漲關係...")
        
        leader_follower_pairs = []
        
        # Get all leader signals
        leader_signals = self.data[self.data['leader_signal']].copy()
        print(f"分析 {len(leader_signals)} 個領漲信號...")
        
        for idx, signal in leader_signals.iterrows():
            signal_time = signal['datetime']
            leader_symbol = signal['symbol']
            leader_price = signal['close_price']
            
            # Define time window for followers
            window_start = signal_time
            window_end = signal_time + timedelta(minutes=max_lag_minutes)
            
            # Check each other stock for following behavior
            for follower_symbol in self.stocks:
                if follower_symbol == leader_symbol:
                    continue
                
                # Get follower's base price at signal time
                follower_base_data = self.data[
                    (self.data['symbol'] == follower_symbol) & 
                    (self.data['datetime'] <= signal_time)
                ]
                
                if follower_base_data.empty:
                    continue
                
                base_price = follower_base_data.iloc[-1]['close_price']
                
                # Check follower's response in time window
                follower_window_data = self.data[
                    (self.data['symbol'] == follower_symbol) & 
                    (self.data['datetime'] > window_start) & 
                    (self.data['datetime'] <= window_end)
                ].copy()
                
                if follower_window_data.empty:
                    continue
                
                # Calculate returns and find first significant gain
                follower_window_data['gain_pct'] = (
                    (follower_window_data['close_price'] - base_price) / base_price * 100
                )
                
                # Find first time gain exceeds threshold
                significant_gains = follower_window_data[follower_window_data['gain_pct'] >= min_gain]
                
                if not significant_gains.empty:
                    first_gain = significant_gains.iloc[0]
                    time_lag = (first_gain['datetime'] - signal_time).total_seconds() / 60
                    
                    # Record the pair
                    pair = {
                        'leader_symbol': leader_symbol,
                        'follower_symbol': follower_symbol,
                        'leader_time': signal_time,
                        'follower_time': first_gain['datetime'],
                        'time_lag_minutes': time_lag,
                        'leader_close': leader_price,
                        'leader_large_total': signal['large_total'],
                        'leader_large_net': signal['large_net'],
                        'leader_return_1min': signal['return_1min'] * 100,
                        'follower_base_price': base_price,
                        'follower_trigger_price': first_gain['close_price'],
                        'follower_gain_pct': first_gain['gain_pct'],
                        'is_enhanced_signal': signal['enhanced_leader_signal']
                    }
                    leader_follower_pairs.append(pair)
        
        print(f"發現 {len(leader_follower_pairs)} 個領漲-跟漲配對")
        
        # Convert to DataFrame for analysis
        if leader_follower_pairs:
            pairs_df = pd.DataFrame(leader_follower_pairs)
            self.results['leader_follower_pairs'] = pairs_df
            return pairs_df
        else:
            print("未發現明顯的領漲跟漲關係")
            return pd.DataFrame()
    
    def calculate_success_rates(self, pairs_df):
        """計算成功率統計"""
        print("計算成功率統計...")
        
        if pairs_df.empty:
            return {}
        
        # Overall statistics
        stats = {
            'total_pairs': len(pairs_df),
            'average_time_lag': pairs_df['time_lag_minutes'].mean(),
            'median_time_lag': pairs_df['time_lag_minutes'].median(),
            'average_follower_gain': pairs_df['follower_gain_pct'].mean(),
            'max_follower_gain': pairs_df['follower_gain_pct'].max()
        }
        
        # Leader ranking by frequency and success
        leader_stats = pairs_df.groupby('leader_symbol').agg({
            'follower_symbol': 'count',
            'time_lag_minutes': 'mean',
            'follower_gain_pct': 'mean',
            'leader_large_total': 'mean'
        }).round(2)
        leader_stats.columns = ['跟漲次數', '平均時間差', '平均跟漲幅度', '平均大單金額']
        leader_stats = leader_stats.sort_values('跟漲次數', ascending=False)
        
        # Follower ranking
        follower_stats = pairs_df.groupby('follower_symbol').agg({
            'leader_symbol': 'count',
            'time_lag_minutes': 'mean',
            'follower_gain_pct': 'mean'
        }).round(2)
        follower_stats.columns = ['跟隨次數', '平均反應時間', '平均漲幅']
        follower_stats = follower_stats.sort_values('跟隨次數', ascending=False)
        
        # Best pairs
        pair_stats = pairs_df.groupby(['leader_symbol', 'follower_symbol']).agg({
            'time_lag_minutes': ['count', 'mean'],
            'follower_gain_pct': 'mean'
        }).round(2)
        pair_stats.columns = ['配對次數', '平均時間差', '平均漲幅']
        pair_stats = pair_stats.sort_values('配對次數', ascending=False)
        
        stats.update({
            'leader_ranking': leader_stats,
            'follower_ranking': follower_stats,
            'best_pairs': pair_stats
        })
        
        self.results['statistics'] = stats
        return stats
    
    def generate_comprehensive_report(self, pairs_df, stats):
        """生成綜合分析報告"""
        print("生成綜合分析報告...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("領漲跟漲分析報告")
        report_lines.append("=" * 80)
        report_lines.append(f"分析期間: {self.start_period} - {self.end_period}")
        report_lines.append(f"分析類股: {self.sector}")
        report_lines.append("")
        
        # 基本統計
        if stats:
            report_lines.append("📊 基本統計")
            report_lines.append("-" * 40)
            report_lines.append(f"總配對數: {stats['total_pairs']}")
            report_lines.append(f"平均時間差: {stats['average_time_lag']:.2f} 分鐘")
            report_lines.append(f"中位數時間差: {stats['median_time_lag']:.2f} 分鐘")
            report_lines.append(f"平均跟漲幅度: {stats['average_follower_gain']:.2f}%")
            report_lines.append(f"最大跟漲幅度: {stats['max_follower_gain']:.2f}%")
            report_lines.append("")
        
        # 領漲股排行
        if 'leader_ranking' in stats:
            report_lines.append("👑 領漲股排行榜 (TOP 5)")
            report_lines.append("-" * 40)
            for i, (symbol, data) in enumerate(stats['leader_ranking'].head().iterrows()):
                stock_name = symbol.replace('.TW', '')
                report_lines.append(f"{i+1}. {stock_name}")
                report_lines.append(f"   觸發跟漲: {data['跟漲次數']} 次")
                report_lines.append(f"   平均時間差: {data['平均時間差']:.1f} 分鐘")
                report_lines.append(f"   平均跟漲幅度: {data['平均跟漲幅度']:.2f}%")
                report_lines.append(f"   平均大單金額: {data['平均大單金額']/1000000:.1f} 百萬")
                report_lines.append("")
        
        # 跟漲股排行
        if 'follower_ranking' in stats:
            report_lines.append("🎯 跟漲股排行榜 (TOP 5)")
            report_lines.append("-" * 40)
            for i, (symbol, data) in enumerate(stats['follower_ranking'].head().iterrows()):
                stock_name = symbol.replace('.TW', '')
                report_lines.append(f"{i+1}. {stock_name}")
                report_lines.append(f"   跟隨次數: {data['跟隨次數']} 次")
                report_lines.append(f"   平均反應時間: {data['平均反應時間']:.1f} 分鐘")
                report_lines.append(f"   平均漲幅: {data['平均漲幅']:.2f}%")
                report_lines.append("")
        
        # 最佳配對
        if 'best_pairs' in stats:
            report_lines.append("⭐ 最佳領漲跟漲配對 (TOP 5)")
            report_lines.append("-" * 40)
            for i, ((leader, follower), data) in enumerate(stats['best_pairs'].head().iterrows()):
                leader_name = leader.replace('.TW', '')
                follower_name = follower.replace('.TW', '')
                report_lines.append(f"{i+1}. {leader_name} → {follower_name}")
                report_lines.append(f"   配對次數: {data['配對次數']} 次")
                report_lines.append(f"   平均時間差: {data['平均時間差']:.1f} 分鐘")
                report_lines.append(f"   平均漲幅: {data['平均漲幅']:.2f}%")
                report_lines.append("")
        
        # 實戰建議
        report_lines.append("💡 實戰操作建議")
        report_lines.append("-" * 40)
        
        if not pairs_df.empty:
            best_leader = stats['leader_ranking'].index[0].replace('.TW', '')
            best_time_lag = stats['average_time_lag']
            
            report_lines.append(f"1. 重點監控領漲股: {best_leader}")
            report_lines.append(f"2. 當{best_leader}出現大單買進且急漲時，立即關注跟漲股")
            report_lines.append(f"3. 預期跟漲反應時間: {best_time_lag:.0f} 分鐘內")
            report_lines.append(f"4. 建議停利設定: 1.5-2.5%")
            report_lines.append(f"5. 建議停損設定: -1%")
            report_lines.append(f"6. 操作時間窗口: 信號後 {int(best_time_lag*2)} 分鐘內")
        else:
            report_lines.append("1. 當前數據未發現明顯領漲跟漲關係")
            report_lines.append("2. 建議降低信號門檻重新分析")
            report_lines.append("3. 或增加更多歷史數據進行分析")
        
        report_lines.append("")
        report_lines.append("⚠️  風險提醒: 此分析僅基於歷史數據，實際操作請謹慎評估風險")
        
        report_text = '\n'.join(report_lines)
        
        # Save report to output directory
        report_file = self.output_dir / 'leader_follower_analysis_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"詳細報告已保存至: {report_file}")
        return report_text
    
    def create_visualizations(self, pairs_df, stats):
        """創建視覺化圖表"""
        print("創建視覺化圖表...")
        
        if pairs_df.empty:
            print("無數據可視覺化")
            return
        
        # Create a 2x2 subplot
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Leader-Follower Analysis Results', fontsize=16, fontweight='bold')
        
        # 1. Time Lag Distribution
        axes[0,0].hist(pairs_df['time_lag_minutes'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0,0].set_title('Time Lag Distribution')
        axes[0,0].set_xlabel('Time Lag (minutes)')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].axvline(pairs_df['time_lag_minutes'].mean(), color='red', linestyle='--', 
                         label=f'Average: {pairs_df["time_lag_minutes"].mean():.1f} min')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Leader Ranking
        if 'leader_ranking' in stats:
            leader_data = stats['leader_ranking'].head(8)
            leader_names = [s.replace('.TW', '') for s in leader_data.index]
            leader_counts = leader_data.iloc[:, 0]  # First column is count
            axes[0,1].barh(leader_names, leader_counts, color='green', alpha=0.7)
            axes[0,1].set_title('Leader Stock Ranking')
            axes[0,1].set_xlabel('Number of Follow Events Triggered')
            # Add value labels
            for i, v in enumerate(leader_counts):
                axes[0,1].text(v + 0.1, i, str(int(v)), va='center')
        
        # 3. Follower Gain Distribution
        axes[1,0].hist(pairs_df['follower_gain_pct'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[1,0].set_title('Follow Gain Distribution')
        axes[1,0].set_xlabel('Follow Gain (%)')
        axes[1,0].set_ylabel('Frequency')
        axes[1,0].axvline(pairs_df['follower_gain_pct'].mean(), color='red', linestyle='--',
                         label=f'Average: {pairs_df["follower_gain_pct"].mean():.1f}%')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. Time Lag vs Gain Scatter
        scatter = axes[1,1].scatter(pairs_df['time_lag_minutes'], pairs_df['follower_gain_pct'], 
                                   alpha=0.6, c=pairs_df['leader_large_total'], cmap='viridis')
        axes[1,1].set_title('Time Lag vs Follow Gain')
        axes[1,1].set_xlabel('Time Lag (minutes)')
        axes[1,1].set_ylabel('Follow Gain (%)')
        cbar = plt.colorbar(scatter, ax=axes[1,1])
        cbar.set_label('Leader Large Order Amount')
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_file = self.output_dir / 'leader_follower_comprehensive_analysis.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"圖表已保存至: {chart_file}")
    
    def create_multi_stock_trend_chart(self, pairs_df):
        """創建多股票走勢圖，顯示領漲跟漲關係"""
        print("創建多股票走勢圖...")
        
        if pairs_df.empty:
            print("無配對數據可繪製走勢圖")
            return
        
        # 找出最活躍的交易日
        pairs_df['trade_date'] = pairs_df['leader_time'].dt.date
        date_counts = pairs_df['trade_date'].value_counts()
        
        # 選擇配對最多的前2個交易日
        top_dates = date_counts.head(2).index
        
        for date in top_dates:
            print(f"繪製 {date} 的多股票走勢圖...")
            
            # 篩選當日數據
            date_str = date.strftime('%Y/%m/%d')
            day_data = self.data[self.data['date'] == date_str].copy()
            
            if day_data.empty:
                continue
            
            # 篩選當日的配對信號
            day_pairs = pairs_df[pairs_df['trade_date'] == date].copy()
            
            if day_pairs.empty:
                continue
            
            # 創建圖表 - 調整比例讓價格圖更大
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12), sharex=True, 
                                          gridspec_kw={'height_ratios': [4, 1]})
            
            # 定義顏色
            colors = {}
            color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for i, symbol in enumerate(self.stocks):
                colors[symbol] = color_palette[i % len(color_palette)]
            
            # 繪製價格走勢（標準化為百分比變化）
            for symbol in self.stocks:
                stock_data = day_data[day_data['symbol'] == symbol].copy()
                if stock_data.empty:
                    continue
                
                stock_data = stock_data.sort_values('datetime')
                
                # 計算當日價格變化百分比
                if len(stock_data) > 0:
                    first_price = stock_data['close_price'].iloc[0]
                    stock_data['price_change_pct'] = ((stock_data['close_price'] - first_price) / first_price) * 100
                    
                    # 繪製價格線
                    stock_name = symbol.replace('.TW', '')
                    ax1.plot(stock_data['datetime'], stock_data['price_change_pct'], 
                           color=colors[symbol], linewidth=2.5, label=f'{stock_name}', alpha=0.8)
            
            # 創建信號說明表
            signal_table = []
            signal_counter = 1
            
            # 標記領漲信號 - 使用編號系統
            for _, pair in day_pairs.iterrows():
                leader_symbol = pair['leader_symbol']
                leader_time = pair['leader_time']
                follower_symbol = pair['follower_symbol']
                follower_time = pair['follower_time']
                
                # 標記領漲點
                leader_data = day_data[
                    (day_data['symbol'] == leader_symbol) & 
                    (day_data['datetime'] == leader_time)
                ]
                if not leader_data.empty:
                    leader_price = leader_data.iloc[0]['close_price']
                    first_price = day_data[day_data['symbol'] == leader_symbol]['close_price'].iloc[0]
                    leader_change = ((leader_price - first_price) / first_price) * 100
                    
                    ax1.scatter(leader_time, leader_change, 
                              color=colors[leader_symbol], s=200, marker='^', 
                              zorder=10, edgecolors='white', linewidth=2)
                    
                    # 添加簡潔的編號標註
                    ax1.annotate(f'L{signal_counter}', 
                               xy=(leader_time, leader_change),
                               xytext=(8, 8), textcoords='offset points',
                               fontsize=10, color='black', weight='bold',
                               bbox=dict(boxstyle='circle,pad=0.2', facecolor='white', alpha=0.8))
                
                # 標記跟漲點
                follower_data = day_data[
                    (day_data['symbol'] == follower_symbol) & 
                    (day_data['datetime'] == follower_time)
                ]
                if not follower_data.empty:
                    follower_price = follower_data.iloc[0]['close_price']
                    first_price = day_data[day_data['symbol'] == follower_symbol]['close_price'].iloc[0]
                    follower_change = ((follower_price - first_price) / first_price) * 100
                    
                    ax1.scatter(follower_time, follower_change, 
                              color=colors[follower_symbol], s=150, marker='o', 
                              zorder=9, edgecolors='white', linewidth=2)
                    
                    # 添加簡潔的編號標註
                    ax1.annotate(f'F{signal_counter}', 
                               xy=(follower_time, follower_change),
                               xytext=(-8, -8), textcoords='offset points',
                               fontsize=10, color='black', weight='bold',
                               bbox=dict(boxstyle='circle,pad=0.2', facecolor='white', alpha=0.8))
                    
                    # 連接線顯示領漲→跟漲關係
                    ax1.plot([leader_time, follower_time], [leader_change, follower_change], 
                           '--', color='gray', alpha=0.5, linewidth=1)
                    
                    # 記錄到說明表
                    time_lag = pair['time_lag_minutes']
                    signal_table.append({
                        'No': signal_counter,
                        'Leader': leader_symbol.replace('.TW', ''),
                        'Lead_Time': leader_time.strftime('%H:%M'),
                        'Follower': follower_symbol.replace('.TW', ''),
                        'Follow_Time': follower_time.strftime('%H:%M'),
                        'Time_Lag': f'{time_lag:.0f}min',
                        'Follow_Gain': f'{pair["follower_gain_pct"]:.2f}%'
                    })
                    
                    signal_counter += 1
            
            # 設置上圖
            ax1.set_ylabel('Price Change (%)', fontsize=12, weight='bold')
            ax1.set_title(f'Multi-Stock Leader-Follower Analysis - {date}\n(1-minute Chart with Lead-Follow Signals)', 
                         fontsize=14, weight='bold')
            ax1.legend(loc='upper left', fontsize=11)
            ax1.grid(True, alpha=0.3)
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            # 繪製成交量（下圖）
            for symbol in self.stocks:
                stock_data = day_data[day_data['symbol'] == symbol].copy()
                if stock_data.empty:
                    continue
                
                stock_data = stock_data.sort_values('datetime')
                stock_name = symbol.replace('.TW', '')
                
                # 成交量柱狀圖
                ax2.bar(stock_data['datetime'], stock_data['volume'], 
                       color=colors[symbol], alpha=0.6, width=pd.Timedelta(minutes=0.8),
                       label=f'{stock_name} Vol')
            
            # 設置下圖
            ax2.set_ylabel('Volume', fontsize=12, weight='bold')
            ax2.set_xlabel('Time', fontsize=12, weight='bold')
            ax2.set_title('Trading Volume', fontsize=12, weight='bold')
            ax2.legend(loc='upper right', fontsize=10, ncol=len(self.stocks))
            ax2.grid(True, alpha=0.3)
            
            # 格式化時間軸
            from matplotlib.dates import DateFormatter, HourLocator
            ax1.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            ax1.xaxis.set_major_locator(HourLocator(interval=1))
            ax2.xaxis.set_major_locator(HourLocator(interval=1))
            
            plt.xticks(rotation=45)
            
            # 在圖下方添加信號說明表
            if signal_table:
                # 調整布局為圖表留出更多空間
                plt.tight_layout()
                
                # 創建說明文字
                legend_text = "Signal Legend: L1,L2... = Leader Signals (▲), F1,F2... = Follower Signals (●)"
                plt.figtext(0.5, 0.02, legend_text, ha='center', fontsize=11, weight='bold')
                
                # 保存信號說明表為CSV
                safe_date = date.strftime('%Y%m%d')
                signal_df = pd.DataFrame(signal_table)
                signal_filename = self.output_dir / f'signal_table_{safe_date}.csv'
                signal_df.to_csv(signal_filename, index=False, encoding='utf-8-sig')
                print(f"信號說明表已保存: {signal_filename}")
            else:
                plt.tight_layout()
            
            # 保存圖表
            safe_date = date.strftime('%Y%m%d')
            filename = self.output_dir / f'multi_stock_trend_{safe_date}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"多股票走勢圖已保存: {filename}")
        
        return True
    
    def create_interactive_multi_stock_chart(self, pairs_df):
        """創建互動式多股票走勢圖，支持mouse hover顯示詳細信息"""
        print("創建互動式多股票走勢圖...")
        
        if pairs_df.empty:
            print("無配對數據可繪製互動圖表")
            return
        
        # 找出最活躍的交易日
        pairs_df['trade_date'] = pairs_df['leader_time'].dt.date
        date_counts = pairs_df['trade_date'].value_counts()
        
        # 選擇配對最多的前2個交易日
        top_dates = date_counts.head(2).index
        
        for date in top_dates:
            print(f"繪製 {date} 的互動式多股票走勢圖...")
            
            # 篩選當日數據
            date_str = date.strftime('%Y/%m/%d')
            day_data = self.data[self.data['date'] == date_str].copy()
            
            if day_data.empty:
                continue
            
            # 篩選當日的配對信號
            day_pairs = pairs_df[pairs_df['trade_date'] == date].copy()
            
            if day_pairs.empty:
                continue
            
            # 創建子圖 - 價格圖 + 成交量圖
            fig = sp.make_subplots(
                rows=2, cols=1,
                row_heights=[0.8, 0.2],
                subplot_titles=('Stock Price Movements', 'Trading Volume'),
                vertical_spacing=0.1,
                shared_xaxes=True
            )
            
            # 定義顏色
            colors = {}
            color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for i, symbol in enumerate(self.stocks):
                colors[symbol] = color_palette[i % len(color_palette)]
            
            # 繪製價格走勢線
            for symbol in self.stocks:
                stock_data = day_data[day_data['symbol'] == symbol].copy()
                if stock_data.empty:
                    continue
                
                stock_data = stock_data.sort_values('datetime')
                
                # 計算當日價格變化百分比
                if len(stock_data) > 0:
                    first_price = stock_data['close_price'].iloc[0]
                    stock_data['price_change_pct'] = ((stock_data['close_price'] - first_price) / first_price) * 100
                    
                    stock_name = symbol.replace('.TW', '')
                    
                    # 價格走勢線
                    fig.add_trace(
                        go.Scatter(
                            x=stock_data['datetime'],
                            y=stock_data['price_change_pct'],
                            mode='lines',
                            name=f'{stock_name}',
                            line=dict(color=colors[symbol], width=2.5),
                            hovertemplate=f'<b>{stock_name}</b><br>' +
                                        'Time: %{x}<br>' +
                                        'Price Change: %{y:.2f}%<br>' +
                                        'Price: %{customdata[0]:.2f}<br>' +
                                        'Volume: %{customdata[1]:,.0f}<br>' +
                                        '<extra></extra>',
                            customdata=np.column_stack((
                                stock_data['close_price'],
                                stock_data['volume']
                            ))
                        ),
                        row=1, col=1
                    )
                    
                    # 成交量柱狀圖
                    fig.add_trace(
                        go.Bar(
                            x=stock_data['datetime'],
                            y=stock_data['volume'],
                            name=f'{stock_name} Vol',
                            marker_color=colors[symbol],
                            opacity=0.6,
                            showlegend=False,
                            hovertemplate=f'<b>{stock_name} Volume</b><br>' +
                                        'Time: %{x}<br>' +
                                        'Volume: %{y:,.0f}<br>' +
                                        '<extra></extra>'
                        ),
                        row=2, col=1
                    )
            
            # 添加領漲跟漲信號點
            for _, pair in day_pairs.iterrows():
                leader_symbol = pair['leader_symbol']
                leader_time = pair['leader_time']
                follower_symbol = pair['follower_symbol']
                follower_time = pair['follower_time']
                time_lag = pair['time_lag_minutes']
                follow_gain = pair['follower_gain_pct']
                
                # 領漲點
                leader_data = day_data[
                    (day_data['symbol'] == leader_symbol) & 
                    (day_data['datetime'] == leader_time)
                ]
                if not leader_data.empty:
                    leader_price = leader_data.iloc[0]['close_price']
                    first_price = day_data[day_data['symbol'] == leader_symbol]['close_price'].iloc[0]
                    leader_change = ((leader_price - first_price) / first_price) * 100
                    leader_large_total = leader_data.iloc[0]['large_total']
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[leader_time],
                            y=[leader_change],
                            mode='markers',
                            marker=dict(
                                symbol='triangle-up',
                                size=15,
                                color=colors[leader_symbol],
                                line=dict(color='white', width=2)
                            ),
                            name=f'{leader_symbol.replace(".TW", "")} Leader',
                            showlegend=False,
                            hovertemplate='<b>🔺 LEADER SIGNAL</b><br>' +
                                        f'Stock: {leader_symbol.replace(".TW", "")}<br>' +
                                        'Time: %{x}<br>' +
                                        f'Price: {leader_price:.2f}<br>' +
                                        f'Change: {leader_change:.2f}%<br>' +
                                        f'Large Orders: {leader_large_total/1000000:.1f}M<br>' +
                                        f'<b>Triggers:</b> {follower_symbol.replace(".TW", "")} in {time_lag:.0f}min<br>' +
                                        '<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # 跟漲點
                follower_data = day_data[
                    (day_data['symbol'] == follower_symbol) & 
                    (day_data['datetime'] == follower_time)
                ]
                if not follower_data.empty:
                    follower_price = follower_data.iloc[0]['close_price']
                    first_price = day_data[day_data['symbol'] == follower_symbol]['close_price'].iloc[0]
                    follower_change = ((follower_price - first_price) / first_price) * 100
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[follower_time],
                            y=[follower_change],
                            mode='markers',
                            marker=dict(
                                symbol='circle',
                                size=12,
                                color=colors[follower_symbol],
                                line=dict(color='white', width=2)
                            ),
                            name=f'{follower_symbol.replace(".TW", "")} Follower',
                            showlegend=False,
                            hovertemplate='<b>🔵 FOLLOWER SIGNAL</b><br>' +
                                        f'Stock: {follower_symbol.replace(".TW", "")}<br>' +
                                        'Time: %{x}<br>' +
                                        f'Price: {follower_price:.2f}<br>' +
                                        f'Change: {follower_change:.2f}%<br>' +
                                        f'Gain: {follow_gain:.2f}%<br>' +
                                        f'<b>Following:</b> {leader_symbol.replace(".TW", "")} after {time_lag:.0f}min<br>' +
                                        '<extra></extra>'
                        ),
                        row=1, col=1
                    )
                    
                    # 連接線
                    fig.add_trace(
                        go.Scatter(
                            x=[leader_time, follower_time],
                            y=[leader_change, follower_change],
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dash'),
                            opacity=0.5,
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=1, col=1
                    )
            
            # 更新圖表布局 - 增加互動功能
            fig.update_layout(
                title=dict(
                    text=f'Interactive Multi-Stock Leader-Follower Analysis - {date}<br>' +
                         f'<sub>Sector: {self.sector} | Period: {self.start_period}-{self.end_period}</sub><br>' +
                         '<sub>🎯 Click legend items to hide/show stocks | Hover for details | Zoom & Pan available</sub>',
                    x=0.5,
                    font=dict(size=16)
                ),
                height=800,
                showlegend=True,
                hovermode='closest',
                plot_bgcolor='white',
                paper_bgcolor='white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1
                )
            )
            
            # 更新x軸
            fig.update_xaxes(
                title_text="Time",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=2, col=1
            )
            
            # 更新y軸
            fig.update_yaxes(
                title_text="Price Change (%)",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
                row=1, col=1
            )
            
            fig.update_yaxes(
                title_text="Volume",
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                row=2, col=1
            )
            
            # 保存互動式圖表
            safe_date = date.strftime('%Y%m%d')
            interactive_filename = self.output_dir / f'interactive_multi_stock_trend_{safe_date}.html'
            fig.write_html(interactive_filename)
            
            print(f"互動式多股票走勢圖已保存: {interactive_filename}")
            print(f"  - 支援滑鼠懸停查看詳細信息")
            print(f"  - 可縮放、平移圖表")
            print(f"  - 點擊圖例可隱藏/顯示特定股票")
        
        return True
    
    def save_detailed_results(self, pairs_df):
        """保存詳細結果到CSV"""
        if not pairs_df.empty:
            # Save detailed pairs
            detailed_file = self.output_dir / 'leader_follower_pairs_detailed.csv'
            pairs_df.to_csv(detailed_file, index=False, encoding='utf-8-sig')
            
            # Create summary table
            summary_df = pairs_df[[
                'leader_symbol', 'follower_symbol', 'leader_time', 'time_lag_minutes',
                'follower_gain_pct', 'leader_large_total', 'is_enhanced_signal'
            ]].copy()
            
            summary_df['leader_symbol'] = summary_df['leader_symbol'].str.replace('.TW', '')
            summary_df['follower_symbol'] = summary_df['follower_symbol'].str.replace('.TW', '')
            summary_df['leader_time'] = summary_df['leader_time'].dt.strftime('%Y/%m/%d %H:%M')
            summary_df['leader_large_total'] = (summary_df['leader_large_total'] / 1000000).round(1)
            
            summary_df.columns = ['領漲股', '跟漲股', '信號時間', '時間差(分鐘)', '跟漲幅度(%)', '大單金額(百萬)', '強化信號']
            summary_file = self.output_dir / 'leader_follower_summary.csv'
            summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
            
            print(f"詳細結果已保存:")
            print(f"- {detailed_file} ({len(pairs_df)} 筆記錄)")
            print(f"- {summary_file} (摘要表)")
    
    def run_complete_analysis(self):
        """執行完整分析流程"""
        print("開始執行完整的領漲跟漲分析...")
        print("=" * 60)
        
        # Step 1: Load data
        if self.load_data() is None:
            print("無法載入數據，分析終止")
            return None
        
        # Step 2: Calculate indicators
        self.calculate_price_movements()
        
        # Step 3: Identify leader signals
        signal_count = self.identify_leader_signals()
        
        if signal_count == 0:
            print("⚠️  未發現符合條件的領漲信號，請調整參數後重試")
            return None
        
        # Step 4: Analyze relationships
        pairs_df = self.analyze_leader_follower_relationships()
        
        if pairs_df.empty:
            print("⚠️  未發現明顯的領漲跟漲關係")
            return None
        
        # Step 5: Calculate statistics
        stats = self.calculate_success_rates(pairs_df)
        
        # Step 6: Generate outputs
        report = self.generate_comprehensive_report(pairs_df, stats)
        self.create_visualizations(pairs_df, stats)
        self.create_multi_stock_trend_chart(pairs_df)  # 靜態多股票走勢圖
        self.create_interactive_multi_stock_chart(pairs_df)  # 互動式圖表
        self.save_detailed_results(pairs_df)
        
        # Step 7: Display summary
        print("\n" + "=" * 60)
        print("分析完成！主要發現:")
        print("=" * 60)
        if stats:
            print(f"✓ 發現 {stats['total_pairs']} 個有效的領漲跟漲配對")
            print(f"✓ 平均反應時間: {stats['average_time_lag']:.1f} 分鐘")
            print(f"✓ 平均跟漲幅度: {stats['average_follower_gain']:.2f}%")
            
            if 'leader_ranking' in stats and not stats['leader_ranking'].empty:
                best_leader = stats['leader_ranking'].index[0].replace('.TW', '')
                print(f"✓ 最佳領漲股: {best_leader}")
            
            if 'best_pairs' in stats and not stats['best_pairs'].empty:
                best_pair = stats['best_pairs'].index[0]
                leader_name = best_pair[0].replace('.TW', '')
                follower_name = best_pair[1].replace('.TW', '')
                print(f"✓ 最佳配對: {leader_name} → {follower_name}")
        
        print(f"\n📁 輸出檔案 (位於 {self.output_dir}):")
        print(f"  - leader_follower_analysis_report.txt (詳細報告)")
        print(f"  - leader_follower_comprehensive_analysis.png (統計圖表)")
        print(f"  - multi_stock_trend_YYYYMMDD.png (靜態多股票走勢圖)")
        print(f"  - interactive_multi_stock_trend_YYYYMMDD.html (🌟互動式圖表)")
        print(f"  - signal_table_YYYYMMDD.csv (信號編號說明表)")
        print(f"  - leader_follower_pairs_detailed.csv (詳細數據)")
        print(f"  - leader_follower_summary.csv (摘要表)")
        
        return {
            'pairs_df': pairs_df,
            'statistics': stats,
            'report': report
        }

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='CSV-Based Leader-Follower Analysis Tool')
    parser.add_argument('--start', required=True, help='Start period (YYYYMM format, e.g., 202605)')
    parser.add_argument('--end', required=True, help='End period (YYYYMM format, e.g., 202606)')
    parser.add_argument('--sector', required=True, help='Sector name (e.g., DJ_IC基板)')
    parser.add_argument('--base-dir', help='Base directory path (default: current directory)')
    
    args = parser.parse_args()
    
    # Initialize and run analysis
    analyzer = CsvBasedLeaderFollowerAnalyzer(
        start_period=args.start,
        end_period=args.end,
        sector=args.sector,
        base_dir=args.base_dir
    )
    
    results = analyzer.run_complete_analysis()
    
    if results:
        print("\n🎉 分析成功完成！")
    else:
        print("\n❌ 分析未能找到有效結果，請檢查數據或調整參數")

if __name__ == "__main__":
    main()