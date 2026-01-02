#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.Core.FloatingPoint;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.DrawingTools;
#endregion

//This namespace holds Strategies in this folder and is required. Do not change it.
namespace NinjaTrader.NinjaScript.Strategies
{
	public class AAvwap_momentum : Strategy
	{
		#region Variables
		// VWAP Indicators
		private VWAP vwapFast;
		private VWAP vwapSlow;

		// Entry signals
		private bool greenDotSignal = false;
		private bool redDotSignal = false;

		// Position tracking
		private double entryPrice = 0;
		private double mainPositionStopLoss = 0; // SL level shared by all grid positions

		// Grid tracking
		private List<string> gridOrderNames = new List<string>();
		private int gridOrderCounter = 0;

		// Hour filter tracking
		private HashSet<int> excludedHours = new HashSet<int>();
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description									= @"Simple VWAP Momentum Strategy - Green/Red Dot Entries with Fixed TP/SL";
				Name										= "AAvwap_momentum";
				Calculate									= Calculate.OnBarClose;
				EntriesPerDirection							= 1;
				EntryHandling								= EntryHandling.AllEntries;
				IsExitOnSessionCloseStrategy				= true;
				ExitOnSessionCloseSeconds					= 30;
				IsFillLimitOnTouch							= false;
				MaximumBarsLookBack							= MaximumBarsLookBack.TwoHundredFiftySix;
				OrderFillResolution							= OrderFillResolution.Standard;
				Slippage									= 0;
				StartBehavior								= StartBehavior.WaitUntilFlat;
				TimeInForce									= TimeInForce.Gtc;
				TraceOrders									= false;
				RealtimeErrorHandling						= RealtimeErrorHandling.StopCancelClose;
				StopTargetHandling							= StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade							= 20;
				IsInstantiatedOnEachOptimizationIteration	= true;

				// Strategy Parameters (from config.py)
				VwapFastPeriod		= 100;		// VWAP_FAST
				VwapSlowPeriod		= 200;		// VWAP_SLOW
				TakeProfitPoints	= 125;		// VWAP_MOMENTUM_TP_POINTS
				StopLossPoints		= 75;		// VWAP_MOMENTUM_SL_POINTS (UPDATED TO MATCH CURRENT CONFIG)
				PriceEjectionTrigger = 0.001;	// PRICE_EJECTION_TRIGGER (0.1%)
				UseTrendFilter		= true;		// USE_VWAP_SLOW_TREND_FILTER
				AllowLong			= true;		// VWAP_MOMENTUM_LONG_ALLOWED
				AllowShort			= true;		// VWAP_MOMENTUM_SHORT_ALLOWED

				// Trading Hours (default 24h, adjust as needed)
				StartHour			= 0;
				StartMinute			= 0;
				EndHour				= 22;
				EndMinute			= 59;

				// Grid Entry System
				UseGridEntry		= false;	// USE_ENTRY_GRID
				GridStepPoints		= 60;		// GRID_STEP (distance between grid levels in points)
				NumberOfGridSteps	= 1;		// NUMBER_OF_GRID_STEPS (number of additional limit orders)

				// Close All Trades at Specific Time
				UseCloseAllAtTime	= false;	// Enable auto-close at specific time
				CloseAllHour		= 22;		// Hour to close all positions (0-23)
				CloseAllMinute		= 0;		// Minute to close all positions (0-59)

