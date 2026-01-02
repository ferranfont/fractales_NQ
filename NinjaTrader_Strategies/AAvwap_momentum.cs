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

//Strategy to implement VWAP Momentum Logic from config.py
// Authors: Assistant & User
// Version: 3.0 (ULTRA-ROBUST Ghost Order Protection)
// - AdoptAccountPosition: Syncs with real broker position
// - Ghost Position Detector: Compares strategy vs account state
// - Historical Block: No processing of historical bars
// - Order Cleanup: Cancels all pending orders on start/stop

namespace NinjaTrader.NinjaScript.Strategies
{
	public class AAvwap_momentum_V3 : Strategy
	{
		#region Variables
		// Parameters
		private int		vwapFastPeriod;
		private int		vwapSlowPeriod;
		private double	takeProfitPoints;
		private double	stopLossPoints;
		private double	priceEjectionTrigger;
		private bool	useTrendFilter;
		private bool	allowLong;
		private bool	allowShort;
		
		// Trading Hours
		private int		startHour;
		private int		startMinute;
		private int		endHour;
		private int		endMinute;

		// Grid Entry
		private bool	useGridEntry;
		private double	gridStepPoints;
		private int		numberOfGridSteps;

		// Close All
		private bool	useCloseAllAtTime;
		private int		closeAllHour;
		private int		closeAllMinute;

		// Hour Filter
		private bool	useHourFilter;
		private string	excludedHoursString;
		private HashSet<int> excludedHoursSet;

		// Indicators
		private SMA vwapFast; 
		private SMA vwapSlow; 

		// Internal Logic
		private double entryPrice;
		private double mainPositionStopLoss;
		private List<string> gridOrderNames; 
		
		// Safety
		private DateTime enableTime;

		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description									= "VWAP Momentum Strategy with Ejection Logic";
				Name										= "AAvwap_momentum_V3";
				Calculate									= Calculate.OnBarClose;
				EntriesPerDirection							= 1;
				EntryHandling								= EntryHandling.AllEntries;
				IsExitOnSessionCloseStrategy				= true;
				ExitOnSessionCloseSeconds					= 30;
				IsFillLimitOnTouch							= false;
				MaximumBarsLookBack							= MaximumBarsLookBack.TwoHundredFiftySix;
				OrderFillResolution							= OrderFillResolution.Standard;
				Slippage									= 0;
				StartBehavior								= StartBehavior.AdoptAccountPosition; 
				TimeInForce									= TimeInForce.Gtc;
				TraceOrders									= false;
				RealtimeErrorHandling						= RealtimeErrorHandling.StopCancelClose;
				StopTargetHandling							= StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade							= 200; 
				IsInstantiatedOnEachOptimizationIteration	= true;

				// Strategy Parameters
				VwapFastPeriod		= 100;		
				VwapSlowPeriod		= 200;		
				TakeProfitPoints	= 500;		
				StopLossPoints		= 300;		
				PriceEjectionTrigger = 0.001;	// 0.1% Trigger
				UseTrendFilter		= true;		
				AllowLong			= true;		
				AllowShort			= true;		

				// Trading Hours
				StartHour			= 0;
				StartMinute			= 0;
				EndHour				= 22;
				EndMinute			= 59;

				// Grid Entry
				UseGridEntry		= false;	
				GridStepPoints		= 60;		
				NumberOfGridSteps	= 1;		

				// Close All
				UseCloseAllAtTime	= false;	
				CloseAllHour		= 22;		
				CloseAllMinute		= 0;		

