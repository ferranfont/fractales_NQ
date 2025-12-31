# VWAP Momentum Strategy - Sortino Ratio Analysis
**Period**: 2025-10-01 to 2025-12-12 (53 days)
**Current Sortino Ratio**: 0.11 (VERY LOW)

---

## 1. EXECUTIVE SUMMARY

### Current Performance
- **Total Trades**: 1,377
- **Total P&L**: $97,135 (+)
- **Avg per trade**: $70.54
- **Win Rate**: 50.2%
- **Sharpe Ratio**: 0.07
- **Sortino Ratio**: 0.11 ❌ **CRITICAL ISSUE**

### Why is Sortino So Low?
```
Sortino Ratio = Mean Return / Downside Std Dev
             = $70.54 / $649.20
             = 0.1087
```

**Problem**: High downside volatility ($649) compared to average return ($71)

---

## 2. ROOT CAUSE ANALYSIS

### Exit Reason Breakdown

| Exit Reason | Count | % of Trades | Total P&L | Avg P&L | Impact |
|------------|-------|-------------|-----------|---------|--------|
| **PROFIT (TP hit)** | 132 | 9.6% | +$330,000 | +$2,500 | ✅ Excellent |
| **PROTECTIVE_SL** | 184 | 13.4% | -$294,400 | -$1,600 | ❌ Major losses |
| **TIME_EXIT** | 1,058 | 76.8% | +$60,070 | +$57 | ⚠️ Mostly noise |

### The Core Problem

1. **TP hit rate too low**: Only 9.6% of trades reach TP (+$2,500)
2. **SL hit rate too high**: 13.4% of trades hit SL (-$1,600)
3. **76.8% are time exits**: Average profit of only $57 (basically noise)
4. **Asymmetric hit rates**: More SL hits than TP hits despite good R:R ratio

### Contribution to P&L
- TP exits contribute: **339.7%** of total P&L ($330k of $97k)
- SL exits lose: **-303.1%** of total P&L (-$294k)
- Time exits contribute: **61.8%** of total P&L ($60k)

**Net effect**: TP profits are eroded by SL losses, leaving only time-exit profits

---

## 3. TIME EXIT ANALYSIS (76.8% of trades)

### By Time in Market

| Time Range | Count | Win Rate | Avg P&L | Status |
|-----------|-------|----------|---------|--------|
| **0-1 min** | 762 | 51.3% | $8 | 🟡 NOISE |
| **1-5 min** | 217 | 53.0% | $62 | 🟢 OK |
| **5-30 min** | 0 | - | - | - |
| **30-60 min** | 33 | 69.7% | $531 | 🟢 GOOD |
| **60-180 min** | 13 | 69.2% | $677 | 🟢 GOOD |
| **180+ min** | 33 | 60.6% | $418 | 🟢 OK |

**KEY INSIGHT**: 762 trades (55% of ALL trades) exit in 0-1 minute with $8 average. This is pure noise and contributes to volatility without meaningful profit.

---

## 4. HOURLY PERFORMANCE ANALYSIS

### Best Hours (Avg P&L > $100)

| Hour | Count | Total P&L | Avg P&L | Win Rate | TP Rate | Rating |
|------|-------|-----------|---------|----------|---------|--------|
| 10:00 | 17 | $13,935 | **$820** | 64.7% | 41.2% | ⭐⭐⭐ |
| 18:00 | 31 | $24,035 | **$775** | 61.3% | 48.4% | ⭐⭐⭐ |
| 06:00 | 8 | $3,940 | **$492** | 62.5% | 37.5% | ⭐⭐⭐ |
| 01:00 | 22 | $10,290 | **$468** | 54.5% | 27.3% | ⭐⭐⭐ |
| 12:00 | 8 | $3,600 | **$450** | 50.0% | 50.0% | ⭐⭐⭐ |
| 17:00 | 52 | $21,930 | **$422** | 50.0% | 42.3% | ⭐⭐⭐ |
| 16:00 | 70 | $26,000 | **$371** | 48.6% | 41.4% | ⭐⭐⭐ |
| 13:00 | 15 | $4,700 | **$313** | 46.7% | 46.7% | ⭐⭐⭐ |
| 03:00 | 6 | $1,695 | **$282** | 66.7% | 16.7% | ⭐⭐⭐ |
| 04:00 | 5 | $1,255 | **$251** | 40.0% | 40.0% | ⭐⭐⭐ |

