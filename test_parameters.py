#!/usr/bin/env python3

import pandas as pd
import numpy as np
from pathlib import Path

# Load data
df = pd.read_csv('output/IC基板/combined_data_debug.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Calculate needed indicators
df['large_total'] = df['large_buy'] + df['xlarge_buy']
df['large_net'] = (df['large_buy'] + df['xlarge_buy']) - (df['large_sell'] + df['xlarge_sell'])

# Calculate returns
df['return_1min'] = df.groupby('symbol')['close'].pct_change()

# Calculate moving averages for each stock
for symbol in df['symbol'].unique():
    mask = df['symbol'] == symbol
    df.loc[mask, 'large_total_ma30'] = df.loc[mask, 'large_total'].rolling(window=30, min_periods=1).mean()

# Calculate daily highs for each stock and date
df['daily_high'] = df.groupby(['symbol', df['datetime'].dt.date])['close'].transform('max')
df['is_daily_high'] = df['close'] >= df['daily_high']

# Calculate 30min rolling max
df['rolling_max_30min'] = df.groupby('symbol')['close'].rolling(window=30, min_periods=1).max().reset_index(0, drop=True)
df['is_30min_high'] = df['close'] >= df['rolling_max_30min']

# Test different parameters
money_multiplier = 1.3  # Lower from 1.5
min_amount = 5000000   # Lower from 10M to 5M
min_price_change = 0.003 # Lower from 0.5% to 0.3%

leader_signal = (
    (df['large_total'] > df['large_total_ma30'] * money_multiplier) & 
    (df['large_total'] > min_amount) &
    (df['large_net'] > 0) &
    (df['return_1min'] > min_price_change) &
    (df['is_daily_high'] | df['is_30min_high'])
)

print(f'使用調整後的參數:')
print(f'資金倍數: {money_multiplier}x')
print(f'最小金額: {min_amount:,}')
print(f'最小價格變化: {min_price_change*100}%')
print()

for symbol in df['symbol'].unique():
    signals = leader_signal[df['symbol'] == symbol].sum()
    print(f'{symbol.replace(".TW", "")}: 領漲信號={signals}')

print(f'總計領漲信號: {leader_signal.sum()}')

# Show some sample signals
if leader_signal.sum() > 0:
    sample_signals = df[leader_signal].head(3)
    print("\n前3個信號範例:")
    for _, signal in sample_signals.iterrows():
        print(f"  {signal['symbol']} at {signal['datetime']}: price={signal['close']:.2f}, return={signal['return_1min']*100:.2f}%, large_total={signal['large_total']/1000000:.1f}M")