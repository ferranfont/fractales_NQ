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
			}
			else if (State == State.Configure)
			{
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

			// Check if we're within trading hours
			if (!IsWithinTradingHours())
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

					// Enter LONG
					EnterLong(1, "Green_Dot_Long");
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

					// Enter SHORT
					EnterShort(1, "Red_Dot_Short");
				}
			}
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice,
			int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			// Track entry price when order is filled
			if (order.Name == "Green_Dot_Long" || order.Name == "Red_Dot_Short")
			{
				if (orderState == OrderState.Filled)
				{
					entryPrice = averageFillPrice;

					// Set fixed TP and SL
					if (Position.MarketPosition == MarketPosition.Long)
					{
						SetProfitTarget("Green_Dot_Long", CalculationMode.Ticks, TakeProfitPoints);
						SetStopLoss("Green_Dot_Long", CalculationMode.Ticks, StopLossPoints, false);
					}
					else if (Position.MarketPosition == MarketPosition.Short)
					{
						SetProfitTarget("Red_Dot_Short", CalculationMode.Ticks, TakeProfitPoints);
						SetStopLoss("Red_Dot_Short", CalculationMode.Ticks, StopLossPoints, false);
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

		#endregion
	}
}
