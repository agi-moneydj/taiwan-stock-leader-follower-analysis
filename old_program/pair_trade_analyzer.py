#!/usr/bin/env python3
"""
Pair Trading Lead-Follow Analysis Tool
Analyzes leader-follower relationships in stock data based on institutional order flow.
Enhanced with industry classification and cross-industry search capabilities.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import argparse
import os
import json
import shutil
warnings.filterwarnings('ignore')

class PairTradeAnalyzer:
    def __init__(self, csv_file, industry=None, base_dir=None):
        """Initialize analyzer with CSV data file and industry classification."""
        self.csv_file = csv_file
        self.industry = industry or "default"
        self.base_dir = base_dir or "/home/agi/pairTrade"
        self.industry_dir = os.path.join(self.base_dir, self.industry)
        self.data = None
        self.stocks = []
        self.results = {}
        
        # Create industry directory if it doesn't exist
        self._create_industry_directory()
    
    def _create_industry_directory(self):
        """Create industry directory structure."""
        if not os.path.exists(self.industry_dir):
            os.makedirs(self.industry_dir)
            print(f"Created industry directory: {self.industry_dir}")
    
    def _get_output_path(self, filename):
        """Get full path for output file in industry directory."""
        return os.path.join(self.industry_dir, filename)
    
    def _update_master_index(self):
        """Update master index file with current analysis results."""
        master_index_path = os.path.join(self.base_dir, "master_index.json")
        
        # Load existing index or create new one
        if os.path.exists(master_index_path):
            with open(master_index_path, 'r', encoding='utf-8') as f:
                master_index = json.load(f)
        else:
            master_index = {"stocks": {}, "industries": {}}
        
        # Get current analysis results
        if not self.results:
            return
            
        # Update industry information
        master_index["industries"][self.industry] = {
            "stocks": [s.replace('.TW', '') for s in self.stocks],
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "data_file": os.path.basename(self.csv_file),
            "total_signals": len(self.results.get('signals', [])) if 'signals' in self.results else 0
        }
        
        # Update stock information
        correlations = self.results.get('correlations', {})
        leadership_analysis = self.results.get('leadership_analysis', {})
        
        for stock in self.stocks:
            stock_code = stock.replace('.TW', '')
            
            if stock_code not in master_index["stocks"]:
                master_index["stocks"][stock_code] = {
                    "industries": [],
                    "latest_analysis": datetime.now().strftime("%Y-%m-%d"),
                    "roles": {}
                }
            
            # Add current industry if not already present
            if self.industry not in master_index["stocks"][stock_code]["industries"]:
                master_index["stocks"][stock_code]["industries"].append(self.industry)
            
            # Update role information
            role_info = {"role": "neutral", "leaders": [], "followers": [], "success_rates": {}, "time_lags": {}}
            
            # Determine if this stock is a leader or follower
            leaders = leadership_analysis.get('leaders', [])
            followers = leadership_analysis.get('followers', [])
            
            is_leader = any(stock == leader[0] for leader in leaders[:3])  # Top 3 leaders
            is_follower = any(stock == follower[0] for follower in followers[:3])  # Top 3 followers
            
            if is_leader and is_follower:
                role_info["role"] = "both"
            elif is_leader:
                role_info["role"] = "leader"
            elif is_follower:
                role_info["role"] = "follower"
            
            # Find leaders and followers for this stock
            for leader_stock in correlations:
                if stock in correlations[leader_stock]:
                    data = correlations[leader_stock][stock]
                    if data.get('buy_success_rate', 0) >= 0.5:  # 50% success rate threshold
                        leader_code = leader_stock.replace('.TW', '')
                        role_info["leaders"].append(leader_code)
                        role_info["success_rates"][leader_code] = f"{data['buy_success_rate']:.0%}"
                        role_info["time_lags"][leader_code] = f"{data.get('avg_buy_lag', 0):.0f}min"
            
            for follower_stock in correlations.get(stock, {}):
                data = correlations[stock][follower_stock]
                if data.get('buy_success_rate', 0) >= 0.5:  # 50% success rate threshold
                    follower_code = follower_stock.replace('.TW', '')
                    role_info["followers"].append(follower_code)
            
            master_index["stocks"][stock_code]["roles"][self.industry] = role_info
            master_index["stocks"][stock_code]["latest_analysis"] = datetime.now().strftime("%Y-%m-%d")
        
        # Save updated index
        with open(master_index_path, 'w', encoding='utf-8') as f:
            json.dump(master_index, f, ensure_ascii=False, indent=2)
        
        print(f"Updated master index: {master_index_path}")
        
    def load_data(self):
        """Load and preprocess the CSV data."""
        print("Loading data...")
        
        # Define column names based on CLAUDE.md - CSV actually has 19 columns
        columns = [
            'symbol', 'date', 'time', 'close_price', 'volume', 'volume_ratio', 
            'price_change_pct', 'med_buy', 'large_buy', 'xlarge_buy',
            'med_sell', 'large_sell', 'xlarge_sell', 'med_buy_cum', 
            'large_buy_cum', 'xlarge_buy_cum', 'med_sell_cum', 
            'large_sell_cum', 'xlarge_sell_cum'
        ]
        
        # Load data - there's a trailing space causing 20th empty column
        self.data = pd.read_csv(self.csv_file, sep=' ', names=columns, header=None, usecols=range(19))
        print(f"Loaded {len(self.data):,} rows with {self.data.shape[1]} columns")
        
        # Convert time to proper datetime
        # Handle integer time format (HHmmss) with proper zero-padding
        # Note: time like 110000 means 11:00:00, not 01:10:00
        self.data['time'] = self.data['time'].astype(int)
        time_str = self.data['time'].astype(str).str.zfill(6)
        time_formatted = time_str.str[:2] + ':' + time_str.str[2:4] + ':' + time_str.str[4:6]
        
        # Combine date and time strings properly
        datetime_str = self.data['date'].astype(str) + ' ' + time_formatted
        
        self.data['datetime'] = pd.to_datetime(datetime_str, format='%Y/%m/%d %H:%M:%S')
        
        # Filter to day trading hours: 09:01:00 - 12:40:00
        self.data['hour'] = self.data['datetime'].dt.hour
        self.data['minute'] = self.data['datetime'].dt.minute
        
        # Keep only trading hours (09:01 to 12:40)
        trading_mask = (
            ((self.data['hour'] == 9) & (self.data['minute'] >= 1)) |
            ((self.data['hour'] >= 10) & (self.data['hour'] <= 11)) |
            ((self.data['hour'] == 12) & (self.data['minute'] <= 40))
        )
        
        self.data = self.data[trading_mask].reset_index(drop=True)
        print(f"Filtered to trading hours (09:01-12:40): {len(self.data):,} records")
        
        # Calculate net institutional flow
        self.data['large_net'] = (self.data['large_buy'] + self.data['xlarge_buy']) - \
                                (self.data['large_sell'] + self.data['xlarge_sell'])
        
        # Calculate total large order amount
        self.data['large_total'] = self.data['large_buy'] + self.data['xlarge_buy']
        
        # Sort by datetime
        self.data = self.data.sort_values(['symbol', 'datetime']).reset_index(drop=True)
        
        # Get unique stocks
        self.stocks = sorted(self.data['symbol'].unique())
        print(f"Loaded data for {len(self.stocks)} stocks: {self.stocks}")
        
        return self.data
    
    def calculate_price_movements(self, lookback_minutes=5):
        """Calculate price movements and momentum indicators."""
        print("Calculating price movements...")
        
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol].copy()
            
            # Calculate returns
            stock_data['return_1min'] = stock_data['close_price'].pct_change()
            stock_data['return_5min'] = stock_data['close_price'].pct_change(5)
            
            # Calculate rolling highs/lows
            stock_data['daily_high'] = stock_data.groupby(stock_data['datetime'].dt.date)['close_price'].transform('max')
            stock_data['daily_low'] = stock_data.groupby(stock_data['datetime'].dt.date)['close_price'].transform('min')
            
            # 5-day and 10-day highs (approximate with available data)
            stock_data['rolling_max_5d'] = stock_data['close_price'].rolling(window=300, min_periods=1).max()  # ~5 days
            stock_data['rolling_max_10d'] = stock_data['close_price'].rolling(window=600, min_periods=1).max()  # ~10 days
            
            # New high/low flags
            stock_data['is_daily_high'] = stock_data['close_price'] >= stock_data['daily_high']
            stock_data['is_daily_low'] = stock_data['close_price'] <= stock_data['daily_low']
            stock_data['is_5d_high'] = stock_data['close_price'] >= stock_data['rolling_max_5d']
            
            # Update main dataframe
            self.data.loc[self.data['symbol'] == symbol, stock_data.columns] = stock_data
    
    def identify_signals(self, large_threshold=1000000, net_threshold=500000):
        """Identify buy/sell signals based on large order flow."""
        print(f"Identifying signals with thresholds: large_total>{large_threshold:,}, large_net>{net_threshold:,}")
        
        # Strong buy signals
        self.data['strong_buy_signal'] = (
            (self.data['large_total'] > large_threshold) & 
            (self.data['large_net'] > net_threshold) &
            (self.data['return_1min'] > 0.01)  # Price surge >1%
        )
        
        # Strong sell signals  
        self.data['strong_sell_signal'] = (
            (self.data['large_total'] > large_threshold) & 
            (self.data['large_net'] < -net_threshold) &
            (self.data['return_1min'] < -0.01)  # Price drop >1%
        )
        
        # Enhanced signals with new highs/lows
        self.data['enhanced_buy_signal'] = (
            self.data['strong_buy_signal'] & 
            (self.data['is_daily_high'] | self.data['is_5d_high'])
        )
        
        self.data['enhanced_sell_signal'] = (
            self.data['strong_sell_signal'] & 
            self.data['is_daily_low']
        )
        
        # Print signal summary
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol]
            buy_signals = stock_data['strong_buy_signal'].sum()
            sell_signals = stock_data['strong_sell_signal'].sum()
            enhanced_buy = stock_data['enhanced_buy_signal'].sum()
            enhanced_sell = stock_data['enhanced_sell_signal'].sum()
            
            print(f"{symbol}: Buy={buy_signals}, Sell={sell_signals}, Enhanced Buy={enhanced_buy}, Enhanced Sell={enhanced_sell}")
    
    def analyze_leader_follower(self, max_lag_minutes=30):
        """Analyze leader-follower relationships with time lags."""
        print("Analyzing leader-follower relationships...")
        
        correlations = {}
        
        for leader in self.stocks:
            correlations[leader] = {}
            leader_data = self.data[self.data['symbol'] == leader].set_index('datetime')
            
            # Get leader signals
            leader_buy_times = leader_data[leader_data['strong_buy_signal']].index
            leader_sell_times = leader_data[leader_data['strong_sell_signal']].index
            
            if len(leader_buy_times) == 0 and len(leader_sell_times) == 0:
                continue
                
            for follower in self.stocks:
                if leader == follower:
                    continue
                    
                follower_data = self.data[self.data['symbol'] == follower].set_index('datetime')
                
                # Analyze responses to leader signals
                buy_responses = []
                sell_responses = []
                
                # Check buy signal responses
                for signal_time in leader_buy_times:
                    # Look for responses in next 30 minutes
                    end_time = signal_time + timedelta(minutes=max_lag_minutes)
                    response_window = follower_data[
                        (follower_data.index > signal_time) & 
                        (follower_data.index <= end_time)
                    ]
                    
                    if not response_window.empty:
                        # Calculate max return in response window
                        max_return = response_window['return_1min'].cumsum().max()
                        if max_return > 0.005:  # >0.5% response
                            # Find when max return occurred  
                            max_idx = response_window['return_1min'].cumsum().idxmax()
                            lag_minutes = (max_idx - signal_time).total_seconds() / 60
                            buy_responses.append({'lag': lag_minutes, 'return': max_return})
                
                # Check sell signal responses
                for signal_time in leader_sell_times:
                    end_time = signal_time + timedelta(minutes=max_lag_minutes)
                    response_window = follower_data[
                        (follower_data.index > signal_time) & 
                        (follower_data.index <= end_time)
                    ]
                    
                    if not response_window.empty:
                        min_return = response_window['return_1min'].cumsum().min()
                        if min_return < -0.005:  # <-0.5% response
                            min_idx = response_window['return_1min'].cumsum().idxmin()
                            lag_minutes = (min_idx - signal_time).total_seconds() / 60
                            sell_responses.append({'lag': lag_minutes, 'return': abs(min_return)})
                
                # Store results
                correlations[leader][follower] = {
                    'buy_responses': buy_responses,
                    'sell_responses': sell_responses,
                    'buy_success_rate': len(buy_responses) / max(len(leader_buy_times), 1),
                    'sell_success_rate': len(sell_responses) / max(len(leader_sell_times), 1),
                    'avg_buy_lag': np.mean([r['lag'] for r in buy_responses]) if buy_responses else 0,
                    'avg_sell_lag': np.mean([r['lag'] for r in sell_responses]) if sell_responses else 0,
                    'avg_buy_return': np.mean([r['return'] for r in buy_responses]) if buy_responses else 0,
                    'avg_sell_return': np.mean([r['return'] for r in sell_responses]) if sell_responses else 0,
                }
        
        self.results['correlations'] = correlations
        return correlations
    
    def optimize_thresholds(self):
        """Find optimal thresholds for signal detection."""
        print("Optimizing thresholds...")
        
        # Test different threshold combinations (reduce for performance)
        large_thresholds = [1000000, 2000000]
        net_thresholds = [500000, 1000000]
        
        best_results = {}
        
        for large_thresh in large_thresholds:
            for net_thresh in net_thresholds:
                # Temporarily set thresholds and identify signals
                temp_data = self.data.copy()
                temp_data['temp_buy_signal'] = (
                    (temp_data['large_total'] > large_thresh) & 
                    (temp_data['large_net'] > net_thresh) &
                    (temp_data['return_1min'] > 0.01)
                )
                
                # Count successful follow-through for each stock
                success_rates = []
                for symbol in self.stocks:
                    stock_data = temp_data[temp_data['symbol'] == symbol]
                    signals = stock_data[stock_data['temp_buy_signal']]
                    
                    if len(signals) > 0:
                        # Check if next few minutes show continued momentum
                        success_count = 0
                        for idx in signals.index:
                            if idx < len(stock_data) - 5:  # Ensure we have next 5 minutes
                                next_returns = stock_data.iloc[idx+1:idx+6]['return_1min'].sum()
                                if next_returns > 0.01:  # Continued momentum
                                    success_count += 1
                        
                        success_rate = success_count / len(signals)
                        success_rates.append(success_rate)
                
                avg_success_rate = np.mean(success_rates) if success_rates else 0
                signal_count = temp_data['temp_buy_signal'].sum()
                
                best_results[(large_thresh, net_thresh)] = {
                    'success_rate': avg_success_rate,
                    'signal_count': signal_count,
                    'score': avg_success_rate * np.log(signal_count + 1)  # Balanced score
                }
        
        # Find best threshold combination
        best_combo = max(best_results.keys(), key=lambda x: best_results[x]['score'])
        self.results['optimal_thresholds'] = {
            'large_threshold': best_combo[0],
            'net_threshold': best_combo[1],
            'performance': best_results[best_combo]
        }
        
        print(f"Optimal thresholds: Large={best_combo[0]:,}, Net={best_combo[1]:,}")
        print(f"Success rate: {best_results[best_combo]['success_rate']:.2%}")
        
        return best_combo
    
    def generate_visualizations(self):
        """Generate charts for analysis validation."""
        print("Generating visualizations...")
        
        plt.style.use('default')
        
        # Determine if we need separate charts based on number of stocks
        n_stocks = len(self.stocks)
        use_separate_charts = n_stocks > 12  # Threshold for separating charts
        
        if use_separate_charts:
            self._generate_separate_charts()
        else:
            self._generate_combined_chart()
    
    def _generate_separate_charts(self):
        """Generate 4 separate charts for better visibility with many stocks."""
        print("Generating separate charts for better visibility...")
        
        correlations = self.results.get('correlations', {})
        stock_labels = [s.replace('.TW', '') for s in self.stocks]
        n_stocks = len(self.stocks)
        
        # Calculate optimal figure size for each chart
        fig_size = max(10, min(16, n_stocks * 0.6))
        font_size = max(8, min(12, 120 // n_stocks))
        
        # Chart 1: Leader-Follower Success Rates Heatmap
        success_matrix = np.zeros((len(self.stocks), len(self.stocks)))
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    success_rate = correlations[leader][follower]['buy_success_rate']
                    success_matrix[i][j] = success_rate
        
        fig1, ax1 = plt.subplots(figsize=(fig_size, fig_size))
        im1 = ax1.imshow(success_matrix, cmap='Reds', aspect='auto')
        ax1.set_xticks(range(len(self.stocks)))
        ax1.set_yticks(range(len(self.stocks)))
        ax1.set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        ax1.set_yticklabels(stock_labels, fontsize=font_size)
        ax1.set_title('Leader-Follower Success Rates\n(Leader=Y-axis, Follower=X-axis)', fontsize=14)
        plt.colorbar(im1, ax=ax1)
        
        # Add text annotations if not too crowded
        if n_stocks <= 20:
            for i in range(len(self.stocks)):
                for j in range(len(self.stocks)):
                    if success_matrix[i][j] > 0:
                        ax1.text(j, i, f'{success_matrix[i][j]:.2f}', 
                               ha='center', va='center', 
                               color='white' if success_matrix[i][j] > 0.5 else 'black',
                               fontsize=max(6, font_size-3))
        
        plt.tight_layout()
        output_path1 = self._get_output_path('leader_follower_success_rates.png')
        plt.savefig(output_path1, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 2: Average Response Time Lags
        lag_matrix = np.zeros((len(self.stocks), len(self.stocks)))
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    avg_lag = correlations[leader][follower]['avg_buy_lag']
                    lag_matrix[i][j] = avg_lag if avg_lag > 0 else np.nan
        
        fig2, ax2 = plt.subplots(figsize=(fig_size, fig_size))
        im2 = ax2.imshow(lag_matrix, cmap='Blues', aspect='auto')
        ax2.set_xticks(range(len(self.stocks)))
        ax2.set_yticks(range(len(self.stocks)))
        ax2.set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        ax2.set_yticklabels(stock_labels, fontsize=font_size)
        ax2.set_title('Average Response Time Lags (minutes)\n(Leader=Y-axis, Follower=X-axis)', fontsize=14)
        plt.colorbar(im2, ax=ax2)
        
        # Add text annotations if not too crowded
        if n_stocks <= 20:
            for i in range(len(self.stocks)):
                for j in range(len(self.stocks)):
                    if not np.isnan(lag_matrix[i][j]) and lag_matrix[i][j] > 0:
                        ax2.text(j, i, f'{lag_matrix[i][j]:.1f}', 
                               ha='center', va='center', 
                               color='white' if lag_matrix[i][j] > 15 else 'black',
                               fontsize=max(6, font_size-3))
        
        plt.tight_layout()
        output_path2 = self._get_output_path('leader_follower_time_lags.png')
        plt.savefig(output_path2, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 3: Signal Distribution by Stock
        signal_counts = []
        stock_names = []
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol]
            buy_signals = stock_data['strong_buy_signal'].sum()
            sell_signals = stock_data['strong_sell_signal'].sum()
            signal_counts.extend([buy_signals, sell_signals])
            stock_names.extend([f'{symbol.replace(".TW", "")}\nBuy', f'{symbol.replace(".TW", "")}\nSell'])
        
        fig3, ax3 = plt.subplots(figsize=(max(12, n_stocks * 0.8), 8))
        colors = ['green', 'red'] * len(self.stocks)
        bars = ax3.bar(range(len(signal_counts)), signal_counts, color=colors, alpha=0.7)
        ax3.set_xticks(range(len(signal_counts)))
        ax3.set_xticklabels(stock_names, rotation=90, ha='center', fontsize=max(8, font_size-2))
        ax3.set_title('Signal Count Distribution', fontsize=14)
        ax3.set_ylabel('Number of Signals')
        
        # Add value labels on bars
        for bar, count in zip(bars, signal_counts):
            if count > 0:
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       str(count), ha='center', va='bottom', fontsize=max(6, font_size-3))
        
        plt.tight_layout()
        output_path3 = self._get_output_path('leader_follower_signal_distribution.png')
        plt.savefig(output_path3, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 4: Average Return Magnitude
        return_matrix = np.zeros((len(self.stocks), len(self.stocks)))
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    avg_return = correlations[leader][follower]['avg_buy_return']
                    return_matrix[i][j] = avg_return * 100  # Convert to percentage
        
        fig4, ax4 = plt.subplots(figsize=(fig_size, fig_size))
        im4 = ax4.imshow(return_matrix, cmap='Greens', aspect='auto')
        ax4.set_xticks(range(len(self.stocks)))
        ax4.set_yticks(range(len(self.stocks)))
        ax4.set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        ax4.set_yticklabels(stock_labels, fontsize=font_size)
        ax4.set_title('Average Follow Return (%)\n(Leader=Y-axis, Follower=X-axis)', fontsize=14)
        plt.colorbar(im4, ax=ax4)
        
        # Add text annotations if not too crowded
        if n_stocks <= 20:
            for i in range(len(self.stocks)):
                for j in range(len(self.stocks)):
                    if return_matrix[i][j] > 0:
                        ax4.text(j, i, f'{return_matrix[i][j]:.1f}%', 
                               ha='center', va='center', 
                               color='white' if return_matrix[i][j] > 1 else 'black',
                               fontsize=max(6, font_size-3))
        
        plt.tight_layout()
        output_path4 = self._get_output_path('leader_follower_returns.png')
        plt.savefig(output_path4, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Separate charts saved:")
        print(f"  - Success Rates: '{output_path1}'")
        print(f"  - Time Lags: '{output_path2}'")
        print(f"  - Signal Distribution: '{output_path3}'")
        print(f"  - Returns: '{output_path4}'")
    
    def _generate_combined_chart(self):
        """Generate combined chart for fewer stocks."""
        # Adjust figure size and layout based on number of stocks
        n_stocks = len(self.stocks)
        if n_stocks > 8:
            fig_width = max(20, n_stocks * 1.5)
            fig_height = max(16, n_stocks * 1.2)
        else:
            fig_width, fig_height = 16, 12
            
        fig, axes = plt.subplots(2, 2, figsize=(fig_width, fig_height))
        
        # 1. Leader-Follower Success Rates Heatmap
        correlations = self.results.get('correlations', {})
        success_matrix = np.zeros((len(self.stocks), len(self.stocks)))
        
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    success_rate = correlations[leader][follower]['buy_success_rate']
                    success_matrix[i][j] = success_rate
        
        im1 = axes[0,0].imshow(success_matrix, cmap='Reds', aspect='auto')
        axes[0,0].set_xticks(range(len(self.stocks)))
        axes[0,0].set_yticks(range(len(self.stocks)))
        
        # Rotate labels and adjust font size for better readability
        stock_labels = [s.replace('.TW', '') for s in self.stocks]
        font_size = max(6, min(10, 80 // n_stocks))  # Scale font size based on number of stocks
        
        axes[0,0].set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        axes[0,0].set_yticklabels(stock_labels, fontsize=font_size)
        axes[0,0].set_title('Leader-Follower Success Rates\n(Leader=Y-axis, Follower=X-axis)', fontsize=12)
        plt.colorbar(im1, ax=axes[0,0])
        
        # Add text annotations only if not too crowded
        if n_stocks <= 10:
            for i in range(len(self.stocks)):
                for j in range(len(self.stocks)):
                    if success_matrix[i][j] > 0:
                        axes[0,0].text(j, i, f'{success_matrix[i][j]:.2f}', 
                                     ha='center', va='center', 
                                     color='white' if success_matrix[i][j] > 0.5 else 'black',
                                     fontsize=max(6, font_size-2))
        
        # 2. Average Response Time Lags
        lag_matrix = np.zeros((len(self.stocks), len(self.stocks)))
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    avg_lag = correlations[leader][follower]['avg_buy_lag']
                    lag_matrix[i][j] = avg_lag if avg_lag > 0 else np.nan
        
        im2 = axes[0,1].imshow(lag_matrix, cmap='Blues', aspect='auto')
        axes[0,1].set_xticks(range(len(self.stocks)))
        axes[0,1].set_yticks(range(len(self.stocks)))
        axes[0,1].set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        axes[0,1].set_yticklabels(stock_labels, fontsize=font_size)
        axes[0,1].set_title('Average Response Time Lags (minutes)\n(Leader=Y-axis, Follower=X-axis)', fontsize=12)
        plt.colorbar(im2, ax=axes[0,1])
        
        # Add text annotations for lags only if not too crowded
        if n_stocks <= 10:
            for i in range(len(self.stocks)):
                for j in range(len(self.stocks)):
                    if not np.isnan(lag_matrix[i][j]) and lag_matrix[i][j] > 0:
                        axes[0,1].text(j, i, f'{lag_matrix[i][j]:.1f}', 
                                     ha='center', va='center', 
                                     color='white' if lag_matrix[i][j] > 15 else 'black',
                                     fontsize=max(6, font_size-2))
        
        # 3. Signal Distribution by Stock
        signal_counts = []
        stock_names = []
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol]
            buy_signals = stock_data['strong_buy_signal'].sum()
            sell_signals = stock_data['strong_sell_signal'].sum()
            signal_counts.extend([buy_signals, sell_signals])
            stock_names.extend([f'{symbol.replace(".TW", "")}\nBuy', f'{symbol.replace(".TW", "")}\nSell'])
        
        colors = ['green', 'red'] * len(self.stocks)
        bars = axes[1,0].bar(range(len(signal_counts)), signal_counts, color=colors, alpha=0.7)
        axes[1,0].set_xticks(range(len(signal_counts)))
        
        # Adjust label rotation and font size for better readability
        label_rotation = 90 if n_stocks > 8 else 45
        axes[1,0].set_xticklabels(stock_names, rotation=label_rotation, ha='right' if label_rotation == 45 else 'center', fontsize=max(6, font_size-1))
        axes[1,0].set_title('Signal Count Distribution', fontsize=12)
        axes[1,0].set_ylabel('Number of Signals')
        
        # Add value labels on bars only if not too crowded
        if n_stocks <= 12:
            for bar, count in zip(bars, signal_counts):
                if count > 0:
                    axes[1,0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                                 str(count), ha='center', va='bottom', fontsize=max(6, font_size-2))
        
        # 4. Average Return Magnitude
        return_matrix = np.zeros((len(self.stocks), len(self.stocks)))
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    avg_return = correlations[leader][follower]['avg_buy_return']
                    return_matrix[i][j] = avg_return * 100  # Convert to percentage
        
        im3 = axes[1,1].imshow(return_matrix, cmap='Greens', aspect='auto')
        axes[1,1].set_xticks(range(len(self.stocks)))
        axes[1,1].set_yticks(range(len(self.stocks)))
        axes[1,1].set_xticklabels(stock_labels, rotation=45, ha='right', fontsize=font_size)
        axes[1,1].set_yticklabels(stock_labels, fontsize=font_size)
        axes[1,1].set_title('Average Follow Return (%)\n(Leader=Y-axis, Follower=X-axis)', fontsize=12)
        plt.colorbar(im3, ax=axes[1,1])
        
        # Add text annotations for returns only if not too crowded
        if n_stocks <= 10:
            for i in range(len(self.stocks)):
                for j in range(len(self.stocks)):
                    if return_matrix[i][j] > 0:
                        axes[1,1].text(j, i, f'{return_matrix[i][j]:.1f}%', 
                                     ha='center', va='center', 
                                     color='white' if return_matrix[i][j] > 1 else 'black',
                                     fontsize=max(6, font_size-2))
        
        plt.tight_layout(pad=3.0)  # Add more padding to prevent label cutoff
        output_path = self._get_output_path('leader_follower_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()  # Don't show in headless environment
        
        print(f"Combined visualization saved as '{output_path}'")
    
    def generate_leadership_analysis_chart(self):
        """Generate comprehensive leadership analysis chart."""
        print("Generating leadership analysis chart...")
        
        # Get leadership analysis data
        leadership_analysis = self.results.get('leadership_analysis', {})
        correlations = self.results.get('correlations', {})
        
        if not leadership_analysis:
            print("No leadership analysis data available")
            return
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Leadership Score Ranking (Top left)
        ax1 = fig.add_subplot(gs[0, 0])
        leaders = leadership_analysis['leaders'][:5]  # Top 5
        leader_names = [s.replace('.TW', '') for s, _ in leaders]
        leader_scores = [data['score'] for _, data in leaders]
        
        bars = ax1.barh(leader_names, leader_scores, color='darkblue', alpha=0.7)
        ax1.set_xlabel('Leadership Score')
        ax1.set_title('Leadership Ranking', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add score labels
        for bar, score in zip(bars, leader_scores):
            ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{score:.1f}', va='center', fontsize=10)
        
        # 2. Followership Score Ranking (Top middle)
        ax2 = fig.add_subplot(gs[0, 1])
        followers = leadership_analysis['followers'][:5]  # Top 5
        follower_names = [s.replace('.TW', '') for s, _ in followers]
        follower_scores = [data['score'] for _, data in followers]
        
        bars = ax2.barh(follower_names, follower_scores, color='darkred', alpha=0.7)
        ax2.set_xlabel('Followership Score')
        ax2.set_title('Follower Ranking', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add score labels
        for bar, score in zip(bars, follower_scores):
            ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                    f'{score:.2f}', va='center', fontsize=10)
        
        # 3. Signal Activity (Top right)
        ax3 = fig.add_subplot(gs[0, 2])
        stocks = [s.replace('.TW', '') for s in self.stocks]
        signal_counts = []
        enhanced_counts = []
        
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol]
            signal_counts.append(stock_data['strong_buy_signal'].sum())
            enhanced_counts.append(stock_data['enhanced_buy_signal'].sum())
        
        x = range(len(stocks))
        width = 0.35
        ax3.bar([i - width/2 for i in x], signal_counts, width, label='Buy Signals', color='green', alpha=0.7)
        ax3.bar([i + width/2 for i in x], enhanced_counts, width, label='Enhanced Signals', color='darkgreen', alpha=0.7)
        ax3.set_xlabel('Stocks')
        ax3.set_ylabel('Signal Count')
        ax3.set_title('Signal Activity', fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(stocks, rotation=45)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Average Response Time Matrix (Middle left)
        ax4 = fig.add_subplot(gs[1, :2])
        
        # Create response time matrix
        stock_names = [s.replace('.TW', '') for s in self.stocks]
        n_stocks = len(stock_names)
        response_matrix = np.full((n_stocks, n_stocks), np.nan)
        
        for i, leader in enumerate(self.stocks):
            for j, follower in enumerate(self.stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    avg_lag = correlations[leader][follower].get('avg_buy_lag', 0)
                    if avg_lag > 0:
                        response_matrix[i, j] = avg_lag
        
        # Create heatmap
        masked_array = np.ma.masked_invalid(response_matrix)
        im = ax4.imshow(masked_array, cmap='YlOrRd', aspect='auto', vmin=0, vmax=30)
        
        # Add text annotations
        for i in range(n_stocks):
            for j in range(n_stocks):
                if not np.isnan(response_matrix[i, j]) and response_matrix[i, j] > 0:
                    text = f'{response_matrix[i, j]:.0f}m'
                    color = 'white' if response_matrix[i, j] > 15 else 'black'
                    ax4.text(j, i, text, ha='center', va='center', color=color, fontsize=9)
        
        ax4.set_xticks(range(n_stocks))
        ax4.set_yticks(range(n_stocks))
        ax4.set_xticklabels(stock_names, rotation=45)
        ax4.set_yticklabels(stock_names)
        ax4.set_xlabel('Follower')
        ax4.set_ylabel('Leader')
        ax4.set_title('Average Response Time (Minutes)', fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
        cbar.set_label('Minutes')
        
        # 5. Success Rate Distribution (Middle right)
        ax5 = fig.add_subplot(gs[1, 2])
        
        # Collect all success rates
        success_rates = []
        for leader in correlations:
            for follower in correlations[leader]:
                rate = correlations[leader][follower].get('buy_success_rate', 0)
                if rate > 0:
                    success_rates.append(rate * 100)  # Convert to percentage
        
        if success_rates:
            ax5.hist(success_rates, bins=10, color='skyblue', alpha=0.7, edgecolor='black')
            ax5.set_xlabel('Success Rate (%)')
            ax5.set_ylabel('Number of Pairs')
            ax5.set_title('Success Rate Distribution', fontweight='bold')
            ax5.grid(True, alpha=0.3)
            
            # Add statistics
            mean_rate = np.mean(success_rates)
            ax5.axvline(mean_rate, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_rate:.1f}%')
            ax5.legend()
        
        # 6. Return Distribution (Bottom left)
        ax6 = fig.add_subplot(gs[2, 0])
        
        # Collect all returns
        returns = []
        for leader in correlations:
            for follower in correlations[leader]:
                avg_return = correlations[leader][follower].get('avg_buy_return', 0)
                if avg_return > 0:
                    returns.append(avg_return * 100)  # Convert to percentage
        
        if returns:
            ax6.hist(returns, bins=10, color='lightgreen', alpha=0.7, edgecolor='black')
            ax6.set_xlabel('Return (%)')
            ax6.set_ylabel('Number of Pairs')
            ax6.set_title('Return Distribution', fontweight='bold')
            ax6.grid(True, alpha=0.3)
            
            # Add statistics
            mean_return = np.mean(returns)
            ax6.axvline(mean_return, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_return:.1f}%')
            ax6.legend()
        
        # 7. Best Pairs Summary (Bottom middle & right)
        ax7 = fig.add_subplot(gs[2, 1:])
        ax7.axis('off')
        
        # Find best pairs
        best_pairs = []
        for leader in correlations:
            for follower in correlations[leader]:
                data = correlations[leader][follower]
                if data.get('buy_success_rate', 0) > 0.5:  # >50% success rate
                    best_pairs.append({
                        'leader': leader.replace('.TW', ''),
                        'follower': follower.replace('.TW', ''),
                        'success_rate': data['buy_success_rate'],
                        'avg_lag': data.get('avg_buy_lag', 0),
                        'avg_return': data.get('avg_buy_return', 0) * 100
                    })
        
        # Sort by success rate
        best_pairs.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # Create table
        if best_pairs:
            table_data = []
            headers = ['Leader', 'Follower', 'Success Rate', 'Time Lag', 'Return']
            
            for pair in best_pairs[:8]:  # Top 8 pairs
                table_data.append([
                    pair['leader'],
                    pair['follower'],
                    f"{pair['success_rate']:.0%}",
                    f"{pair['avg_lag']:.0f}min",
                    f"{pair['avg_return']:.1f}%"
                ])
            
            table = ax7.table(cellText=table_data, colLabels=headers,
                            cellLoc='center', loc='center',
                            colWidths=[0.15, 0.15, 0.15, 0.15, 0.15])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
            
            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            ax7.set_title('Best Leader-Follower Pairs (Success Rate ≥ 50%)', 
                         fontweight='bold', pad=20)
        
        # Add overall title
        fig.suptitle('Comprehensive Leadership Analysis', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        # Save the chart
        output_path = self._get_output_path('leader_analysis.jpg')
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"Leadership analysis chart saved as '{output_path}'")
    
    def identify_leaders_and_followers(self):
        """Dynamically identify leader and follower stocks based on signal patterns."""
        print("Identifying leader and follower stocks...")
        
        # Analyze each stock's leadership characteristics
        leadership_scores = {}
        followership_scores = {}
        
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol].copy()
            
            # Leadership metrics
            signal_count = stock_data['strong_buy_signal'].sum()
            enhanced_signal_count = stock_data['enhanced_buy_signal'].sum()
            avg_large_net = stock_data[stock_data['strong_buy_signal']]['large_net'].mean() if signal_count > 0 else 0
            avg_volume = stock_data[stock_data['strong_buy_signal']]['volume'].mean() if signal_count > 0 else 0
            
            # Calculate leadership score
            leadership_score = (
                signal_count * 0.3 +                    # Signal frequency
                enhanced_signal_count * 0.4 +           # Enhanced signal quality
                (avg_large_net / 1000000) * 0.2 +       # Average net flow strength
                (avg_volume / 1000) * 0.1                # Volume strength
            )
            
            leadership_scores[symbol] = {
                'score': leadership_score,
                'signal_count': signal_count,
                'enhanced_count': enhanced_signal_count,
                'avg_net_flow': avg_large_net / 1000000 if avg_large_net else 0,
                'avg_volume': avg_volume
            }
        
        # Sort by leadership score
        sorted_leaders = sorted(leadership_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # Analyze followership for each stock
        correlations = self.results.get('correlations', {})
        
        for symbol in self.stocks:
            # Calculate how often this stock follows others
            follow_responses = []
            
            for leader in correlations:
                if symbol.replace('.TW', '') in [f.replace('.TW', '') for f in correlations[leader]] and leader != symbol:
                    follower_key = symbol
                    if follower_key in correlations[leader]:
                        response_data = correlations[leader][follower_key]
                        if response_data['buy_success_rate'] > 0:
                            follow_responses.append({
                                'leader': leader,
                                'success_rate': response_data['buy_success_rate'],
                                'avg_lag': response_data.get('avg_buy_lag', 0),
                                'avg_return': response_data.get('avg_buy_return', 0)
                            })
            
            # Calculate followership score
            if follow_responses:
                avg_success_rate = np.mean([r['success_rate'] for r in follow_responses])
                response_count = len(follow_responses)
                avg_return = np.mean([r['avg_return'] for r in follow_responses])
                
                followership_score = (
                    avg_success_rate * 0.5 +              # Success rate of following
                    (response_count / len(self.stocks)) * 0.3 +  # Responsiveness to multiple leaders
                    avg_return * 0.2                       # Average return when following
                )
            else:
                followership_score = 0
                
            followership_scores[symbol] = {
                'score': followership_score,
                'response_count': len(follow_responses),
                'avg_success_rate': np.mean([r['success_rate'] for r in follow_responses]) if follow_responses else 0,
                'avg_return': np.mean([r['avg_return'] for r in follow_responses]) if follow_responses else 0,
                'responses': follow_responses
            }
        
        # Sort by followership score
        sorted_followers = sorted(followership_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # Store results
        self.results['leadership_analysis'] = {
            'leaders': sorted_leaders,
            'followers': sorted_followers,
            'leadership_scores': leadership_scores,
            'followership_scores': followership_scores
        }
        
        # Print analysis
        print("\n=== 龍頭股排名 ===")
        for i, (symbol, data) in enumerate(sorted_leaders[:3], 1):
            print(f"{i}. {symbol.replace('.TW', '')}: 分數={data['score']:.2f} "
                  f"(訊號數={data['signal_count']}, 強化訊號={data['enhanced_count']}, "
                  f"平均淨流入={data['avg_net_flow']:.1f}M)")
        
        print("\n=== 跟隨股排名 ===")
        for i, (symbol, data) in enumerate(sorted_followers[:3], 1):
            print(f"{i}. {symbol.replace('.TW', '')}: 分數={data['score']:.2f} "
                  f"(響應次數={data['response_count']}, 平均成功率={data['avg_success_rate']:.1%}, "
                  f"平均報酬={data['avg_return']*100:.1f}%)")
        
        return sorted_leaders, sorted_followers
    
    def get_dynamic_key_pairs(self, top_leaders=2, top_followers=3):
        """Get key leader-follower pairs based on dynamic analysis."""
        leadership_analysis = self.results.get('leadership_analysis', {})
        
        if not leadership_analysis:
            # Fallback to previous method if analysis not done
            return [('1597.TW', '6215.TW'), ('1597.TW', '2359.TW'), ('1597.TW', '2049.TW')]
        
        leaders = leadership_analysis['leaders'][:top_leaders]
        followers = leadership_analysis['followers'][:top_followers]
        
        # Generate all combinations of top leaders and followers
        key_pairs = []
        for leader_symbol, _ in leaders:
            for follower_symbol, _ in followers:
                if leader_symbol != follower_symbol:
                    key_pairs.append((leader_symbol, follower_symbol))
        
        return key_pairs
    
    def analyze_detailed_conditions(self):
        """Analyze detailed trigger conditions for leader-follower relationships."""
        print("Analyzing detailed trigger conditions...")
        
        detailed_conditions = {}
        
        # Get dynamic key pairs instead of hard-coded ones
        key_pairs = self.get_dynamic_key_pairs()
        
        for leader_symbol, follower_symbol in key_pairs:
            print(f"\nAnalyzing {leader_symbol} → {follower_symbol}...")
            
            leader_data = self.data[self.data['symbol'] == leader_symbol].copy()
            follower_data = self.data[self.data['symbol'] == follower_symbol].copy()
            
            # Get leader signals
            leader_signals = leader_data[leader_data['strong_buy_signal']].copy()
            
            if len(leader_signals) == 0:
                continue
                
            signal_analysis = []
            
            for idx, signal in leader_signals.iterrows():
                signal_time = signal['datetime']
                
                # Detailed conditions at signal time
                conditions = {
                    'signal_time': signal_time,
                    'leader_price': signal['close_price'],
                    'leader_price_change': signal['return_1min'] * 100,  # %
                    'leader_volume': signal['volume'],
                    'leader_large_net': signal['large_net'] / 1000000,  # Million
                    'leader_large_total': signal['large_total'] / 1000000,  # Million
                    'is_daily_high': signal['is_daily_high'],
                    'is_5d_high': signal['is_5d_high'],
                    'is_enhanced': signal['enhanced_buy_signal']
                }
                
                # Find follower response within 30 minutes
                response_window = follower_data[
                    (follower_data['datetime'] > signal_time) & 
                    (follower_data['datetime'] <= signal_time + timedelta(minutes=30))
                ].copy()
                
                if not response_window.empty:
                    # Calculate follower returns at different time intervals
                    follower_price_at_signal = follower_data[
                        follower_data['datetime'] <= signal_time
                    ]['close_price'].iloc[-1] if len(follower_data[follower_data['datetime'] <= signal_time]) > 0 else None
                    
                    if follower_price_at_signal:
                        # Check returns at 5, 10, 15, 20, 30 minutes
                        for minutes in [5, 10, 15, 20, 30]:
                            target_time = signal_time + timedelta(minutes=minutes)
                            nearby_data = response_window[
                                abs(response_window['datetime'] - target_time) <= timedelta(minutes=2)
                            ]
                            
                            if not nearby_data.empty:
                                follower_price_later = nearby_data['close_price'].iloc[0]
                                return_pct = ((follower_price_later - follower_price_at_signal) / follower_price_at_signal) * 100
                                conditions[f'follower_return_{minutes}min'] = return_pct
                                
                                # Mark as successful if return > 1%
                                conditions[f'success_{minutes}min'] = return_pct > 1.0
                            else:
                                conditions[f'follower_return_{minutes}min'] = None
                                conditions[f'success_{minutes}min'] = False
                        
                        # Find maximum return within 30 minutes
                        max_return = 0
                        max_return_time = None
                        for _, row in response_window.iterrows():
                            return_pct = ((row['close_price'] - follower_price_at_signal) / follower_price_at_signal) * 100
                            if return_pct > max_return:
                                max_return = return_pct
                                max_return_time = row['datetime']
                        
                        conditions['max_return_30min'] = max_return
                        conditions['max_return_time'] = max_return_time
                        conditions['time_to_max_return'] = (max_return_time - signal_time).total_seconds() / 60 if max_return_time else None
                
                signal_analysis.append(conditions)
            
            detailed_conditions[f"{leader_symbol}_{follower_symbol}"] = signal_analysis
        
        self.results['detailed_conditions'] = detailed_conditions
        return detailed_conditions
    
    def generate_pair_chart(self, leader_symbol='1597.TW', follower_symbol='6215.TW', 
                           start_date=None, end_date=None):
        """Generate paired stock price chart with buy/sell signals."""
        print(f"Generating pair chart for {leader_symbol} vs {follower_symbol}...")
        
        # Get data for both stocks
        leader_data = self.data[self.data['symbol'] == leader_symbol].copy()
        follower_data = self.data[self.data['symbol'] == follower_symbol].copy()
        
        # Filter by date if specified
        if start_date:
            leader_data = leader_data[leader_data['datetime'] >= start_date]
            follower_data = follower_data[follower_data['datetime'] >= start_date]
        if end_date:
            leader_data = leader_data[leader_data['datetime'] <= end_date]
            follower_data = follower_data[follower_data['datetime'] <= end_date]
        
        if leader_data.empty or follower_data.empty:
            print("No data available for the specified period")
            return
        
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
        
        # Normalize prices to percentage change from first price for comparison
        leader_data = leader_data.copy()
        follower_data = follower_data.copy()
        
        if len(leader_data) > 0 and len(follower_data) > 0:
            leader_first_price = leader_data['close_price'].iloc[0]
            follower_first_price = follower_data['close_price'].iloc[0]
            
            leader_data['price_normalized'] = ((leader_data['close_price'] - leader_first_price) / leader_first_price) * 100
            follower_data['price_normalized'] = ((follower_data['close_price'] - follower_first_price) / follower_first_price) * 100
        
        # Plot 1: Normalized Price Comparison
        ax1.plot(leader_data['datetime'], leader_data['price_normalized'], 
                label=f'{leader_symbol.replace(".TW", "")} (Leader)', color='blue', linewidth=1.5)
        ax1.plot(follower_data['datetime'], follower_data['price_normalized'], 
                label=f'{follower_symbol.replace(".TW", "")} (Follower)', color='red', linewidth=1.5)
        
        # Mark leader buy signals
        leader_signals = leader_data[leader_data['strong_buy_signal']]
        for _, signal in leader_signals.iterrows():
            ax1.scatter(signal['datetime'], signal['price_normalized'], 
                       color='green', s=100, marker='^', zorder=5, alpha=0.8)
            ax1.annotate(f'Buy Signal\n{signal["large_net"]/1000000:.1f}M', 
                        xy=(signal['datetime'], signal['price_normalized']),
                        xytext=(10, 20), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        ax1.set_ylabel('Price Change (%)')
        ax1.set_title(f'Price Comparison: {leader_symbol.replace(".TW", "")} vs {follower_symbol.replace(".TW", "")}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Volume and Large Orders
        ax2_twin = ax2.twinx()
        
        # Leader volume and net flow
        ax2.bar(leader_data['datetime'], leader_data['volume'], alpha=0.3, color='blue', 
               label=f'{leader_symbol.replace(".TW", "")} Volume')
        ax2_twin.plot(leader_data['datetime'], leader_data['large_net']/1000000, 
                     color='darkblue', linewidth=2, label='Leader Net Flow (M)')
        
        ax2.set_ylabel('Volume')
        ax2_twin.set_ylabel('Net Large Orders (Million)')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        
        # Plot 3: Follower Volume and Returns
        ax3_twin = ax3.twinx()
        
        ax3.bar(follower_data['datetime'], follower_data['volume'], alpha=0.3, color='red',
               label=f'{follower_symbol.replace(".TW", "")} Volume')
        ax3_twin.plot(follower_data['datetime'], follower_data['return_1min']*100, 
                     color='darkred', linewidth=1, label='Follower 1min Return (%)')
        
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Volume')
        ax3_twin.set_ylabel('1-minute Return (%)')
        ax3.legend(loc='upper left')
        ax3_twin.legend(loc='upper right')
        
        # Format x-axis
        import matplotlib.dates as mdates
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax3.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save the chart
        filename = f'pair_chart_{leader_symbol.replace(".TW", "")}_{follower_symbol.replace(".TW", "")}.png'
        output_path = self._get_output_path(filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Pair chart saved as: {output_path}")
        return output_path
    
    def generate_detailed_analysis_report(self):
        """Generate detailed analysis report with trigger conditions."""
        print("Generating detailed analysis report...")
        
        detailed_conditions = self.results.get('detailed_conditions', {})
        
        report_lines = []
        report_lines.append("=== 詳細觸發條件分析報告 ===\n")
        
        for pair_key, signal_list in detailed_conditions.items():
            if not signal_list:
                continue
                
            leader, follower = pair_key.split('_')
            leader_name = leader.replace('.TW', '')
            follower_name = follower.replace('.TW', '')
            
            report_lines.append(f"## {leader_name} → {follower_name} 詳細分析")
            report_lines.append("-" * 50)
            
            # Analyze successful conditions
            successful_signals = []
            all_conditions = []
            
            for signal in signal_list:
                all_conditions.append(signal)
                # Consider successful if 10-minute return > 1%
                if signal.get('success_10min', False):
                    successful_signals.append(signal)
            
            success_rate = len(successful_signals) / len(all_conditions) if all_conditions else 0
            report_lines.append(f"總訊號數: {len(all_conditions)}")
            report_lines.append(f"成功訊號數: {len(successful_signals)} (成功率: {success_rate:.1%})")
            report_lines.append("")
            
            if successful_signals:
                # Analyze successful conditions
                report_lines.append("### 成功案例的觸發條件分析:")
                
                # Price change analysis
                price_changes = [s['leader_price_change'] for s in successful_signals if s.get('leader_price_change')]
                if price_changes:
                    report_lines.append(f"龍頭股漲幅範圍: {min(price_changes):.2f}% ~ {max(price_changes):.2f}%")
                    report_lines.append(f"平均漲幅: {np.mean(price_changes):.2f}%")
                
                # Net flow analysis  
                net_flows = [s['leader_large_net'] for s in successful_signals if s.get('leader_large_net')]
                if net_flows:
                    report_lines.append(f"淨買超範圍: {min(net_flows):.1f}M ~ {max(net_flows):.1f}M")
                    report_lines.append(f"平均淨買超: {np.mean(net_flows):.1f}M")
                
                # New high analysis
                new_high_count = sum(1 for s in successful_signals if s.get('is_daily_high', False))
                enhanced_count = sum(1 for s in successful_signals if s.get('is_enhanced', False))
                
                report_lines.append(f"創當日新高比例: {new_high_count}/{len(successful_signals)} ({new_high_count/len(successful_signals):.1%})")
                report_lines.append(f"強化訊號比例: {enhanced_count}/{len(successful_signals)} ({enhanced_count/len(successful_signals):.1%})")
                
                # Return analysis
                returns_10min = [s['follower_return_10min'] for s in successful_signals if s.get('follower_return_10min')]
                max_returns = [s['max_return_30min'] for s in successful_signals if s.get('max_return_30min')]
                
                if returns_10min:
                    report_lines.append(f"10分鐘跟漲幅度: {min(returns_10min):.2f}% ~ {max(returns_10min):.2f}%")
                    report_lines.append(f"平均10分鐘漲幅: {np.mean(returns_10min):.2f}%")
                
                if max_returns:
                    report_lines.append(f"30分鐘內最大漲幅: {np.mean(max_returns):.2f}%")
                
                report_lines.append("")
                
                # Detailed signal table
                report_lines.append("### 詳細訊號記錄:")
                report_lines.append("時間\t\t\t龍頭漲幅%\t淨買超M\t創新高\t跟隨10min%\t最大漲幅%")
                report_lines.append("-" * 80)
                
                for signal in successful_signals:
                    time_str = signal['signal_time'].strftime('%Y/%m/%d %H:%M')
                    price_change = signal.get('leader_price_change', 0)
                    net_flow = signal.get('leader_large_net', 0)
                    is_high = "是" if signal.get('is_daily_high', False) else "否"
                    return_10min = signal.get('follower_return_10min', 0)
                    max_return = signal.get('max_return_30min', 0)
                    
                    report_lines.append(f"{time_str}\t{price_change:.2f}%\t\t{net_flow:.1f}\t{is_high}\t{return_10min:.2f}%\t\t{max_return:.2f}%")
                
                report_lines.append("")
            
            # Failed cases analysis
            failed_signals = [s for s in all_conditions if not s.get('success_10min', False)]
            if failed_signals:
                report_lines.append("### 失敗案例分析:")
                
                # Analyze why they failed
                failed_price_changes = [s['leader_price_change'] for s in failed_signals if s.get('leader_price_change')]
                failed_net_flows = [s['leader_large_net'] for s in failed_signals if s.get('leader_large_net')]
                
                if failed_price_changes:
                    report_lines.append(f"失敗案例龍頭漲幅: 平均 {np.mean(failed_price_changes):.2f}%")
                if failed_net_flows:
                    report_lines.append(f"失敗案例淨買超: 平均 {np.mean(failed_net_flows):.1f}M")
                
                failed_new_high = sum(1 for s in failed_signals if s.get('is_daily_high', False))
                report_lines.append(f"失敗案例創新高比例: {failed_new_high}/{len(failed_signals)} ({failed_new_high/len(failed_signals):.1%})")
                report_lines.append("")
            
            report_lines.append("\n")
        
        # Generate recommendations
        report_lines.append("=== 優化建議 ===")
        report_lines.append("基於以上分析，建議的觸發條件:")
        report_lines.append("")
        
        # Find the best performing conditions
        all_successful = []
        for signal_list in detailed_conditions.values():
            all_successful.extend([s for s in signal_list if s.get('success_10min', False)])
        
        if all_successful:
            best_price_changes = [s['leader_price_change'] for s in all_successful if s.get('leader_price_change')]
            best_net_flows = [s['leader_large_net'] for s in all_successful if s.get('leader_large_net')]
            best_new_high_rate = sum(1 for s in all_successful if s.get('is_daily_high', False)) / len(all_successful)
            
            if best_price_changes:
                min_price_change = np.percentile(best_price_changes, 25)  # 25th percentile
                report_lines.append(f"1. 龍頭股漲幅 ≥ {min_price_change:.2f}%")
            
            if best_net_flows:
                min_net_flow = np.percentile(best_net_flows, 25)  # 25th percentile  
                report_lines.append(f"2. 淨買超金額 ≥ {min_net_flow:.1f} 百萬")
            
            if best_new_high_rate > 0.6:
                report_lines.append("3. 建議優先考慮創當日新高的訊號")
            
            report_lines.append("4. 建議在訊號出現後 8-12 分鐘內進場")
            report_lines.append("5. 設定停利: 1.5-2% 或持有 10-15 分鐘")
            report_lines.append("6. 設定停損: -1% 或持有超過 20 分鐘無漲幅")
        
        report_text = '\n'.join(report_lines)
        
        # Save to file
        output_path = self._get_output_path('detailed_analysis_report.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.results['detailed_report'] = report_text
        return report_text
    
    def generate_signal_table(self):
        """Generate detailed trading signal table."""
        print("Generating detailed signal table...")
        
        # Collect all signals with details
        signal_records = []
        
        for symbol in self.stocks:
            stock_data = self.data[self.data['symbol'] == symbol].copy()
            
            # Buy signals
            buy_signals = stock_data[stock_data['strong_buy_signal']].copy()
            for idx, row in buy_signals.iterrows():
                signal_records.append({
                    'datetime': row['datetime'],
                    'date': row['datetime'].strftime('%Y/%m/%d'),
                    'time': row['datetime'].strftime('%H:%M:%S'),
                    'symbol': symbol.replace('.TW', ''),
                    'signal_type': '做多',
                    'price': row['close_price'],
                    'volume': row['volume'],
                    'large_buy': row['large_buy'],
                    'xlarge_buy': row['xlarge_buy'],
                    'large_sell': row['large_sell'],
                    'xlarge_sell': row['xlarge_sell'],
                    'large_total': row['large_total'],
                    'large_net': row['large_net'],
                    'is_enhanced': row['enhanced_buy_signal'],
                    'is_daily_high': row['is_daily_high'],
                    'is_5d_high': row['is_5d_high'],
                    'price_change_pct': row['price_change_pct'],
                    'return_1min': row['return_1min'] * 100,  # Convert to percentage
                })
            
            # Sell signals
            sell_signals = stock_data[stock_data['strong_sell_signal']].copy()
            for idx, row in sell_signals.iterrows():
                signal_records.append({
                    'datetime': row['datetime'],
                    'date': row['datetime'].strftime('%Y/%m/%d'),
                    'time': row['datetime'].strftime('%H:%M:%S'),
                    'symbol': symbol.replace('.TW', ''),
                    'signal_type': '做空',
                    'price': row['close_price'],
                    'volume': row['volume'],
                    'large_buy': row['large_buy'],
                    'xlarge_buy': row['xlarge_buy'],
                    'large_sell': row['large_sell'],
                    'xlarge_sell': row['xlarge_sell'],
                    'large_total': row['large_total'],
                    'large_net': row['large_net'],
                    'is_enhanced': row['enhanced_sell_signal'],
                    'is_daily_high': row['is_daily_high'],
                    'is_5d_high': row['is_5d_high'],
                    'price_change_pct': row['price_change_pct'],
                    'return_1min': row['return_1min'] * 100,  # Convert to percentage
                })
        
        # Convert to DataFrame and sort by datetime
        if signal_records:
            signals_df = pd.DataFrame(signal_records)
            signals_df = signals_df.sort_values('datetime').reset_index(drop=True)
            
            # Format the table for display
            display_df = signals_df[[
                'date', 'time', 'symbol', 'signal_type', 'price', 
                'large_total', 'large_net', 'return_1min', 'is_enhanced'
            ]].copy()
            
            # Rename columns for better readability
            display_df.columns = [
                '日期', '時間', '股票', '操作', '價格',
                '大單總額', '淨買超', '漲跌%', '強化訊號'
            ]
            
            # Format numbers
            display_df['價格'] = display_df['價格'].round(2)
            display_df['大單總額'] = (display_df['大單總額'] / 1000000).round(1)  # Convert to millions
            display_df['淨買超'] = (display_df['淨買超'] / 1000000).round(1)      # Convert to millions
            display_df['漲跌%'] = display_df['漲跌%'].round(2)
            display_df['強化訊號'] = display_df['強化訊號'].map({True: '是', False: '否'})
            
            # Save to CSV
            detailed_path = self._get_output_path('trading_signals_detailed.csv')
            summary_path = self._get_output_path('trading_signals_summary.csv')
            signals_df.to_csv(detailed_path, index=False, encoding='utf-8-sig')
            display_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
            
            self.results['signal_table'] = display_df
            self.results['signal_records'] = signals_df
            
            print(f"Generated {len(signals_df)} trading signals")
            return display_df
        else:
            print("No trading signals found")
            return pd.DataFrame()
    
    def generate_plain_explanation(self):
        """Generate plain language explanation of analysis results."""
        print("Generating plain language explanation...")
        
        correlations = self.results.get('correlations', {})
        signal_table = self.results.get('signal_table', pd.DataFrame())
        
        explanation = []
        explanation.append("=== 股票跟漲跟跌分析 - 白話說明 ===\n")
        
        # 1. Data Summary
        explanation.append("📊 **資料概況**")
        explanation.append(f"• 分析了 {len(self.stocks)} 檔股票：{', '.join([s.replace('.TW', '') for s in self.stocks])}")
        explanation.append(f"• 資料期間：{self.data['datetime'].min().strftime('%Y/%m/%d')} 到 {self.data['datetime'].max().strftime('%Y/%m/%d')}")
        explanation.append(f"• 分析時段：每天 09:01-12:40 (適合當沖操作)")
        explanation.append(f"• 共有 {len(self.data):,} 筆分鐘資料\n")
        
        # 2. Signal Analysis
        if not signal_table.empty:
            explanation.append("🚨 **交易訊號分析**")
            buy_signals = signal_table[signal_table['操作'] == '做多']
            sell_signals = signal_table[signal_table['操作'] == '做空']
            
            explanation.append(f"• 總共發現 {len(signal_table)} 個交易訊號")
            explanation.append(f"  - 做多訊號：{len(buy_signals)} 個")
            explanation.append(f"  - 做空訊號：{len(sell_signals)} 個")
            
            if len(buy_signals) > 0:
                most_active = buy_signals['股票'].value_counts().index[0]
                explanation.append(f"• 最活躍的股票：{most_active} (有 {buy_signals['股票'].value_counts().iloc[0]} 個做多訊號)")
            
            explanation.append(f"• 訊號觸發條件：大單總額 ≥ 100萬，淨買超 ≥ 50萬")
            explanation.append("")
        
        # 3. Leader-Follower Relationships
        explanation.append("👑 **龍頭跟隨關係**")
        
        # Find best leader-follower pairs
        best_pairs = []
        for leader in correlations:
            for follower in correlations[leader]:
                data = correlations[leader][follower]
                if data['buy_success_rate'] > 0.3:  # >30% success rate
                    best_pairs.append({
                        'leader': leader.replace('.TW', ''),
                        'follower': follower.replace('.TW', ''),
                        'success_rate': data['buy_success_rate'],
                        'avg_lag': data['avg_buy_lag'],
                        'avg_return': data['avg_buy_return'] * 100
                    })
        
        best_pairs.sort(key=lambda x: x['success_rate'], reverse=True)
        
        if best_pairs:
            # Use dynamic analysis to find the best leader
            leadership_analysis = self.results.get('leadership_analysis', {})
            if leadership_analysis and leadership_analysis['leaders']:
                best_leader = leadership_analysis['leaders'][0][0].replace('.TW', '')
            else:
                # Fallback to correlation-based method
                leader_scores = {}
                for pair in best_pairs:
                    leader = pair['leader']
                    if leader not in leader_scores:
                        leader_scores[leader] = []
                    leader_scores[leader].append(pair['success_rate'])
                
                best_leader = max(leader_scores.keys(), 
                                key=lambda x: (len(leader_scores[x]), np.mean(leader_scores[x])))
            
            explanation.append(f"• **龍頭股票**：{best_leader}")
            explanation.append(f"  - 這檔股票最容易帶動其他股票跟漲")
            explanation.append(f"  - 當 {best_leader} 有大單買進並且急漲時，其他股票很容易跟著漲")
            explanation.append("")
            
            explanation.append("• **最佳跟隨組合** (成功率 ≥ 50%)：")
            for pair in best_pairs[:5]:  # Top 5 pairs
                if pair['success_rate'] >= 0.5:
                    explanation.append(f"  - {pair['leader']} 漲 → {pair['follower']} 跟漲")
                    explanation.append(f"    成功率：{pair['success_rate']:.0%}")
                    explanation.append(f"    時間差：約 {pair['avg_lag']:.0f} 分鐘")
                    explanation.append(f"    平均跟漲：{pair['avg_return']:.1f}%")
                    explanation.append("")
            
            # Trading strategy explanation
            explanation.append("💡 **交易策略建議**")
            explanation.append(f"1. **監控龍頭股 {best_leader}**：")
            explanation.append(f"   - 當 {best_leader} 出現大單買進 (≥100萬) 且急漲時")
            explanation.append(f"   - 立即關注跟隨股票的買進機會")
            explanation.append("")
            
            explanation.append("2. **跟隨股票操作**：")
            for pair in best_pairs[:3]:  # Top 3 pairs
                if pair['success_rate'] >= 0.7:
                    explanation.append(f"   - {pair['leader']} 漲 → 在 {pair['avg_lag']:.0f} 分鐘內買進 {pair['follower']}")
            explanation.append("")
            
            explanation.append("3. **風險控制**：")
            explanation.append("   - 設定停損：跌破買進價 2%")
            explanation.append("   - 設定停利：漲幅達 3-5%")
            explanation.append("   - 時間控制：如果 30 分鐘內沒有跟漲就停損出場")
            explanation.append("")
            
        else:
            explanation.append("• 目前的資料中沒有發現明顯的龍頭跟隨關係")
            explanation.append("• 建議降低訊號門檻或增加更多資料來分析")
            explanation.append("")
        
        # 4. Market Timing
        if not signal_table.empty:
            explanation.append("⏰ **最佳交易時段**")
            
            # Analyze signal timing
            signals_with_time = self.results.get('signal_records', pd.DataFrame())
            if not signals_with_time.empty:
                signals_with_time['hour'] = signals_with_time['datetime'].dt.hour
                hour_counts = signals_with_time['hour'].value_counts().sort_index()
                
                best_hour = hour_counts.index[0]
                explanation.append(f"• 訊號最常出現的時段：{best_hour}:00-{best_hour+1}:00")
                explanation.append(f"• 建議在 {best_hour}:00 前準備好資金，密切關注盤面")
                explanation.append("")
        
        # 5. Important Notes
        explanation.append("⚠️  **重要提醒**")
        explanation.append("• 這個分析基於歷史資料，不保證未來表現")
        explanation.append("• 股票投資有風險，請做好風險控制")
        explanation.append("• 建議先用小額資金測試策略")
        explanation.append("• 市場狀況變化時，要適時調整策略")
        
        explanation_text = '\n'.join(explanation)
        
        # Save explanation to file
        output_path = self._get_output_path('analysis_explanation.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(explanation_text)
        
        self.results['explanation'] = explanation_text
        return explanation_text
    
    def generate_report(self):
        """Generate comprehensive analysis report."""
        print("\n" + "="*80)
        print("PAIR TRADING ANALYSIS REPORT")
        print("="*80)
        
        print(f"\nSTOCKS ANALYZED: {', '.join([s.replace('.TW', '') for s in self.stocks])}")
        print(f"DATA POINTS: {len(self.data):,} records")
        print(f"TIME PERIOD: {self.data['datetime'].min()} to {self.data['datetime'].max()}")
        
        # Optimal thresholds
        if 'optimal_thresholds' in self.results:
            opt = self.results['optimal_thresholds']
            print(f"\nOPTIMAL SIGNAL THRESHOLDS:")
            print(f"Large Order Amount: ≥ {opt['large_threshold']:,}")
            print(f"Net Buy Amount: ≥ {opt['net_threshold']:,}")
            print(f"Success Rate: {opt['performance']['success_rate']:.1%}")
            print(f"Signal Count: {opt['performance']['signal_count']}")
        
        # Leader-follower relationships
        correlations = self.results.get('correlations', {})
        print(f"\nLEADER-FOLLOWER RELATIONSHIPS:")
        print("-" * 60)
        
        best_pairs = []
        for leader in correlations:
            for follower in correlations[leader]:
                data = correlations[leader][follower]
                if data['buy_success_rate'] > 0.3:  # >30% success rate
                    best_pairs.append({
                        'leader': leader.replace('.TW', ''),
                        'follower': follower.replace('.TW', ''),
                        'success_rate': data['buy_success_rate'],
                        'avg_lag': data['avg_buy_lag'],
                        'avg_return': data['avg_buy_return'] * 100
                    })
        
        # Sort by success rate
        best_pairs.sort(key=lambda x: x['success_rate'], reverse=True)
        
        print(f"{'Leader':<8} {'Follower':<8} {'Success%':<8} {'Lag(min)':<8} {'Return%':<8}")
        print("-" * 48)
        for pair in best_pairs[:10]:  # Top 10 pairs
            print(f"{pair['leader']:<8} {pair['follower']:<8} {pair['success_rate']:<8.1%} "
                  f"{pair['avg_lag']:<8.1f} {pair['avg_return']:<8.1f}%")
        
        # Summary insights
        print(f"\nKEY INSIGHTS:")
        print("-" * 20)
        
        if best_pairs:
            # Find most consistent leader
            leader_scores = {}
            for pair in best_pairs:
                leader = pair['leader']
                leader_scores[leader] = leader_scores.get(leader, [])
                leader_scores[leader].append(pair['success_rate'])
            
            best_leader = max(leader_scores.keys(), 
                            key=lambda x: (len(leader_scores[x]), np.mean(leader_scores[x])))
            
            # Find most responsive follower
            follower_scores = {}
            for pair in best_pairs:
                follower = pair['follower']
                follower_scores[follower] = follower_scores.get(follower, [])
                follower_scores[follower].append(pair['success_rate'])
            
            best_follower = max(follower_scores.keys(), 
                              key=lambda x: (len(follower_scores[x]), np.mean(follower_scores[x])))
            
            print(f"• Most Consistent Leader: {best_leader}")
            print(f"• Most Responsive Follower: {best_follower}")
            print(f"• Average Response Time: {np.mean([p['avg_lag'] for p in best_pairs]):.1f} minutes")
            print(f"• Average Follow Return: {np.mean([p['avg_return'] for p in best_pairs]):.1f}%")
            print(f"• Best Success Rate: {max(pair['success_rate'] for pair in best_pairs):.1%}")
        else:
            print("• No strong leader-follower relationships detected with current thresholds")
            print("• Consider adjusting signal detection parameters")
        
        print(f"\nRECOMMENDATIONS:")
        print("-" * 15)
        if best_pairs:
            print("• Focus on top 3-5 leader-follower pairs for trading strategy")
            print("• Monitor leader stocks for large order signals")
            print("• Set alerts for follower stocks with 2-10 minute delay")
            print("• Backtest strategy with identified optimal thresholds")
        else:
            print("• Re-examine data with lower threshold values")
            print("• Consider shorter time intervals for signal detection")
            print("• Verify data quality and completeness")
    
    def run_analysis(self):
        """Run complete analysis pipeline."""
        print("Starting Pair Trading Analysis...")
        print("=" * 50)
        
        # Load and process data
        self.load_data()
        self.calculate_price_movements()
        
        # Find optimal thresholds
        optimal_thresholds = self.optimize_thresholds()
        
        # Use optimal thresholds for signal identification
        self.identify_signals(
            large_threshold=optimal_thresholds[0],
            net_threshold=optimal_thresholds[1]
        )
        
        # Analyze relationships
        self.analyze_leader_follower()
        
        # Generate outputs
        self.generate_visualizations()
        
        # Generate new detailed analysis
        detailed_conditions = self.analyze_detailed_conditions()
        
        # Dynamic leader-follower identification
        leaders, followers = self.identify_leaders_and_followers()
        
        # Generate comprehensive leadership analysis chart
        self.generate_leadership_analysis_chart()
        
        # Generate pair charts for top dynamic relationships
        key_pairs = self.get_dynamic_key_pairs(top_leaders=2, top_followers=2)
        for leader, follower in key_pairs[:3]:  # Limit to top 3 pairs
            self.generate_pair_chart(leader, follower)
        
        # Generate detailed analysis report
        detailed_report = self.generate_detailed_analysis_report()
        
        # Generate new features
        signal_table = self.generate_signal_table()
        explanation = self.generate_plain_explanation()
        
        # Generate traditional report
        self.generate_report()
        
        # Display signal table if exists
        if not signal_table.empty:
            print("\n" + "="*80)
            print("交易訊號明細表")
            print("="*80)
            print(signal_table.to_string(index=False))
            print(f"\n詳細資料已儲存至：trading_signals_detailed.csv")
            print(f"摘要表格已儲存至：trading_signals_summary.csv")
        
        # Display explanation
        print("\n" + "="*80)
        print("白話文分析說明")
        print("="*80)
        print(explanation)
        print(f"\n完整說明已儲存至：analysis_explanation.txt")
        
        # Display detailed analysis report
        print("\n" + "="*80)
        print("詳細觸發條件驗證報告")
        print("="*80)
        print(detailed_report)
        print(f"\n詳細報告已儲存至：detailed_analysis_report.txt")
        
        # Update master index
        self._update_master_index()
        
        return self.results

    def generate_intraday_multi_chart(self, selected_date=None, selected_stocks=None):
        """Generate intraday multi-stock chart showing price movements with clear leader-follower relationships."""
        print("Generating intraday multi-stock chart...")
        
        # Use all stocks if none specified
        if selected_stocks is None:
            selected_stocks = self.stocks
        else:
            # Add .TW suffix if not present
            selected_stocks = [s if s.endswith('.TW') else s + '.TW' for s in selected_stocks]
        
        print(f"Selected stocks: {selected_stocks}")
        if selected_date:
            print(f"Selected date: {selected_date}")
        
        # Filter data for selected date if specified
        if selected_date:
            # Handle different date formats
            if isinstance(selected_date, str):
                if len(selected_date) == 8:  # YYYYMMDD format -> YYYY/MM/DD
                    selected_date = f"{selected_date[:4]}/{selected_date[4:6]}/{selected_date[6:8]}"
                elif len(selected_date) == 10 and '-' in selected_date:  # YYYY-MM-DD format
                    selected_date = selected_date.replace('-', '/')
            
            date_data = self.data[self.data['date'] == selected_date].copy()
            if date_data.empty:
                print(f"No data available for date {selected_date}")
                print(f"Available dates: {sorted(self.data['date'].unique())[:5]}...")
                return
        else:
            # Use all available data
            date_data = self.data.copy()
        
        # Filter for selected stocks
        date_data = date_data[date_data['symbol'].isin(selected_stocks)].copy()
        
        if date_data.empty:
            print("No data available for selected stocks")
            return
        
        # Convert time to datetime for plotting
        date_data['time_str'] = date_data['time'].astype(str).str.zfill(6)
        date_data['datetime'] = pd.to_datetime(date_data['date'].astype(str) + ' ' + 
                                              date_data['time_str'].str[:2] + ':' +
                                              date_data['time_str'].str[2:4] + ':' +
                                              date_data['time_str'].str[4:6])
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12), sharex=True, 
                                      gridspec_kw={'height_ratios': [3, 1]})
        
        # Color palette for different stocks
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        # Plot each stock's price movement
        for i, stock in enumerate(selected_stocks):
            stock_data = date_data[date_data['symbol'] == stock].copy()
            if stock_data.empty:
                continue
                
            # Sort by datetime
            stock_data = stock_data.sort_values('datetime')
            
            # Use price change from CSV (already considers ex-dividend, splits, etc.)
            if len(stock_data) > 0:
                if selected_date:
                    # For single date: use the price_change_pct column directly
                    stock_data['price_change'] = stock_data['price_change_pct']
                else:
                    # For multi-date: calculate cumulative return from start of dataset  
                    first_price = stock_data['close_price'].iloc[0]
                    stock_data['price_change'] = ((stock_data['close_price'] - first_price) / first_price) * 100
            else:
                continue
            
            # Plot price line
            color = colors[i % len(colors)]
            stock_name = stock.replace('.TW', '')
            
            ax1.plot(stock_data['datetime'], stock_data['price_change'], 
                    color=color, linewidth=2.5, label=f'{stock_name}', alpha=0.8)
            
            # Add buy signals
            buy_signals = stock_data[stock_data['strong_buy_signal'] == 1]
            if not buy_signals.empty:
                ax1.scatter(buy_signals['datetime'], buy_signals['price_change'], 
                           color=color, s=150, marker='^', zorder=5, 
                           edgecolors='white', linewidth=2)
                
                # Add signal annotations
                for _, signal in buy_signals.iterrows():
                    ax1.annotate(f'{stock_name}\nBuy: {signal["close_price"]:.1f}', 
                                xy=(signal['datetime'], signal['price_change']),
                                xytext=(10, 10), textcoords='offset points',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7),
                                fontsize=9, color='white', weight='bold',
                                arrowprops=dict(arrowstyle='->', color=color, alpha=0.7))
            
            # Add sell signals
            sell_signals = stock_data[stock_data['strong_sell_signal'] == 1]
            if not sell_signals.empty:
                ax1.scatter(sell_signals['datetime'], sell_signals['price_change'], 
                           color=color, s=150, marker='v', zorder=5, 
                           edgecolors='white', linewidth=2)
        
        # Format main chart
        ax1.set_ylabel('Price Change (%)', fontsize=12, weight='bold')
        if selected_date:
            title = f'Intraday Multi-Stock Price Movement Analysis - {selected_date}\n(Leader-Follower Relationship & Time Lag)'
        else:
            title = 'Intraday Multi-Stock Price Movement Analysis\n(Leader-Follower Relationship & Time Lag)'
        ax1.set_title(title, fontsize=14, weight='bold', pad=20)
        ax1.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        
        # Add volume subplot
        for i, stock in enumerate(selected_stocks):
            stock_data = date_data[date_data['symbol'] == stock].copy()
            if stock_data.empty:
                continue
                
            stock_data = stock_data.sort_values('datetime')
            color = colors[i % len(colors)]
            stock_name = stock.replace('.TW', '')
            
            # Plot volume bars with transparency
            ax2.bar(stock_data['datetime'], stock_data['volume'], 
                   color=color, alpha=0.6, width=pd.Timedelta(minutes=0.8), 
                   label=f'{stock_name} Vol')
        
        # Format volume chart
        ax2.set_ylabel('Volume', fontsize=12, weight='bold')
        ax2.set_xlabel('Time', fontsize=12, weight='bold')
        ax2.set_title('Trading Volume', fontsize=12, weight='bold')
        ax2.legend(loc='upper right', fontsize=10, ncol=len(selected_stocks))
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis
        if selected_date:
            ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
            ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        else:
            ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%m/%d %H:%M'))
            ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%m/%d %H:%M'))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the chart
        if selected_date:
            # Replace slashes in date for filename
            safe_date = selected_date.replace('/', '_')
            filename = f'intraday_multi_chart_{safe_date}.png'
        else:
            filename = f'intraday_multi_chart_all_dates.png'
        
        output_path = self._get_output_path(filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Intraday multi-stock chart saved as: {output_path}")
        return output_path

def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description='Pair Trading Lead-Follow Analysis Tool with Industry Classification')
    parser.add_argument('--data', '-d', required=True, help='Path to CSV data file')
    parser.add_argument('--industry', '-i', default='default', help='Industry classification (e.g., security, ic_substrate)')
    parser.add_argument('--base-dir', '-b', default='/home/agi/pairTrade', help='Base directory for analysis results')
    parser.add_argument('--no-charts', action='store_true', help='Skip generating intraday charts')
    parser.add_argument('--date', help='Generate intraday chart for specific date (YYYYMMDD format)')
    parser.add_argument('--stocks', nargs='+', help='Specific stocks for analysis (e.g., 3037 8046)')
    
    args = parser.parse_args()
    
    print(f"Starting Pair Trading Analysis for Industry: {args.industry}")
    print("="*80)
    
    # Initialize and run analysis
    analyzer = PairTradeAnalyzer(args.data, industry=args.industry, base_dir=args.base_dir)
    results = analyzer.run_analysis()
    
    # Generate intraday charts if requested
    if not args.no_charts:
        print("\n" + "="*50)
        print("Generating intraday multi-stock charts...")
        print("="*50)
        
        if args.date:
            # Generate chart for specific date
            if args.stocks:
                analyzer.generate_intraday_multi_chart(selected_date=args.date, selected_stocks=args.stocks)
            else:
                analyzer.generate_intraday_multi_chart(selected_date=args.date)
        else:
            # Generate chart for available data
            if args.stocks:
                analyzer.generate_intraday_multi_chart(selected_stocks=args.stocks)
            else:
                # Default: generate chart for all stocks, latest available date
                available_dates = sorted(analyzer.data['date'].unique())
                if available_dates:
                    latest_date = available_dates[-1].replace('/', '')
                    analyzer.generate_intraday_multi_chart(selected_date=latest_date)

if __name__ == "__main__":
    main()