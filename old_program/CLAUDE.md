# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Data Structure

This repository contains stock trading data for Taiwan stocks in CSV format.

### BigBuySell-min.csv
- **Format**: Minute-level trading data (21,000 rows)
- **Time Format**: Integer HHmmss format (e.g., 90512 = 09:05:12, needs padding to 090512)
- **Analysis Window**: 09:01:00 - 12:40:00 (day trading focus, excludes difficult late-day periods)
- **Columns** (space-separated):
  1. 股號 (Stock Symbol)
  2. 日期 (Date - YYYY/MM/DD)
  3. 時間 (Time - HHmmss integer format, may need zero-padding)
  4. 收盤價 (Close Price)
  5. 成交量 (Volume)
  6. 量比 (Volume Ratio - current/previous day)
  7. 漲跌幅 (Price Change %)
  8. 買進中單金額 (Medium Buy Orders Amount)
  9. 買進大單金額 (Large Buy Orders Amount)
  10. 買進特大單金額 (Extra Large Buy Orders Amount)
  11. 賣出中單金額 (Medium Sell Orders Amount)
  12. 賣出大單金額 (Large Sell Orders Amount)
  13. 賣出特大單金額 (Extra Large Sell Orders Amount)
  14. 買進中單金額當日累計 (Daily Cumulative Medium Buy Amount)
  15. 買進大單金額當日累計 (Daily Cumulative Large Buy Amount)
  16. 買進特大單金額當日累計 (Daily Cumulative Extra Large Buy Amount)
  17. 賣出中單金額當日累計 (Daily Cumulative Medium Sell Amount)
  18. 賣出大單金額當日累計 (Daily Cumulative Large Sell Amount)
  19. 賣出特大單金額當日累計 (Daily Cumulative Extra Large Sell Amount)

## Data Analysis Context

This contains market microstructure data for robotics industry stocks in Taiwan, focusing on institutional order flow analysis for pair trading strategies.

## Trading Strategy Objectives

### Lead-Follow Pattern Discovery
The data is used to identify leader-follower relationships among robotics stocks:

1. **Leader Stock Identification**: Stocks like 1590.TW or 2049.TW that initiate price movements with large institutional orders
2. **Follower Stock Mapping**: Other robotics stocks that follow the leader with time lag
3. **Retail Following Pattern**: When leader stocks surge with large orders, retail investors may buy second/third-tier stocks in the same sector

### Key Analysis Patterns

**Bullish Triggers** (Leader → Followers):
- Large/extra-large buy orders causing rapid price surge in leader stocks
- Leader creates daily new highs with institutional buying
- Leader creates 5-day or 10-day new highs with extra-large buy orders
- Threshold analysis: Optimal large + extra-large order amounts for successful follow-through

**Bearish Triggers** (Leader → Followers):
- Large/extra-large sell orders causing rapid decline in leader stocks  
- Leader creates daily new lows with institutional selling
- Time lag analysis between leader moves and follower responses

### Analysis Goals
- Identify which stocks act as sector leaders
- Map follower stocks and their typical response time delays
- Determine optimal thresholds for large/extra-large order amounts
- Detect momentum breakout patterns (daily/5-day/10-day highs/lows)
- Measure correlation strength between leader-follower pairs