				// Hour Filter (Avoid Trading During Specific Hours)
				UseHourFilter		= false;	// Enable hour exclusion filter
				ExcludedHoursString	= "0,5,23";	// Comma-separated list of hours to exclude (e.g., "0,5,23" = avoid 00:xx, 05:xx, 23:xx)
			}
			else if (State == State.Configure)
			{
				// Parse excluded hours string into HashSet
				ParseExcludedHours();
			}
			else if (State == State.DataLoaded)
			{
				// Initialize VWAP indicators
				vwapFast = VWAP(Close, VwapFastPeriod);
				vwapSlow = VWAP(Close, VwapSlowPeriod);

				// Add to chart for visualization
				AddChartIndicator(vwapFast);
				AddChartIndicator(vwapSlow);

				// Set colors for visualization
				vwapFast.Plots[0].Brush = Brushes.Magenta;
				vwapSlow.Plots[0].Brush = Brushes.Green;
			}
		}

		protected override void OnBarUpdate()
		{
			// Need enough bars for VWAP calculation
			if (CurrentBar < Math.Max(VwapFastPeriod, VwapSlowPeriod))
				return;

			// Check if we need to close all positions at specific time
			if (UseCloseAllAtTime && ShouldCloseAllPositions())
			{
				CloseAllPositions("Time_Close");
				return;
			}

			// Check if we're within trading hours
			if (!IsWithinTradingHours())
				return;

			// Check if current hour is excluded (hour filter)
			if (UseHourFilter && IsHourExcluded())
				return;

			// Get current values
			double currentPrice = Close[0];
			double vwapFastValue = vwapFast[0];
			double vwapSlowValue = vwapSlow[0];

			// Calculate price distance from VWAP Fast as percentage
			double priceDistancePct = Math.Abs(currentPrice - vwapFastValue) / vwapFastValue;

			// Determine trend direction (for trend filter)
			bool isUptrend = vwapFastValue > vwapSlowValue;
			bool isDowntrend = vwapFastValue < vwapSlowValue;

			// GREEN DOT SIGNAL (Price ejection above VWAP Fast)
			// Condition: Price is above VWAP Fast by at least PRICE_EJECTION_TRIGGER percentage
			greenDotSignal = false;
			if (currentPrice > vwapFastValue)
			{
				if (priceDistancePct >= PriceEjectionTrigger)
				{
					greenDotSignal = true;

					// Draw green dot on chart
					Draw.Dot(this, "GreenDot_" + CurrentBar, false, 0, currentPrice, Brushes.LimeGreen);
				}
			}

			// RED DOT SIGNAL (Price ejection below VWAP Fast)
			// Condition: Price is below VWAP Fast by at least PRICE_EJECTION_TRIGGER percentage
			redDotSignal = false;
			if (currentPrice < vwapFastValue)
			{
				if (priceDistancePct >= PriceEjectionTrigger)
				{
					redDotSignal = true;

					// Draw red dot on chart
					Draw.Dot(this, "RedDot_" + CurrentBar, false, 0, currentPrice, Brushes.Red);
				}
			}

			// ENTRY LOGIC
			if (Position.MarketPosition == MarketPosition.Flat)
			{
				// LONG ENTRY (Green Dot)
				if (greenDotSignal && AllowLong)
				{
					// Apply trend filter if enabled
					if (UseTrendFilter)
					{
						if (!isUptrend)
							return; // Skip entry if not in uptrend
					}

					// Enter LONG (main position)
					EnterLong(1, "Green_Dot_Long");

					// Place Grid Limit Orders if enabled
					if (UseGridEntry && NumberOfGridSteps > 0)
					{
						PlaceGridOrders(true, currentPrice); // true = LONG
					}
				}

				// SHORT ENTRY (Red Dot)
				if (redDotSignal && AllowShort)
				{
					// Apply trend filter if enabled
					if (UseTrendFilter)
					{
						if (!isDowntrend)
							return; // Skip entry if not in downtrend
					}

					// Enter SHORT (main position)
					EnterShort(1, "Red_Dot_Short");

					// Place Grid Limit Orders if enabled
					if (UseGridEntry && NumberOfGridSteps > 0)
					{
						PlaceGridOrders(false, currentPrice); // false = SHORT
					}
				}
			}
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice,
			int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			// Track entry price when MAIN position order is filled
			if (order.Name == "Green_Dot_Long" || order.Name == "Red_Dot_Short")
			{
				if (orderState == OrderState.Filled)
				{
					entryPrice = averageFillPrice;

					// Calculate and store main position SL level (shared by grid entries)
					if (Position.MarketPosition == MarketPosition.Long)
					{
						mainPositionStopLoss = entryPrice - (StopLossPoints * TickSize);
						SetProfitTarget("Green_Dot_Long", CalculationMode.Ticks, TakeProfitPoints);
						SetStopLoss("Green_Dot_Long", CalculationMode.Ticks, StopLossPoints, false);
					}
					else if (Position.MarketPosition == MarketPosition.Short)
					{
						mainPositionStopLoss = entryPrice + (StopLossPoints * TickSize);
						SetProfitTarget("Red_Dot_Short", CalculationMode.Ticks, TakeProfitPoints);
						SetStopLoss("Red_Dot_Short", CalculationMode.Ticks, StopLossPoints, false);
					}
				}
			}

			// Track GRID entry fills
			if (gridOrderNames.Contains(order.Name))
			{
				if (orderState == OrderState.Filled)
				{
					double gridEntryPrice = averageFillPrice;

					// Set TP for grid entry (calculated from its own fill price)
					SetProfitTarget(order.Name, CalculationMode.Ticks, TakeProfitPoints);

					// Set SL for grid entry (uses MAIN position's SL level, NOT from grid fill price)
					if (Position.MarketPosition == MarketPosition.Long)
					{
						// Calculate SL distance from grid fill price to main SL level
						double slDistance = gridEntryPrice - mainPositionStopLoss;
						int slTicks = (int)(slDistance / TickSize);
						SetStopLoss(order.Name, CalculationMode.Ticks, slTicks, false);
					}
					else if (Position.MarketPosition == MarketPosition.Short)
					{
						// Calculate SL distance from grid fill price to main SL level
						double slDistance = mainPositionStopLoss - gridEntryPrice;
						int slTicks = (int)(slDistance / TickSize);
						SetStopLoss(order.Name, CalculationMode.Ticks, slTicks, false);
					}
				}
			}
		}

		/// <summary>
		/// Check if current time is within allowed trading hours
		/// </summary>
		private bool IsWithinTradingHours()
		{
			TimeSpan currentTime = Time[0].TimeOfDay;
			TimeSpan startTime = new TimeSpan(StartHour, StartMinute, 0);
			TimeSpan endTime = new TimeSpan(EndHour, EndMinute, 59);

			return currentTime >= startTime && currentTime <= endTime;
		}

		/// <summary>
		/// Check if we should close all positions (at specific time)
		/// </summary>
		private bool ShouldCloseAllPositions()
		{
			TimeSpan currentTime = Time[0].TimeOfDay;
			TimeSpan closeTime = new TimeSpan(CloseAllHour, CloseAllMinute, 0);

			// Close if current time is at or past the close time and we have positions
			return currentTime >= closeTime && Position.MarketPosition != MarketPosition.Flat;
		}

		/// <summary>
		/// Close all open positions
		/// </summary>
		private void CloseAllPositions(string signalName)
		{
			if (Position.MarketPosition == MarketPosition.Long)
			{
				ExitLong(signalName);
			}
			else if (Position.MarketPosition == MarketPosition.Short)
			{
				ExitShort(signalName);
			}

			// Cancel any pending grid limit orders
			CancelAllGridOrders();
		}

		/// <summary>
		/// Place grid limit orders
		/// </summary>
		private void PlaceGridOrders(bool isLong, double mainEntryPrice)
		{
			// Clear previous grid order tracking
			gridOrderNames.Clear();

			for (int i = 1; i <= NumberOfGridSteps; i++)
			{
				double limitPrice;
				string orderName = "Grid_" + (++gridOrderCounter) + "_Step" + i;

				if (isLong)
				{
					// For LONG: Place limit orders BELOW main entry
					// Example: Main at 20000, Grid Step 60 pts → Grid 1 at 19940, Grid 2 at 19880
					limitPrice = mainEntryPrice - (i * GridStepPoints * TickSize);
					EnterLongLimit(1, limitPrice, orderName);
				}
				else
				{
					// For SHORT: Place limit orders ABOVE main entry
					// Example: Main at 20000, Grid Step 60 pts → Grid 1 at 20060, Grid 2 at 20120
					limitPrice = mainEntryPrice + (i * GridStepPoints * TickSize);
					EnterShortLimit(1, limitPrice, orderName);
				}

				// Track grid order names
				gridOrderNames.Add(orderName);

				// Draw horizontal line on chart for grid level
				Draw.HorizontalLine(this, "GridLevel_" + orderName, limitPrice,
					isLong ? Brushes.LimeGreen : Brushes.Red, DashStyleHelper.Dot, 1);
			}
		}

		/// <summary>
		/// Cancel all pending grid limit orders
		/// </summary>
		private void CancelAllGridOrders()
		{
			// NinjaTrader will automatically cancel all pending orders when position is closed
			// But we clear our tracking list
			gridOrderNames.Clear();
		}

		/// <summary>
		/// Parse the ExcludedHoursString into a HashSet for fast lookup
		/// </summary>
		private void ParseExcludedHours()
		{
			excludedHours.Clear();

			if (string.IsNullOrWhiteSpace(ExcludedHoursString))
				return;

			// Split by comma and parse each hour
			string[] hours = ExcludedHoursString.Split(',');
			foreach (string hourStr in hours)
			{
				int hour;
				if (int.TryParse(hourStr.Trim(), out hour))
				{
					// Validate hour is in valid range (0-23)
					if (hour >= 0 && hour <= 23)
					{
						excludedHours.Add(hour);
					}
				}
			}
		}

		/// <summary>
		/// Check if current hour is in the excluded hours list
		/// </summary>
		private bool IsHourExcluded()
		{
			int currentHour = Time[0].Hour;
			return excludedHours.Contains(currentHour);
		}

		#region Properties

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name="VWAP Fast Period", Description="Period for fast VWAP (magenta line)", Order=1, GroupName="1. VWAP Parameters")]
		public int VwapFastPeriod
		{ get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name="VWAP Slow Period", Description="Period for slow VWAP (green line)", Order=2, GroupName="1. VWAP Parameters")]
		public int VwapSlowPeriod
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0.0001, 1)]
		[Display(Name="Price Ejection Trigger %", Description="Minimum distance from VWAP Fast to trigger entry (0.001 = 0.1%)", Order=3, GroupName="1. VWAP Parameters")]
		public double PriceEjectionTrigger
		{ get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name="Take Profit (Points)", Description="Take profit in points", Order=1, GroupName="2. Exit Parameters")]
		public int TakeProfitPoints
		{ get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name="Stop Loss (Points)", Description="Stop loss in points", Order=2, GroupName="2. Exit Parameters")]
		public int StopLossPoints
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Use Trend Filter", Description="Only trade with VWAP trend (Fast vs Slow)", Order=1, GroupName="3. Entry Filters")]
		public bool UseTrendFilter
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Allow Long Trades", Description="Enable BUY entries (green dots)", Order=2, GroupName="3. Entry Filters")]
		public bool AllowLong
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Allow Short Trades", Description="Enable SELL entries (red dots)", Order=3, GroupName="3. Entry Filters")]
		public bool AllowShort
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0, 23)]
		[Display(Name="Start Hour", Description="Trading start hour (0-23)", Order=1, GroupName="4. Trading Hours")]
		public int StartHour
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0, 59)]
		[Display(Name="Start Minute", Description="Trading start minute (0-59)", Order=2, GroupName="4. Trading Hours")]
		public int StartMinute
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0, 23)]
		[Display(Name="End Hour", Description="Trading end hour (0-23)", Order=3, GroupName="4. Trading Hours")]
		public int EndHour
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0, 59)]
		[Display(Name="End Minute", Description="Trading end minute (0-59)", Order=4, GroupName="4. Trading Hours")]
		public int EndMinute
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Use Grid Entry", Description="Enable grid entry system with multiple limit orders", Order=1, GroupName="5. Grid Entry System")]
		public bool UseGridEntry
		{ get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name="Grid Step (Points)", Description="Distance between grid levels in points (e.g., 60 points = 60 ticks for NQ)", Order=2, GroupName="5. Grid Entry System")]
		public int GridStepPoints
		{ get; set; }

		[NinjaScriptProperty]
		[Range(1, 10)]
		[Display(Name="Number of Grid Steps", Description="Number of additional limit orders to place (1-10)", Order=3, GroupName="5. Grid Entry System")]
		public int NumberOfGridSteps
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Close All at Time", Description="Enable auto-close all positions at specific time", Order=1, GroupName="6. Time Management")]
		public bool UseCloseAllAtTime
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0, 23)]
		[Display(Name="Close All Hour", Description="Hour to close all positions (0-23, e.g., 22 = 10 PM)", Order=2, GroupName="6. Time Management")]
		public int CloseAllHour
		{ get; set; }

		[NinjaScriptProperty]
		[Range(0, 59)]
		[Display(Name="Close All Minute", Description="Minute to close all positions (0-59)", Order=3, GroupName="6. Time Management")]
		public int CloseAllMinute
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Use Hour Filter", Description="Enable hour exclusion filter to avoid trading during specific hours", Order=1, GroupName="7. Hour Filter")]
		public bool UseHourFilter
		{ get; set; }

		[NinjaScriptProperty]
		[Display(Name="Excluded Hours", Description="Comma-separated list of hours to exclude (0-23). Example: \"0,5,23\" excludes midnight, 5 AM, and 11 PM", Order=2, GroupName="7. Hour Filter")]
		public string ExcludedHoursString
		{ get; set; }

		#endregion
	}
}
