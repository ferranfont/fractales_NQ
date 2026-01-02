# Price Ejection Trigger - Configuration Guide

## ⚠️ CRITICAL: Understanding Trigger Logic

### The Correct Logic

**SMALLER trigger = MORE signals**
**LARGER trigger = FEWER signals**

The trigger represents the MINIMUM distance required between price and VWAP Fast to generate a signal.

---

## 📊 Trigger Value Examples (at price ~25,500)

| Trigger Value | Percentage | Points Required | Signal Frequency |
|---------------|-----------|-----------------|------------------|
| **0.00001** | 0.001% | ~0.26 points | Very High - Almost every tick |
| **0.0001** ✅ | 0.01% | ~2.5 points | High - Recommended for tick data |
| **0.001** | 0.1% | ~25.5 points | Medium - Recommended for 1-min bars |
| **0.01** | 1.0% | ~255 points | Very Low - Rare signals only |

---

## 🎯 Recommended Settings by Data Type

### For 1-Tick Bars (Default)
```
Price Ejection Trigger: 0.0001 (0.01%)
```
**Why:** With tick data, price and SMA adjust constantly. You need a small trigger (2-3 points) to catch ejection moves.

**Example:**
- Price: 25491.25
- SMA Fast: 25492.75
- Distance: 1.5 points = 0.0059%
- With trigger 0.0001 (0.01% = 2.5 points): **NO SIGNAL** (need 2.5 pts, have 1.5 pts)
- With trigger 0.00005 (0.005% = 1.3 points): **SIGNAL!** (need 1.3 pts, have 1.5 pts) ✅

### For 1-Minute Bars
```
Price Ejection Trigger: 0.001 (0.1%)
```
**Why:** 1-minute bars have larger price moves and SMA updates less frequently. You can use a larger trigger (25 points) to filter noise.

### For 5-Minute Bars
```
Price Ejection Trigger: 0.005 (0.5%)
```
**Why:** Longer timeframes have even larger moves. Larger trigger filters out minor retracements.

---

## 🔍 Troubleshooting: No Signals

### Problem: Strategy runs but no entries

**Check 1: Is trigger TOO LARGE?**
```
Output shows: "Distance: 0.0059%" but no GREEN/RED DOT SIGNAL
Current trigger: 0.001 (0.1%)

Solution: DECREASE trigger to 0.0001 (0.01%) or lower
```

**Check 2: Calculate required distance**
```python
# At price 25,500
Trigger 0.001 (0.1%) = 25,500 × 0.001 = 25.5 points required
Trigger 0.0001 (0.01%) = 25,500 × 0.0001 = 2.55 points required
Trigger 0.00001 (0.001%) = 25,500 × 0.00001 = 0.255 points required
```

**Check 3: Compare with actual distance**
Look at NinjaTrader Output:
```
Price: 25491.25 | SMA Fast: 25492.75
Distance: |25491.25 - 25492.75| = 1.5 points = 0.0059%

0.0059% > 0.001 (0.1%)? NO → No signal ❌
0.0059% > 0.0001 (0.01%)? NO → No signal ❌
0.0059% > 0.00001 (0.001%)? YES → Signal! ✅
```

---

## 🧪 Testing Different Trigger Values

### Step 1: Enable Debug Output
The strategy already has debug prints enabled. Check NinjaTrader Output Window for:
```
Bar 296500 | Time: ... | Price: 25491.25 | SMA Fast: 25492.75 | SMA Slow: 25491.22
```

### Step 2: Test with Very Small Trigger
```
Set: Price Ejection Trigger = 0.00001 (0.001%)
Run: Strategy on 1-tick chart
Expect: MANY signals (possibly too many)
```

### Step 3: Gradually Increase
```
Test sequence:
0.00001 → Too many signals?
0.00005 → Still too many?
0.0001 → Good balance? ✅
0.0005 → Too few signals?
```

### Step 4: Find Your Sweet Spot
- **Too many signals:** Market noise, overtrading → INCREASE trigger
- **Too few signals:** Missing good moves → DECREASE trigger
- **Just right:** Clear ejection moves only → Keep this value

---

## 📋 Common Mistakes

### ❌ WRONG: "Trigger is too small, let's increase it"
```
Current: 0.001 (no signals)
Wrong fix: 0.01 (even FEWER signals!)
Correct fix: 0.0001 (MORE signals) ✅
```

### ❌ WRONG: "Use same trigger for all timeframes"
```
1-tick bars: Need 0.0001
1-min bars: Need 0.001
5-min bars: Need 0.005

Same trigger won't work for all!
```

### ❌ WRONG: "Set trigger to 0 to get all signals"
```
Trigger 0 = Trade every tick (not useful)
Need SOME filtering to catch actual ejections
```

---

## 🎓 Advanced: Optimal Trigger by Volatility

### High Volatility Days (VIX > 20)
```
Use LARGER trigger (0.001-0.005)
Why: Larger moves, filter noise
```

### Low Volatility Days (VIX < 15)
```
Use SMALLER trigger (0.0001-0.0005)
Why: Smaller moves, catch subtle ejections
```

### Dynamic Trigger (Future Enhancement)
```csharp
// Calculate ATR-based trigger
double atr = ATR(14)[0];
double dynamicTrigger = atr / Close[0];  // ATR as % of price
```

---

## 📊 Default Configuration (Updated)

```csharp
// In NinjaTrader strategy defaults
PriceEjectionTrigger = 0.0001;  // 0.01% - optimized for tick data

// For tick data: Start here and adjust
// For 1-min bars: Use 0.001 (0.1%)
// For 5-min bars: Use 0.005 (0.5%)
```

---

## 🔗 Related Parameters

The trigger works together with:

1. **VWAP Fast Period** (default 100)
   - Shorter period → SMA moves faster → may need smaller trigger
   - Longer period → SMA smoother → may need larger trigger

2. **Trend Filter** (UseTrendFilter)
   - If enabled: Fewer signals (adds extra filter)
   - If disabled: More signals (only ejection check)

3. **Trading Hours** + **Hour Filter**
   - Limit when signals can occur
   - Doesn't change trigger sensitivity, just blocks certain hours

---

## ✅ Summary

**Key Principle:** The trigger is a MINIMUM threshold, not a maximum.

- Price must move **AT LEAST** this percentage away from VWAP Fast
- **SMALLER** trigger = easier to meet threshold = MORE signals
- **LARGER** trigger = harder to meet threshold = FEWER signals

**For your tick data with 1.5 point typical moves:**
- Use **0.0001** (0.01%) = requires 2.5 points → some signals
- Use **0.00005** (0.005%) = requires 1.3 points → more signals
- Use **0.00001** (0.001%) = requires 0.25 points → many signals

**Start with 0.0001 and adjust based on results.**

---

**Version:** 1.0
**Date:** 2026-01-02
**Updated by:** Claude Code
**Related File:** AAvwap_momentum.cs
