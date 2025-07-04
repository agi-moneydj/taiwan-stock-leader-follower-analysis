#!/usr/bin/env python3
"""
Sector Analysis Tool
Analyzes leader-follower relationships in sector stocks based on institutional order flow.
Converts TXT data files to BigBuySell-min.csv format and applies pair trading analysis.
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
import sys
from pathlib import Path
import glob
warnings.filterwarnings('ignore')

class SectorAnalyzer:
    def __init__(self, start_period, end_period, sector, base_dir=None):
        """Initialize sector analyzer with date range and sector."""
        self.start_period = start_period  # YYYYMM format
        self.end_period = end_period      # YYYYMM format
        self.sector = sector              # DJ_IC基板 format
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.csv_dir = self.base_dir / "csv"
        self.sector_info_dir = self.base_dir / "sectorInfo"
        self.output_dir = self.base_dir / "output" / sector.replace("DJ_", "")
        
        self.sector_stocks = []
        self.combined_data = None
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
            # Find all txt files for this month
            for stock in self.sector_stocks:
                stock_dir = self.csv_dir / stock
                if stock_dir.exists():
                    pattern = f"Min_{current_year:04d}{current_month:02d}*.txt"
                    files = list(stock_dir.glob(pattern))
                    for file in files:
                        # Extract date from filename like Min_20250630.txt
                        date_str = file.stem.split('_')[1]  # Gets 20250630
                        if date_str not in dates:
                            dates.append(date_str)
            
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        dates.sort()
        print(f"Found {len(dates)} trading dates in range {self.start_period}-{self.end_period}")
        return dates
    
    def read_min_data(self, stock, date):
        """Read minute K-line data from Min_YYYYMMDD.txt file."""
        stock_dir = self.csv_dir / stock
        min_file = stock_dir / f"Min_{date}.txt"
        
        if not min_file.exists():
            return None
        
        try:
            # Read the file, skip the header line
            df = pd.read_csv(min_file, skiprows=1, header=None)
            df.columns = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Pattern', 'IsReal']
            
            # Add stock symbol
            df['symbol'] = f"{stock}.TW"
            
            # Create datetime column
            df['datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + 
                                          df['Time'].astype(str).str.zfill(6), 
                                          format='%Y%m%d %H%M%S')
            
            return df
        except Exception as e:
            print(f"Error reading {min_file}: {e}")
            return None
    
    def read_tamin_data(self, stock, date):
        """Read TA minute data from TAMin_YYYYMMDD.txt file."""
        stock_dir = self.csv_dir / stock
        tamin_file = stock_dir / f"TAMin_{date}.txt"
        
        if not tamin_file.exists():
            return None
        
        try:
            # Read the file, skip the header line
            df = pd.read_csv(tamin_file, skiprows=1, header=None)
            
            # Parse header to get field names
            with open(tamin_file, 'r') as f:
                header_line = f.readline().strip()
            
            # Extract field names from header
            field_start = header_line.find('Field=') + 6
            field_end = header_line.find(';', field_start)
            if field_end == -1:
                field_names = header_line[field_start:].split(',')
            else:
                field_names = header_line[field_start:field_end].split(',')
            
            df.columns = field_names
            
            # Create datetime column
            df['datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + 
                                          df['Time'].astype(str).str.zfill(6), 
                                          format='%Y%m%d %H%M%S')
            
            return df
        except Exception as e:
            print(f"Error reading {tamin_file}: {e}")
            return None
    
    def convert_to_bigbuysell_format(self, stock, date):
        """Convert Min and TAMin data to BigBuySell-min.csv format."""
        min_data = self.read_min_data(stock, date)
        tamin_data = self.read_tamin_data(stock, date)
        
        if min_data is None or tamin_data is None:
            return None
        
        try:
            # Merge data on datetime
            merged = pd.merge(min_data, tamin_data, on='datetime', suffixes=('_min', '_ta'))
            
            # Calculate price change percentage
            prev_close = merged['Close'].iloc[0]  # Use first close as reference
            merged['price_change_pct'] = ((merged['Close'] - prev_close) / prev_close) * 100
            
            # Calculate volume ratio (simplified as current/first volume)
            first_volume = merged['Volume'].iloc[0]
            merged['volume_ratio'] = merged['Volume'] / first_volume if first_volume > 0 else 1.0
            
            # Create BigBuySell format DataFrame
            result = pd.DataFrame()
            result['symbol'] = merged['symbol']
            result['date'] = merged['Date_min'].apply(lambda x: f"{str(x)[:4]}/{str(x)[4:6]}/{str(x)[6:]}")
            result['time'] = merged['Time_min']
            result['close'] = merged['Close']
            result['volume'] = merged['Volume']
            result['volume_ratio'] = merged['volume_ratio']
            result['price_change_pct'] = merged['price_change_pct']
            
            # Map order flow data (TAMin columns to BigBuySell columns)
            result['medium_buy'] = merged.get('DMOrderInValue', 0.0)        # 買進中單金額
            result['large_buy'] = merged.get('DLOrderInValue', 0.0)         # 買進大單金額  
            result['xlarge_buy'] = merged.get('DXLOrderInValue', 0.0)       # 買進特大單金額
            result['medium_sell'] = merged.get('DMOrderOutValue', 0.0)      # 賣出中單金額
            result['large_sell'] = merged.get('DLOrderOutValue', 0.0)       # 賣出大單金額
            result['xlarge_sell'] = merged.get('DXLOrderOutValue', 0.0)     # 賣出特大單金額
            
            # Calculate cumulative values (daily cumulative)
            result['medium_buy_cum'] = result['medium_buy'].cumsum()
            result['large_buy_cum'] = result['large_buy'].cumsum()
            result['xlarge_buy_cum'] = result['xlarge_buy'].cumsum()
            result['medium_sell_cum'] = result['medium_sell'].cumsum()
            result['large_sell_cum'] = result['large_sell'].cumsum()
            result['xlarge_sell_cum'] = result['xlarge_sell'].cumsum()
            
            # Add datetime for analysis
            result['datetime'] = merged['datetime']
            
            return result
            
        except Exception as e:
            print(f"Error converting data for {stock} on {date}: {e}")
            return None
    
    def load_all_data(self):
        """Load and convert all data for the sector and date range."""
        print("Loading and converting data...")
        
        dates = self.generate_date_range()
        all_data = []
        
        for date in dates:
            print(f"Processing date: {date}")
            daily_data = []
            
            for stock in self.sector_stocks:
                stock_data = self.convert_to_bigbuysell_format(stock, date)
                if stock_data is not None:
                    daily_data.append(stock_data)
            
            if daily_data:
                all_data.extend(daily_data)
        
        if all_data:
            self.combined_data = pd.concat(all_data, ignore_index=True)
            self.combined_data = self.combined_data.sort_values(['datetime', 'symbol']).reset_index(drop=True)
            print(f"Combined data shape: {self.combined_data.shape}")
            
            # Save combined data for debugging
            debug_file = self.output_dir / "combined_data_debug.csv"
            self.combined_data.to_csv(debug_file, index=False)
            print(f"Debug data saved to: {debug_file}")
            
        else:
            print("No data found for the specified period and sector.")
            return False
        
        return True
    
    def calculate_signals(self):
        """Calculate buy/sell signals based on order flow."""
        print("Calculating trading signals...")
        
        if self.combined_data is None:
            return
        
        df = self.combined_data.copy()
        
        # Calculate 1-minute returns
        df['return_1min'] = df.groupby('symbol')['close'].pct_change()
        
        # Define signal thresholds (can be adjusted)
        large_threshold = 1000000    # 100万
        xlarge_threshold = 5000000   # 500万
        
        # Strong buy signals: Large institutional buying
        df['strong_buy_signal'] = (
            (df['large_buy'] > large_threshold) | 
            (df['xlarge_buy'] > xlarge_threshold)
        ) & (df['return_1min'] > 0.005)  # with positive price movement
        
        # Strong sell signals: Large institutional selling  
        df['strong_sell_signal'] = (
            (df['large_sell'] > large_threshold) |
            (df['xlarge_sell'] > xlarge_threshold)
        ) & (df['return_1min'] < -0.005)  # with negative price movement
        
        self.combined_data = df
        
        # Print signal statistics
        total_buy_signals = df['strong_buy_signal'].sum()
        total_sell_signals = df['strong_sell_signal'].sum()
        print(f"Generated {total_buy_signals} buy signals and {total_sell_signals} sell signals")
        
        return df
    
    def analyze_leader_follower(self, max_lag_minutes=30):
        """Analyze leader-follower relationships with time lags."""
        print("Analyzing leader-follower relationships...")
        
        if self.combined_data is None:
            print("No data available for analysis.")
            return
        
        stocks = [f"{stock}.TW" for stock in self.sector_stocks]
        correlations = {}
        
        for leader in stocks:
            correlations[leader] = {}
            leader_data = self.combined_data[self.combined_data['symbol'] == leader].set_index('datetime')
            
            if leader_data.empty:
                continue
                
            # Get leader signals
            leader_buy_times = leader_data[leader_data['strong_buy_signal']].index
            leader_sell_times = leader_data[leader_data['strong_sell_signal']].index
            
            if len(leader_buy_times) == 0 and len(leader_sell_times) == 0:
                continue
                
            for follower in stocks:
                if leader == follower:
                    continue
                    
                follower_data = self.combined_data[self.combined_data['symbol'] == follower].set_index('datetime')
                
                if follower_data.empty:
                    continue
                
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
                
                # Store correlation results
                if buy_responses or sell_responses:
                    correlations[leader][follower] = {
                        'buy_responses': len(buy_responses),
                        'sell_responses': len(sell_responses),
                        'buy_success_rate': len(buy_responses) / max(len(leader_buy_times), 1),
                        'sell_success_rate': len(sell_responses) / max(len(leader_sell_times), 1),
                        'avg_buy_lag': np.mean([r['lag'] for r in buy_responses]) if buy_responses else 0,
                        'avg_sell_lag': np.mean([r['lag'] for r in sell_responses]) if sell_responses else 0,
                        'avg_buy_return': np.mean([r['return'] for r in buy_responses]) if buy_responses else 0,
                        'avg_sell_return': np.mean([r['return'] for r in sell_responses]) if sell_responses else 0,
                    }
        
        self.results['correlations'] = correlations
        
        # Analyze leadership rankings
        leadership_scores = {}
        for leader in stocks:
            if leader in correlations:
                total_followers = len([f for f in correlations[leader] if correlations[leader][f]['buy_success_rate'] > 0.1])
                avg_success_rate = np.mean([correlations[leader][f]['buy_success_rate'] 
                                          for f in correlations[leader] if correlations[leader][f]['buy_success_rate'] > 0])
                leadership_scores[leader] = total_followers * avg_success_rate
        
        sorted_leaders = sorted(leadership_scores.items(), key=lambda x: x[1], reverse=True)
        self.results['leadership_analysis'] = {
            'leaders': sorted_leaders,
            'followers': []  # Will be populated in generate_analysis_summary
        }
        
        print(f"Analysis complete. Found correlations for {len(correlations)} potential leaders.")
        return correlations
    
    def generate_analysis_summary(self):
        """Generate text summary of the analysis."""
        print("Generating analysis summary...")
        
        summary_lines = []
        summary_lines.append(f"=== SECTOR ANALYSIS SUMMARY ===")
        summary_lines.append(f"Sector: {self.sector}")
        summary_lines.append(f"Period: {self.start_period} - {self.end_period}")
        summary_lines.append(f"Stocks Analyzed: {len(self.sector_stocks)}")
        summary_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        if 'correlations' in self.results:
            correlations = self.results['correlations']
            leadership = self.results.get('leadership_analysis', {})
            
            # Leadership rankings
            leaders = leadership.get('leaders', [])
            summary_lines.append("=== TOP SECTOR LEADERS ===")
            for i, (leader, score) in enumerate(leaders[:5]):
                leader_clean = leader.replace('.TW', '')
                summary_lines.append(f"{i+1}. {leader_clean} (Leadership Score: {score:.3f})")
            
            summary_lines.append("")
            summary_lines.append("=== LEADER-FOLLOWER RELATIONSHIPS ===")
            
            # Show top relationships
            all_relationships = []
            for leader in correlations:
                for follower in correlations[leader]:
                    rel = correlations[leader][follower]
                    if rel['buy_success_rate'] > 0.1:  # Minimum threshold
                        all_relationships.append({
                            'leader': leader.replace('.TW', ''),
                            'follower': follower.replace('.TW', ''),
                            'success_rate': rel['buy_success_rate'],
                            'avg_lag': rel['avg_buy_lag'],
                            'avg_return': rel['avg_buy_return']
                        })
            
            # Sort by success rate
            all_relationships.sort(key=lambda x: x['success_rate'], reverse=True)
            
            for rel in all_relationships[:10]:  # Top 10
                summary_lines.append(
                    f"{rel['leader']} -> {rel['follower']}: "
                    f"Success Rate={rel['success_rate']:.2%}, "
                    f"Avg Lag={rel['avg_lag']:.1f}min, "
                    f"Avg Return={rel['avg_return']:.2%}"
                )
        
        summary_text = "\n".join(summary_lines)
        
        # Save summary
        summary_file = self.output_dir / "analysis_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        print(f"Analysis summary saved to: {summary_file}")
        print("\n" + summary_text)
        
        return summary_text
    
    def generate_charts(self):
        """Generate visualization charts."""
        print("Generating charts...")
        
        if 'correlations' not in self.results:
            print("No correlation data available for chart generation.")
            return
        
        correlations = self.results['correlations']
        stocks = [f"{stock}.TW" for stock in self.sector_stocks]
        
        # Create success rate matrix
        n_stocks = len(stocks)
        success_matrix = np.zeros((n_stocks, n_stocks))
        
        for i, leader in enumerate(stocks):
            for j, follower in enumerate(stocks):
                if leader != follower and leader in correlations and follower in correlations[leader]:
                    success_rate = correlations[leader][follower]['buy_success_rate']
                    success_matrix[i][j] = success_rate
        
        # Generate heatmap
        plt.figure(figsize=(12, 10))
        stock_labels = [s.replace('.TW', '') for s in stocks]
        
        sns.heatmap(success_matrix, 
                   xticklabels=stock_labels, 
                   yticklabels=stock_labels,
                   annot=True, 
                   fmt='.2f', 
                   cmap='Reds',
                   cbar_kws={'label': 'Success Rate'})
        
        plt.title(f'Leader-Follower Success Rates - {self.sector}\n(Leader=Y-axis, Follower=X-axis)')
        plt.xlabel('Follower Stock')
        plt.ylabel('Leader Stock')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        chart_file = self.output_dir / "leader_follower_analysis.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Chart saved to: {chart_file}")
        
        return chart_file
    
    def run_analysis(self):
        """Run the complete sector analysis."""
        print(f"Starting sector analysis for {self.sector}")
        print(f"Period: {self.start_period} to {self.end_period}")
        
        try:
            # Step 1: Load sector stocks
            self.load_sector_stocks()
            
            # Step 2: Load and convert all data
            if not self.load_all_data():
                print("Failed to load data. Analysis terminated.")
                return False
            
            # Step 3: Calculate signals
            self.calculate_signals()
            
            # Step 4: Run leader-follower analysis
            self.analyze_leader_follower()
            
            # Step 5: Generate summary and charts
            self.generate_analysis_summary()
            self.generate_charts()
            
            print(f"\n=== ANALYSIS COMPLETE ===")
            print(f"Results saved to: {self.output_dir}")
            
            return True
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='Sector Analysis Tool')
    parser.add_argument('--start', required=True, help='Start period (YYYYMM format, e.g., 202605)')
    parser.add_argument('--end', required=True, help='End period (YYYYMM format, e.g., 202606)')
    parser.add_argument('--sector', required=True, help='Sector name (e.g., DJ_IC基板)')
    parser.add_argument('--base-dir', help='Base directory path (default: current directory)')
    
    args = parser.parse_args()
    
    analyzer = SectorAnalyzer(
        start_period=args.start,
        end_period=args.end,
        sector=args.sector,
        base_dir=args.base_dir
    )
    
    success = analyzer.run_analysis()
    
    if success:
        print("Analysis completed successfully!")
        sys.exit(0)
    else:
        print("Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()