				// Hour Filter
				UseHourFilter		= false;		
				ExcludedHoursString	= "1,2,3,9,11,14,20";	
			}
			else if (State == State.Configure)
			{
				ParseExcludedHours();
				
				gridOrderNames = new List<string>();
				for(int i=1; i<=NumberOfGridSteps; i++)
				{
					gridOrderNames.Add("Grid_L_" + i);
					gridOrderNames.Add("Grid_S_" + i);
				}
			}
			else if (State == State.DataLoaded)
			{
				vwapFast = SMA(VwapFastPeriod);
				vwapSlow = SMA(VwapSlowPeriod);

				AddChartIndicator(vwapFast);
				AddChartIndicator(vwapSlow);

				vwapFast.Plots[0].Brush = Brushes.Magenta;
				vwapSlow.Plots[0].Brush = Brushes.Green;
			}
			else if (State == State.Realtime)
			{
				// CRITICAL FIX #1: Detect and reset ghost positions
				// If strategy thinks there's a position but account is actually flat → force reset
				if (Position.MarketPosition != MarketPosition.Flat)
				{
					var accountPosition = Account.Positions.FirstOrDefault(p => p.Instrument == Instrument);
					if (accountPosition == null || accountPosition.Quantity == 0)
					{
						Print(">>> GHOST POSITION DETECTED! Strategy shows position but account is flat. Forcing reset...");
						ExitLong();
						ExitShort();
						Print(">>> Ghost position reset complete.");
					}
				}

				// CRITICAL FIX #2: Cancel ALL pending orders on strategy start to prevent ghost orders
				// This clears any cached order state from previous runs
				CancelAllPendingOrders();
				Print("=== Strategy Started in Realtime Mode - All pending orders cancelled ===");

				enableTime = DateTime.Now;
			}
			else if (State == State.Terminated)
			{
				// CRITICAL FIX: Cancel ALL pending orders on strategy termination
				CancelAllPendingOrders();
				Print("=== Strategy Terminated - All pending orders cancelled ===");
			}
		}

		protected override void OnBarUpdate()
		{
            // CRITICAL FIX #3: Block ALL historical bar processing
            // This ensures strategy NEVER processes historical data, only realtime
            if (State == State.Historical)
                return;

            // =========================================================
            // LÓGICA DE VISUALIZACIÓN (Funciona en Histórico y Realtime)
            // =========================================================

            // Need enough bars
			if (CurrentBar < Math.Max(VwapFastPeriod, VwapSlowPeriod)) return;

			// Get values
			double currentPrice = Close[0];
			double vwapFastValue = vwapFast[0];
			double vwapSlowValue = vwapSlow[0];
			double priceDistancePct = Math.Abs(currentPrice - vwapFastValue) / vwapFastValue;

			bool greenDotSignal = false;
			bool redDotSignal = false;

			// Green Dot Calc
			if (currentPrice > vwapFastValue && priceDistancePct >= PriceEjectionTrigger)
			{
				greenDotSignal = true;
				Draw.Dot(this, "GreenDot_" + CurrentBar, false, 0, currentPrice, Brushes.LimeGreen);
			}

			// Red Dot Calc
			if (currentPrice < vwapFastValue && priceDistancePct >= PriceEjectionTrigger)
			{
				redDotSignal = true;
				Draw.Dot(this, "RedDot_" + CurrentBar, false, 0, currentPrice, Brushes.Red);
			}

            // =========================================================
            // LÓGICA DE TRADING (SOLO REALTIME)
            // =========================================================
            
            // 1. REGLA DE ORO: SI NO ES TIEMPO REAL, NO HACEMOS NADA DE TRADING
            if (State != State.Realtime) return;

            // 2. RETRASO DE SEGURIDAD (1 min)
			if (DateTime.Now < enableTime.AddMinutes(1)) return;

            // 3. RESTO DE FILTROS LÓGICOS
			if (UseCloseAllAtTime && ShouldCloseAllPositions())
			{
				CloseAllPositions("Time_Close");
				return;
			}
			if (!IsWithinTradingHours()) return;
			if (UseHourFilter && IsHourExcluded()) return;

			bool isUptrend = vwapFastValue > vwapSlowValue;
			bool isDowntrend = vwapFastValue < vwapSlowValue;

			// ENTRY EXECUTION
			if (Position.MarketPosition == MarketPosition.Flat)
			{
				// LONG
				if (greenDotSignal && AllowLong)
				{
					if (UseTrendFilter && !isUptrend) return;

					Print(string.Format("{0} - ENTERING LONG", Time[0]));
					EnterLong(1, "Green_Dot_Long");
					Draw.ArrowUp(this, "EntryLong_" + CurrentBar, false, 0, Low[0] - 10 * TickSize, Brushes.LimeGreen);

					if (UseGridEntry && NumberOfGridSteps > 0) PlaceGridOrders(true, currentPrice);
				}

				// SHORT
				if (redDotSignal && AllowShort)
				{
					if (UseTrendFilter && !isDowntrend) return;

					Print(string.Format("{0} - ENTERING SHORT", Time[0]));
					EnterShort(1, "Red_Dot_Short");
					Draw.ArrowDown(this, "EntryShort_" + CurrentBar, false, 0, High[0] + 10 * TickSize, Brushes.Red);

					if (UseGridEntry && NumberOfGridSteps > 0) PlaceGridOrders(false, currentPrice);
				}
			}
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice,
			int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			if (order.Name == "Green_Dot_Long" || order.Name == "Red_Dot_Short")
			{
				if (orderState == OrderState.Filled)
				{
					entryPrice = averageFillPrice;

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
			
			if (gridOrderNames.Contains(order.Name) && orderState == OrderState.Filled)
			{
				if (Position.MarketPosition == MarketPosition.Long)
				{
					SetStopLoss(order.Name, CalculationMode.Price, mainPositionStopLoss, false);
					SetProfitTarget(order.Name, CalculationMode.Ticks, TakeProfitPoints); 
				}
				else if (Position.MarketPosition == MarketPosition.Short)
				{
					SetStopLoss(order.Name, CalculationMode.Price, mainPositionStopLoss, false);
					SetProfitTarget(order.Name, CalculationMode.Ticks, TakeProfitPoints); 
				}
			}
		}

		#region Helpers
		private void PlaceGridOrders(bool isLong, double basePrice)
		{
			for (int i = 1; i <= NumberOfGridSteps; i++)
			{
				if (isLong)
					EnterLongLimit(1, basePrice - (GridStepPoints * i), "Grid_L_" + i);
				else
					EnterShortLimit(1, basePrice + (GridStepPoints * i), "Grid_S_" + i);
			}
		}

		private void CloseAllPositions(string reason)
		{
			if (Position.MarketPosition != MarketPosition.Flat)
			{
				Print("Closing All: " + reason);
				ExitLong();
				ExitShort();
			}
		}
		
		private bool ShouldCloseAllPositions()
		{
			if (Time[0].Hour == CloseAllHour && Time[0].Minute == CloseAllMinute) return true;
			return false;
		}

		private bool IsWithinTradingHours()
		{
			int currentHour = Time[0].Hour;
			int currentMinute = Time[0].Minute;
			int currentTime = currentHour * 60 + currentMinute;
			int startTime = StartHour * 60 + StartMinute;
			int endTime = EndHour * 60 + EndMinute;

			if (endTime < startTime) // Overnight
				return currentTime >= startTime || currentTime <= endTime;
			else
				return currentTime >= startTime && currentTime <= endTime;
		}

		private bool IsHourExcluded()
		{
			return excludedHoursSet != null && excludedHoursSet.Contains(Time[0].Hour);
		}

		private void ParseExcludedHours()
		{
			excludedHoursSet = new HashSet<int>();
			if (string.IsNullOrEmpty(ExcludedHoursString)) return;

			string[] parts = ExcludedHoursString.Split(',');
			foreach (string part in parts)
			{
				int h;
				if (int.TryParse(part.Trim(), out h))
					excludedHoursSet.Add(h);
			}
		}

		private void CancelAllPendingOrders()
		{
			// Cancel all working orders (pending limit/stop orders)
			foreach (var order in Account.Orders)
			{
				if (order.OrderState == OrderState.Working && order.Instrument == Instrument)
				{
					CancelOrder(order);
				}
			}
		}
		#endregion

		#region Properties
		[NinjaScriptProperty]
		[Display(Name="VwapFastPeriod", Order=1, GroupName="Parameters")]
		public int VwapFastPeriod { get; set; }

		[NinjaScriptProperty]
		[Display(Name="VwapSlowPeriod", Order=2, GroupName="Parameters")]
		public int VwapSlowPeriod { get; set; }

		[NinjaScriptProperty]
		[Display(Name="TakeProfitPoints", Order=3, GroupName="Parameters")]
		public double TakeProfitPoints { get; set; }

		[NinjaScriptProperty]
		[Display(Name="StopLossPoints", Order=4, GroupName="Parameters")]
		public double StopLossPoints { get; set; }

		[NinjaScriptProperty]
		[Display(Name="PriceEjectionTrigger", Order=5, GroupName="Parameters")]
		public double PriceEjectionTrigger { get; set; }

		[NinjaScriptProperty]
		[Display(Name="UseTrendFilter", Order=6, GroupName="Parameters")]
		public bool UseTrendFilter { get; set; }

		[NinjaScriptProperty]
		[Display(Name="AllowLong", Order=7, GroupName="Parameters")]
		public bool AllowLong { get; set; }

		[NinjaScriptProperty]
		[Display(Name="AllowShort", Order=8, GroupName="Parameters")]
		public bool AllowShort { get; set; }

		[NinjaScriptProperty]
		[Display(Name="StartHour", Order=9, GroupName="Trading Hours")]
		public int StartHour { get; set; }
		[NinjaScriptProperty]
		[Display(Name="StartMinute", Order=10, GroupName="Trading Hours")]
		public int StartMinute { get; set; }
		[NinjaScriptProperty]
		[Display(Name="EndHour", Order=11, GroupName="Trading Hours")]
		public int EndHour { get; set; }
		[NinjaScriptProperty]
		[Display(Name="EndMinute", Order=12, GroupName="Trading Hours")]
		public int EndMinute { get; set; }

		[NinjaScriptProperty]
		[Display(Name="UseGridEntry", Order=13, GroupName="Grid")]
		public bool UseGridEntry { get; set; }
		[NinjaScriptProperty]
		[Display(Name="GridStepPoints", Order=14, GroupName="Grid")]
		public double GridStepPoints { get; set; }
		[NinjaScriptProperty]
		[Display(Name="NumberOfGridSteps", Order=15, GroupName="Grid")]
		public int NumberOfGridSteps { get; set; }

		[NinjaScriptProperty]
		[Display(Name="UseCloseAllAtTime", Order=16, GroupName="Close All")]
		public bool UseCloseAllAtTime { get; set; }
		[NinjaScriptProperty]
		[Display(Name="CloseAllHour", Order=17, GroupName="Close All")]
		public int CloseAllHour { get; set; }
		[NinjaScriptProperty]
		[Display(Name="CloseAllMinute", Order=18, GroupName="Close All")]
		public int CloseAllMinute { get; set; }

		[NinjaScriptProperty]
		[Display(Name="UseHourFilter", Order=19, GroupName="Hour Filter")]
		public bool UseHourFilter { get; set; }
		[NinjaScriptProperty]
		[Display(Name="ExcludedHours", Order=20, GroupName="Hour Filter")]
		public string ExcludedHoursString { get; set; }
		#endregion
	}
}
