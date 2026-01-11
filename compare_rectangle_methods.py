"""
Compare ORIGINAL vs REALTIME rectangle detection methods
Shows timing differences and classification changes
"""
from find_fractals import load_date_range
from find_rectangles import find_vwap_slope_rectangles
from find_rectangles_realtime import find_vwap_slope_rectangles_realtime
from config import START_DATE, END_DATE

print("="*80)
print("RECTANGLE DETECTION METHOD COMPARISON")
print("="*80)
print(f"Date: {START_DATE}\n")

# Load data
df = load_date_range(START_DATE, END_DATE)

if df is None:
    print("[ERROR] Could not load data")
    exit(1)

# Get rectangles from both methods
print("\n" + "-"*80)
print("ORIGINAL METHOD (wait for blue square):")
print("-"*80)
original_rects = find_vwap_slope_rectangles(df)

print("\n" + "-"*80)
print("REALTIME METHOD (close when threshold met):")
print("-"*80)
realtime_rects = find_vwap_slope_rectangles_realtime(df)

# Compare results
print("\n" + "="*80)
print("COMPARISON SUMMARY")
print("="*80)

orig_green = [r for r in original_rects if r['type'] == 'tall_narrow_up']
orig_red = [r for r in original_rects if r['type'] == 'tall_narrow_down']
orig_orange = [r for r in original_rects if r['type'] == 'consolidation']

real_green = [r for r in realtime_rects if r['type'] == 'tall_narrow_up']
real_red = [r for r in realtime_rects if r['type'] == 'tall_narrow_down']
real_orange = [r for r in realtime_rects if r['type'] == 'consolidation']

print(f"\nTotal Rectangles:")
print(f"  Original: {len(original_rects)} | Realtime: {len(realtime_rects)}")

print(f"\nGREEN Rectangles (BUY opportunities):")
print(f"  Original: {len(orig_green)} | Realtime: {len(real_green)} (+{len(real_green) - len(orig_green)})")

print(f"\nRED Rectangles (SELL opportunities):")
print(f"  Original: {len(orig_red)} | Realtime: {len(real_red)} (+{len(real_red) - len(orig_red)})")

print(f"\nORANGE Rectangles (ignored):")
print(f"  Original: {len(orig_orange)} | Realtime: {len(real_orange)} ({len(orig_orange) - len(real_orange)} converted to GREEN/RED)")

print(f"\nAverage Rectangle Duration:")
orig_avg_bars = sum(r['bars_in_range'] for r in original_rects) / len(original_rects)
real_avg_bars = sum(r['bars_in_range'] for r in realtime_rects) / len(realtime_rects)
print(f"  Original: {orig_avg_bars:.1f} bars | Realtime: {real_avg_bars:.1f} bars")
print(f"  Time saved: {orig_avg_bars - real_avg_bars:.1f} bars on average")

print(f"\nKey Benefit:")
print(f"  Realtime method captures {len(real_green) + len(real_red)} tradeable rectangles")
print(f"  vs Original method with only {len(orig_green) + len(orig_red)} tradeable rectangles")
print(f"  Improvement: +{(len(real_green) + len(real_red)) - (len(orig_green) + len(orig_red))} more trading opportunities")

print("="*80)