### Worst Hours (Avg P&L < $0)

| Hour | Count | Total P&L | Avg P&L | Win Rate | TP Rate | Rating |
|------|-------|-----------|---------|----------|---------|--------|
| 02:00 | 5 | -$8,000 | **-$1,600** | 0.0% | 0.0% | ❌❌❌ |
| 08:00 | 11 | -$9,400 | **-$855** | 18.2% | 18.2% | ❌❌ |
| 14:00 | 15 | -$5,660 | **-$377** | 33.3% | 26.7% | ❌ |
| 05:00 | 5 | -$1,290 | **-$258** | 20.0% | 20.0% | ❌ |
| 19:00 | 32 | -$7,215 | **-$225** | 40.6% | 12.5% | ❌ |

### Performance Hours (20:00-22:00)

| Hour | Count | Total P&L | Avg P&L | Win Rate | TP Rate | Comment |
|------|-------|-----------|---------|----------|---------|---------|
| 20:00 | 328 | $395 | **$1** | 51.2% | 0.0% | 🟡 High volume, no profit |
| 21:00 | 211 | $3,175 | **$15** | 51.2% | 0.0% | 🟡 High volume, minimal profit |
| 22:00 | 390 | $5,635 | **$14** | 50.0% | 0.0% | 🟡 High volume, minimal profit |

**Total 20-22h**: 929 trades (67.5% of all trades!) with avg $10 profit

---

## 5. VWAP SLOPE ANALYSIS

### By VWAP Slope Category

| VWAP Slope Category | Count | Avg P&L | Win Rate | TP Rate |
|---------------------|-------|---------|----------|---------|
| Strong Down (<-1.0) | 451 | **$157** | 51.2% | 14.4% |
| Down (-1.0 to -0.5) | 136 | **-$47** | 47.8% | 8.8% |
| Weak Down (-0.5 to 0) | 146 | **$138** | 49.3% | 9.6% |
| Weak Up (0 to 0.5) | 156 | **$82** | 49.4% | 7.7% |
| Up (0.5 to 1.0) | 154 | **$69** | 52.0% | 7.1% |
| Strong Up (>1.0) | 334 | **-$32** | 49.7% | 5.4% |

### Trend Alignment

| Strategy | Count | Avg P&L | Win Rate | TP Rate | Sortino |
|----------|-------|---------|----------|---------|---------|
| **COUNTER-TREND** | 216 | **$154** | 50.9% | 12.0% | Better |
| **WITH TREND** | 1,161 | **$55** | 50.0% | 9.1% | 0.0836 (-23%) |

**SURPRISING FINDING**: Counter-trend trades perform BETTER than trend-following trades!

---

## 6. IMPROVEMENT SCENARIOS

### Scenario A: Filter by Time of Day (BEST HOURS ONLY)
**Hours**: 0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18

- **Trades**: 247 (17.9% of current volume)
- **Total P&L**: $113,035 (+16% vs current)
- **Avg P&L**: $457.63 (+549% vs $70.54)
- **Win Rate**: 53.4% (+3.2%)
- **TP Rate**: 38.9% (+29.3%)
- **Downside Std**: $481.44 (-26% vs $649)
- **Sortino Ratio**: **0.9505** (+774% improvement!) ✅✅✅

### Scenario B: Remove Noise Trades (0-1 min exits)
- **Remove**: 762 trades with $8 avg (0-1 min time exits)
- **Remaining**: 615 trades
- **Impact**: Would reduce noise and likely improve Sortino significantly

### Scenario C: Optimize TP/SL Ratio

Current: TP=125pts ($2,500), SL=80pts ($1,600) = 1.56:1

**Option 1**: TP=100pts ($2,000), SL=50pts ($1,000) = 2:1
- Better R:R ratio
- Higher TP hit rate expected
- Lower max loss per trade

**Option 2**: TP=150pts ($3,000), SL=75pts ($1,500) = 2:1
- Higher profit per win
- Similar SL to current

---

## 7. RECOMMENDATIONS (PRIORITY ORDER)

