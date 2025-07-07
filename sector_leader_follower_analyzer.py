#!/usr/bin/env python3
"""
Sector Leader-Follower Analysis Tool
Reads from SectorAnalyzer's output CSV file and applies the enhanced leader-follower analysis.
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

class SectorLeaderFollowerAnalyzer:
    def __init__(self, csv_file):
        """Initialize analyzer with CSV data file from SectorAnalyzer."""
        self.csv_file = csv_file
        self.data = None
        self.stocks = []
        self.results = {}
        
        # Determine output directory from input file
        csv_path = Path(csv_file)
        self.output_dir = csv_path.parent
        print(f"Output directory: {self.output_dir}")
        
    def load_data(self):
        """Load and preprocess the CSV data from SectorAnalyzer."""
        print("載入SectorAnalyzer輸出的CSV數據...")
        
        # Load the CSV file from SectorAnalyzer
        self.data = pd.read_csv(self.csv_file)
        print(f"載入 {len(self.data):,} 筆記錄，共 {self.data.shape[1]} 個欄位")
        
        # Standardize column names to match enhanced_leader_follower_analyzer format
        column_mapping = {
            'close': 'close_price',
            'medium_buy': 'med_buy',
            'medium_sell': 'med_sell',
            'medium_buy_cum': 'med_buy_cum',
            'medium_sell_cum': 'med_sell_cum'
        }
        
        self.data = self.data.rename(columns=column_mapping)
        
        # Ensure all required columns exist
        required_columns = [
            'symbol', 'date', 'time', 'close_price', 'volume', 'volume_ratio', 
            'price_change_pct', 'med_buy', 'large_buy', 'xlarge_buy',
            'med_sell', 'large_sell', 'xlarge_sell', 'med_buy_cum', 
            'large_buy_cum', 'xlarge_buy_cum', 'med_sell_cum', 
            'large_sell_cum', 'xlarge_sell_cum'
        ]
        
        for col in required_columns:
            if col not in self.data.columns:
                self.data[col] = 0.0
        
        # Process datetime if not already processed
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
    
    def identify_leader_signals(self, money_multiplier=1.3, min_amount=5000000, min_price_change=0.003):
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
        report_lines.append(f"資料來源: {Path(self.csv_file).name}")
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
        
        if not pairs_df.empty and 'leader_ranking' in stats and not stats['leader_ranking'].empty:
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
        
        # 使用相同的股票篩選邏輯
        selected_stocks, filtered_pairs_df = self.filter_active_stocks(pairs_df)
        if len(selected_stocks) < 2:
            print("篩選後股票數量不足，無法繪製走勢圖")
            return
        
        # 找出最活躍的交易日
        filtered_pairs_df['trade_date'] = filtered_pairs_df['leader_time'].dt.date
        date_counts = filtered_pairs_df['trade_date'].value_counts()
        
        # 選擇配對最多的前2個交易日
        top_dates = date_counts.head(2).index
        
        for date in top_dates:
            print(f"繪製 {date} 的多股票走勢圖...")
            
            # 篩選當日數據
            date_str = date.strftime('%Y/%m/%d')
            day_data = self.data[self.data['date'] == date_str].copy()
            
            if day_data.empty:
                continue
            
            # 篩選當日的配對信號 (使用篩選後的數據)
            day_pairs = filtered_pairs_df[filtered_pairs_df['trade_date'] == date].copy()
            
            if day_pairs.empty:
                continue
            
            # 創建圖表 - 調整比例讓價格圖更大
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12), sharex=True, 
                                          gridspec_kw={'height_ratios': [4, 1]})
            
            # 定義顏色 (只為選中的股票分配顏色)
            colors = {}
            color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            selected_stock_codes = [s.replace('.TW', '') for s in selected_stocks]
            for i, symbol in enumerate(selected_stock_codes):
                colors[symbol] = color_palette[i % len(color_palette)]
            
            # 繪製價格走勢（標準化為百分比變化，只繪製選中的股票）
            for symbol_with_tw in selected_stocks:
                symbol = symbol_with_tw.replace('.TW', '')
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
                leader_symbol_with_tw = pair['leader_symbol']
                leader_symbol = leader_symbol_with_tw.replace('.TW', '')
                leader_time = pair['leader_time']
                follower_symbol_with_tw = pair['follower_symbol']
                follower_symbol = follower_symbol_with_tw.replace('.TW', '')
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
            
            # 繪製成交量（下圖，只繪製選中的股票）
            for symbol_with_tw in selected_stocks:
                symbol = symbol_with_tw.replace('.TW', '')
                stock_data = day_data[day_data['symbol'] == symbol].copy()
                if stock_data.empty:
                    continue
                
                stock_data = stock_data.sort_values('datetime')
                
                # 成交量柱狀圖
                ax2.bar(stock_data['datetime'], stock_data['volume'], 
                       color=colors[symbol], alpha=0.6, width=pd.Timedelta(minutes=0.8),
                       label=f'{symbol} Vol')
            
            # 設置下圖
            ax2.set_ylabel('Volume', fontsize=12, weight='bold')
            ax2.set_xlabel('Time', fontsize=12, weight='bold')
            ax2.set_title('Trading Volume', fontsize=12, weight='bold')
            ax2.legend(loc='upper right', fontsize=10, ncol=len(selected_stocks))
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
    
    def create_interactive_multi_stock_chart(self, pairs_df, selected_stocks=None):
        """創建互動式多股票走勢圖，支持mouse hover顯示詳細信息"""
        print("創建互動式多股票走勢圖...")
        
        if pairs_df.empty:
            print("無配對數據可繪製互動圖表")
            return
        
        # 如果沒有提供selected_stocks，使用篩選邏輯
        if selected_stocks is None:
            selected_stocks, filtered_pairs_df = self.filter_active_stocks(pairs_df)
        else:
            # 使用傳入的股票列表，篩選配對數據
            # 確保 selected_stocks 包含 .TW 後綴
            selected_stocks_with_tw = []
            for stock in selected_stocks:
                if stock.endswith('.TW'):
                    selected_stocks_with_tw.append(stock)
                else:
                    selected_stocks_with_tw.append(f"{stock}.TW")
            
            filtered_pairs_df = pairs_df[
                (pairs_df['leader_symbol'].isin(selected_stocks_with_tw)) & 
                (pairs_df['follower_symbol'].isin(selected_stocks_with_tw))
            ]
            selected_stocks = selected_stocks_with_tw
        
        print(f"選中股票 ({len(selected_stocks)}): {selected_stocks}")
        
        if len(selected_stocks) < 2:
            print("篩選後股票數量不足，無法繪製互動圖表")
            return
        
        # 找出最活躍的交易日
        filtered_pairs_df['trade_date'] = filtered_pairs_df['leader_time'].dt.date
        date_counts = filtered_pairs_df['trade_date'].value_counts()
        
        # 選擇配對最多的前2個交易日
        top_dates = date_counts.head(2).index
        
        for date in top_dates:
            print(f"繪製 {date} 的互動式多股票走勢圖...")
            
            # 篩選當日數據
            date_str = date.strftime('%Y/%m/%d')
            day_data = self.data[self.data['date'] == date_str].copy()
            
            print(f"  日期: {date_str}, 原始數據行數: {len(day_data)}")
            if not day_data.empty:
                print(f"  數據中的股票代號: {sorted(day_data['symbol'].unique())}")
            
            if day_data.empty:
                print(f"  {date_str} 無數據，跳過")
                continue
            
            # 篩選當日的配對信號 (使用篩選後的數據)
            day_pairs = filtered_pairs_df[filtered_pairs_df['trade_date'] == date].copy()
            
            if day_pairs.empty:
                continue
            
            # 創建子圖 - 價格圖 + 成交量圖
            fig = sp.make_subplots(
                rows=2, cols=1,
                row_heights=[0.8, 0.2],
                subplot_titles=('Stock Price Movements', 'Trading Volume'),
                vertical_spacing=0.15,  # 增加子圖間距
                shared_xaxes=True
            )
            
            # 定義顏色 (只為選中的股票分配顏色)
            colors = {}
            color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            selected_stock_codes = [s.replace('.TW', '') for s in selected_stocks]
            for i, symbol in enumerate(selected_stock_codes):
                colors[symbol] = color_palette[i % len(color_palette)]
            
            # 繪製價格走勢線 (只繪製選中的股票)
            trace_count = 0
            for symbol_with_tw in selected_stocks:
                symbol = symbol_with_tw.replace('.TW', '')
                # 數據中的symbol可能包含或不包含.TW，都嘗試匹配
                stock_data = day_data[
                    (day_data['symbol'] == symbol) | 
                    (day_data['symbol'] == symbol_with_tw)
                ].copy()
                print(f"    股票 {symbol}/{symbol_with_tw}: {len(stock_data)} 行數據")
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
                    trace_count += 1
                    
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
                    trace_count += 1
            
            # 添加領漲跟漲信號點
            for _, pair in day_pairs.iterrows():
                leader_symbol_with_tw = pair['leader_symbol']
                leader_symbol = leader_symbol_with_tw.replace('.TW', '')
                leader_time = pair['leader_time']
                follower_symbol_with_tw = pair['follower_symbol']
                follower_symbol = follower_symbol_with_tw.replace('.TW', '')
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
                            name=f'{leader_symbol} Leader',
                            showlegend=False,
                            hovertemplate='<b>🔺 LEADER SIGNAL</b><br>' +
                                        f'Stock: {leader_symbol}<br>' +
                                        'Time: %{x}<br>' +
                                        f'Price: {leader_price:.2f}<br>' +
                                        f'Change: {leader_change:.2f}%<br>' +
                                        f'Large Orders: {leader_large_total/1000000:.1f}M<br>' +
                                        f'<b>Triggers:</b> {follower_symbol} in {time_lag:.0f}min<br>' +
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
                         f'<sub>Data Source: {Path(self.csv_file).name}</sub><br>' +
                         '<sub>🎯 Click legend items to hide/show stocks | Hover for details | Zoom & Pan available</sub>',
                    x=0.5,
                    y=0.97,  # 調整主標題位置，避免與子圖標題重疊
                    font=dict(size=14)  # 稍微減小字體
                ),
                height=850,  # 增加總高度以容納標題
                showlegend=True,
                hovermode='closest',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=120, b=60, l=60, r=60),  # 增加上邊距
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
            
            print(f"  生成的圖表軌跡數量: {trace_count}")
            
            # 保存互動式圖表
            safe_date = date.strftime('%Y%m%d')
            interactive_filename = self.output_dir / f'interactive_multi_stock_trend_{safe_date}.html'
            
            if trace_count > 0:
                fig.write_html(interactive_filename)
                print(f"互動式多股票走勢圖已保存: {interactive_filename}")
                print(f"  - 支援滑鼠懸停查看詳細信息")
                print(f"  - 可縮放、平移圖表")
                print(f"  - 點擊圖例可隱藏/顯示特定股票")
            else:
                print(f"警告: 沒有生成任何圖表軌跡，跳過保存 {interactive_filename}")
        
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
    
    def filter_active_stocks(self, pairs_df, max_stocks=9):
        """篩選最活躍的股票，移除沒有跟漲行為的股票"""
        if pairs_df.empty:
            return [], pairs_df
        
        # 獲取所有股票代號
        all_stocks_raw = sorted(list(set(pairs_df['leader_symbol'].unique()) | set(pairs_df['follower_symbol'].unique())))
        
        # 保留所有參與配對的股票 (leader或follower都保留)
        active_stocks = all_stocks_raw
        
        # 如果活躍股票數量太多（>max_stocks），則篩選出最活躍的股票
        if len(active_stocks) > max_stocks:
            print(f"活躍股票數量過多 ({len(active_stocks)} 檔)，篩選最活躍的 {max_stocks} 檔股票...")
            
            # 計算每檔股票的活躍度分數 (作為leader的次數 + 作為follower的次數)
            stock_activity = {}
            for stock in active_stocks:
                leader_count = len(pairs_df[pairs_df['leader_symbol'] == stock])
                follower_count = len(pairs_df[pairs_df['follower_symbol'] == stock])
                # 加權計算：leader次數權重較高，因為更重要
                stock_activity[stock] = leader_count * 1.5 + follower_count
            
            # 選出最活躍的股票
            top_stocks = sorted(stock_activity.items(), key=lambda x: x[1], reverse=True)[:max_stocks]
            selected_stocks = [stock for stock, _ in top_stocks]
        else:
            selected_stocks = active_stocks
        
        # 篩選配對數據，只保留選中股票的配對
        pairs_df_filtered = pairs_df[
            (pairs_df['leader_symbol'].isin(selected_stocks)) & 
            (pairs_df['follower_symbol'].isin(selected_stocks))
        ]
        
        if len(selected_stocks) != len(all_stocks_raw):
            removed_stocks = [s.replace('.TW', '') for s in all_stocks_raw if s not in selected_stocks]
            print(f"移除股票: {removed_stocks} (無顯著領漲跟漲行為)")
            print(f"選中股票: {[s.replace('.TW', '') for s in selected_stocks]}")
            print(f"有效配對數量: {len(pairs_df)} → {len(pairs_df_filtered)}")
        
        return selected_stocks, pairs_df_filtered

    def create_leader_follower_relation_chart(self, pairs_df):
        """創建領漲跟漲關係圖表 (基於 pair_trade_analyzer.py 的邏輯)"""
        print("創建領漲跟漲關係圖表...")
        
        if pairs_df.empty:
            print("無配對數據可繪製關係圖表")
            return
        
        # 使用共用的股票篩選邏輯
        all_stocks, pairs_df = self.filter_active_stocks(pairs_df)
        n_stocks = len(all_stocks)
        
        if n_stocks < 2:
            print("篩選後股票數量不足，無法繪製關係圖表")
            return
        
        # 設置圖表大小 (針對篩選後的股票數量優化)
        fig_width = max(16, min(20, n_stocks * 2))
        fig_height = max(12, min(16, n_stocks * 1.5))
        
        fig, axes = plt.subplots(2, 2, figsize=(fig_width, fig_height))
        fig.suptitle('Leader-Follower Relationship Analysis', fontsize=16, fontweight='bold')
        
        # 1. 成功率矩陣 (Success Rate Matrix)
        success_matrix = np.zeros((n_stocks, n_stocks))
        
        # 計算每個配對的成功率
        # 使用更合理的成功率定義: 給定領漲跟漲配對的平均收益率作為衡量成功的指標
        for i, leader in enumerate(all_stocks):
            for j, follower in enumerate(all_stocks):
                if leader != follower:
                    pair_data = pairs_df[(pairs_df['leader_symbol'] == leader) & (pairs_df['follower_symbol'] == follower)]
                    if not pair_data.empty:
                        # 成功率定義為平均跟漲幅度的正規化值 (0-1之間)
                        avg_gain = pair_data['follower_gain_pct'].mean()
                        # 將跟漲幅度轉換為 0-1 之間的成功率 (假設 2% 以上為完全成功)
                        success_matrix[i][j] = min(avg_gain / 2.0, 1.0)
                    else:
                        success_matrix[i][j] = 0
        
        im1 = axes[0,0].imshow(success_matrix, cmap='Reds', aspect='auto')
        axes[0,0].set_xticks(range(n_stocks))
        axes[0,0].set_yticks(range(n_stocks))
        
        # 設置標籤 (針對篩選後的較少股票數量，使用更大字體)
        stock_labels = [s.replace('.TW', '') for s in all_stocks]
        font_size = max(8, min(12, 100 // n_stocks))
        
        axes[0,0].set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        axes[0,0].set_yticklabels(stock_labels, fontsize=font_size)
        axes[0,0].set_title('Success Rates\n(Leader=Y-axis, Follower=X-axis)', fontsize=12)
        plt.colorbar(im1, ax=axes[0,0])
        
        # 添加數值標註 (因為已篩選，數量不會太多)
        if n_stocks <= 12:
            for i in range(n_stocks):
                for j in range(n_stocks):
                    if success_matrix[i][j] > 0:
                        axes[0,0].text(j, i, f'{success_matrix[i][j]:.2f}', 
                                     ha='center', va='center', 
                                     color='white' if success_matrix[i][j] > 0.5 else 'black',
                                     fontsize=max(6, font_size-2))
        
        # 2. 反應時間矩陣 (Response Time Matrix)
        lag_matrix = np.zeros((n_stocks, n_stocks))
        
        for i, leader in enumerate(all_stocks):
            for j, follower in enumerate(all_stocks):
                if leader != follower:
                    pair_data = pairs_df[(pairs_df['leader_symbol'] == leader) & (pairs_df['follower_symbol'] == follower)]
                    if not pair_data.empty:
                        avg_lag = pair_data['time_lag_minutes'].mean()
                        lag_matrix[i][j] = avg_lag if avg_lag > 0 else np.nan
        
        im2 = axes[0,1].imshow(lag_matrix, cmap='Blues', aspect='auto')
        axes[0,1].set_xticks(range(n_stocks))
        axes[0,1].set_yticks(range(n_stocks))
        axes[0,1].set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        axes[0,1].set_yticklabels(stock_labels, fontsize=font_size)
        axes[0,1].set_title('Average Response Time (minutes)\n(Leader=Y-axis, Follower=X-axis)', fontsize=12)
        plt.colorbar(im2, ax=axes[0,1])
        
        # 添加時間標註 (因為已篩選，數量不會太多)
        if n_stocks <= 12:
            for i in range(n_stocks):
                for j in range(n_stocks):
                    if not np.isnan(lag_matrix[i][j]) and lag_matrix[i][j] > 0:
                        axes[0,1].text(j, i, f'{lag_matrix[i][j]:.1f}', 
                                     ha='center', va='center', 
                                     color='white' if lag_matrix[i][j] > 15 else 'black',
                                     fontsize=max(6, font_size-2))
        
        # 3. 信號分佈圖 (Signal Distribution)
        signal_counts = []
        stock_names = []
        
        for stock in all_stocks:
            leader_count = len(pairs_df[pairs_df['leader_symbol'] == stock])
            follower_count = len(pairs_df[pairs_df['follower_symbol'] == stock])
            signal_counts.extend([leader_count, follower_count])
            stock_names.extend([f'{stock.replace(".TW", "")}\nLead', f'{stock.replace(".TW", "")}\nFollow'])
        
        colors = ['darkblue', 'darkgreen'] * n_stocks
        bars = axes[1,0].bar(range(len(signal_counts)), signal_counts, color=colors, alpha=0.7)
        axes[1,0].set_xticks(range(len(signal_counts)))
        
        # 調整標籤
        label_rotation = 90 if n_stocks > 8 else 45
        axes[1,0].set_xticklabels(stock_names, rotation=label_rotation, ha='right' if label_rotation == 45 else 'center', fontsize=max(6, font_size-1))
        axes[1,0].set_title('Signal Count Distribution', fontsize=12)
        axes[1,0].set_ylabel('Number of Signals')
        
        # 添加數值標籤 (因為已篩選，數量不會太多)
        if n_stocks <= 15:
            for bar, count in zip(bars, signal_counts):
                if count > 0:
                    axes[1,0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                                 str(count), ha='center', va='bottom', fontsize=max(6, font_size-2))
        
        # 4. 平均漲幅矩陣 (Average Return Matrix)
        return_matrix = np.zeros((n_stocks, n_stocks))
        
        for i, leader in enumerate(all_stocks):
            for j, follower in enumerate(all_stocks):
                if leader != follower:
                    pair_data = pairs_df[(pairs_df['leader_symbol'] == leader) & (pairs_df['follower_symbol'] == follower)]
                    if not pair_data.empty:
                        avg_return = pair_data['follower_gain_pct'].mean()
                        return_matrix[i][j] = avg_return if avg_return > 0 else 0
        
        im3 = axes[1,1].imshow(return_matrix, cmap='Greens', aspect='auto')
        axes[1,1].set_xticks(range(n_stocks))
        axes[1,1].set_yticks(range(n_stocks))
        axes[1,1].set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        axes[1,1].set_yticklabels(stock_labels, fontsize=font_size)
        axes[1,1].set_title('Average Follow Return (%)\n(Leader=Y-axis, Follower=X-axis)', fontsize=12)
        plt.colorbar(im3, ax=axes[1,1])
        
        # 添加回報率標註 (因為已篩選，數量不會太多)
        if n_stocks <= 12:
            for i in range(n_stocks):
                for j in range(n_stocks):
                    if return_matrix[i][j] > 0:
                        axes[1,1].text(j, i, f'{return_matrix[i][j]:.1f}%', 
                                     ha='center', va='center', 
                                     color='white' if return_matrix[i][j] > 1 else 'black',
                                     fontsize=max(6, font_size-2))
        
        plt.tight_layout(pad=3.0)
        output_path = self.output_dir / 'leader_follower_analysis_relation.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"領漲跟漲關係圖表已保存: {output_path}")
        
        # 輸出關係摘要
        print("\n關係分析摘要:")
        print(f"分析股票數量: {n_stocks}")
        print(f"有效配對數量: {len(pairs_df)}")
        
        # 找出最佳配對
        best_pairs = []
        for i, leader in enumerate(all_stocks):
            for j, follower in enumerate(all_stocks):
                if leader != follower and success_matrix[i][j] > 0:
                    best_pairs.append({
                        'leader': leader.replace('.TW', ''),
                        'follower': follower.replace('.TW', ''),
                        'success_rate': success_matrix[i][j],
                        'avg_lag': lag_matrix[i][j] if not np.isnan(lag_matrix[i][j]) else 0,
                        'avg_return': return_matrix[i][j]
                    })
        
        if best_pairs:
            best_pairs.sort(key=lambda x: x['success_rate'], reverse=True)
            print(f"最佳配對 (成功率最高): {best_pairs[0]['leader']} → {best_pairs[0]['follower']} (成功率: {best_pairs[0]['success_rate']:.2f})")

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
        
        # Step 6: Generate outputs (same format as enhanced_leader_follower_analyzer)
        report = self.generate_comprehensive_report(pairs_df, stats)
        self.create_visualizations(pairs_df, stats)
        
        # 獲取篩選後的股票列表 (與關係圖表使用相同邏輯)
        selected_stocks, filtered_pairs_df = self.filter_active_stocks(pairs_df)
        
        self.create_multi_stock_trend_chart(pairs_df)  # 靜態多股票走勢圖 (內部會篩選)
        self.create_interactive_multi_stock_chart(pairs_df, selected_stocks)  # 互動式圖表 (使用相同股票列表)
        self.create_leader_follower_relation_chart(pairs_df)  # 領漲跟漲關係圖表 (內部會篩選)
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
        print(f"  - leader_follower_analysis_relation.png (🌟股票關係圖表)")
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
    parser = argparse.ArgumentParser(description='Sector Leader-Follower Analysis Tool')
    parser.add_argument('csv_file', help='SectorAnalyzer output CSV file path (e.g., output/IC基板/combined_data_debug.csv)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"錯誤: 找不到檔案 {args.csv_file}")
        print("請先運行 SectorAnalyzer 生成 CSV 資料檔案")
        return
    
    # Initialize and run analysis
    analyzer = SectorLeaderFollowerAnalyzer(args.csv_file)
    results = analyzer.run_complete_analysis()
    
    if results:
        print("\n🎉 分析成功完成！")
        print("注意：輸出格式與 enhanced_leader_follower_analyzer.py 完全相同")
    else:
        print("\n❌ 分析未能找到有效結果，請檢查數據或調整參數")

if __name__ == "__main__":
    main()