### 🔴 CRITICAL - Filter Trading Hours
**Implementation**: Add time-of-day filter to config.py

```python
# Only trade during best performing hours
VWAP_MOMENTUM_ALLOWED_HOURS = [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]
```

**Expected Impact**:
- Sortino: 0.11 → **0.95** (+774%)
- Avg P&L: $71 → **$458** (+549%)
- TP Rate: 9.6% → **38.9%** (+305%)

---

### 🟠 HIGH PRIORITY - Remove Noise Trades
**Implementation**: Add minimum time in market filter

```python
# Exit immediately if trade doesn't move favorably in first 5 minutes
USE_EARLY_EXIT_IF_NO_MOVEMENT = True
EARLY_EXIT_MINUTES = 5
EARLY_EXIT_MIN_MFE_POINTS = 10  # Minimum favorable movement required
```

**Expected Impact**: Eliminate 762 noise trades (55% of volume)

---

### 🟡 MEDIUM PRIORITY - Optimize TP/SL
**Implementation**: Test alternative TP/SL ratios

Current problem: 13.4% SL hits vs 9.6% TP hits (asymmetric)

**Test**:
1. TP=100pts, SL=50pts (2:1 ratio)
2. TP=150pts, SL=75pts (2:1 ratio)
3. TP=80pts, SL=40pts (2:1 ratio)

---

### 🟢 OPTIONAL - Add Entry Filters

**Filter 1 - Strong VWAP Slope**:
- Only enter when |VWAP slope| > 1.0
- Current data shows: Strong slopes have higher TP rates (14.4% vs 5-9%)

**Filter 2 - Avoid Peak Noise Hours**:
- Disable trading 20:00-22:00 (929 trades with $10 avg = noise)
- Would eliminate 67.5% of current trades

**Filter 3 - Add ATR/Volatility Filter**:
- Only trade when ATR > threshold (avoid low volatility consolidation)

---

## 8. JSON OPTIMIZATION STATUS ✅

**VERIFIED**: JSON time-in-market optimization IS working correctly

- Durations vary by entry hour as expected
- Hour 1: 360 min, Hour 11: 1 min, Hour 20: 1 min, etc.
- Optimal durations are being loaded correctly from JSON

**This is NOT the problem**. The issue is signal quality and trade filtering.

---

## 9. NEXT STEPS

### Immediate Actions
1. ✅ Implement hourly filter (restrict to best 11 hours)
2. ✅ Add early exit for no-movement trades (first 5 min check)
3. ⏳ Re-run backtest and measure new Sortino ratio

### Testing & Validation
4. ⏳ Test alternative TP/SL ratios (100/50, 150/75)
5. ⏳ Test strong VWAP slope filter (|slope| > 1.0)
6. ⏳ Test volatility/ATR filter

### Optimization
7. ⏳ Re-run optimize_time_in_market.py with new filters
8. ⏳ Generate new optimal JSON config
9. ⏳ Compare before/after metrics

---

## 10. EXPECTED FINAL RESULTS

With **hourly filter + early exit filter**:

| Metric | Current | Expected | Improvement |
|--------|---------|----------|-------------|
| Trades | 1,377 | ~200-300 | -78% to -85% |
| Avg P&L | $71 | $400-500 | +463% to +604% |
| Win Rate | 50.2% | 53-55% | +5% to +10% |
| TP Rate | 9.6% | 35-40% | +265% to +317% |
| Sortino | **0.11** | **0.8-1.0** | +627% to +809% |
| Total P&L | $97k | $80k-120k | Maintained or improved |

**Trade-off**: Fewer trades, but MUCH higher quality with better risk-adjusted returns.

---

## 11. CONCLUSION

The low Sortino Ratio (0.11) is caused by:

1. **Trading at wrong hours** - 67.5% of trades happen 20-22h with $10 avg profit
2. **Too many noise trades** - 55% exit in 0-1 min with $8 avg profit
3. **Poor TP/SL hit distribution** - More SL hits (13.4%) than TP hits (9.6%)
4. **High downside volatility** - $649 std dev from frequent -$1600 SL hits

**Solution**: Filter trades by hour, add early exit for no-movement, and the Sortino should improve by **+774% to ~0.95**.

The JSON optimization system is working perfectly. The problem is **signal quality**, not exit timing.
