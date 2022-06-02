from cmath import nan
from jesse.strategies import Strategy, cached
import jesse.indicators as ta
from jesse import utils
import numpy as np
import jesse.helpers as jh
import utils as tu
from st import st
from st2 import st2
from lrsi2 import lrsi2

class TFC(Strategy):
    def __init__(self):
        super().__init__()
        self.debug_log                              = 1          ## Turn on for debug logging to CSV, 
        self.price_precision                        = 2 		#self._price_precision()
        self.hps                                    = []
        self.svars                                  = {}
        self.lvars                                  = {}
        self.data_header                            = ['Index', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Action', 'Cmt', 'Starting Balance', 'Finishing Balance', 'Profit', 'Qty','SL','TP1', 'TP2']
        self.data_log                               = []
        self.indicator_header                       = ['Index', 'Time', ]
        self.indicator_log                          = []

        self.pine_log                               = ''
        self.pine_orderid                           = 0

        self.sliced_candles                         = {}
        self.is_optimising                          = False
        self.params_overdrive                       = True          ## Overwrite params to file, turn off for production, turn on for testing / optimizing
        
        self.pyramiding_levels                      = 0
        self.last_opened_price                      = 0
        self.last_was_profitable                    = False
        self.pre_index                              = 0
        self.qty                                    = 0

        self.entry_atr                              = 0
        self.entry_price                            = 0
        self.last_win                               = False
        self.initial_entry                          = 0
        self.starting_capital                       = 0
        self.starting_balance                       = 0

        self.onlyLong                               = False         # True: Only Long Position
        self.onlyShort                              = False         # True: Only Short Position
        self.LS                                     = True          # True: Long and Short Position
        # self.vars["enableLS"]                       = True
        self.vars["enableLong"]                     = True          # Enable Long Entry
        self.vars["enableShort"]                    = True          # Enable Short Entry
        self.vars["botRisk"]                        = 2             # Bot Risk % each entry
        self.vars["maximum_pyramiding_levels"]      = 2
        self.vars["trailing_stoploss"]              = 2
        self.vars["move_on_no_entry"]               = True


        # self.botLeverage                            = 10          # Bot Leverage
        self.vars["botPricePrecision"]              = 2             # Bot Order Price Precision
        self.vars["botBasePrecision"]               = 3             # Bot Order Coin Precision
        self.vars["atrLength"]                      = 14            # ATR Length
        self.vars["atrSmoothing"]                   = 'RMA'         # ATR Smoothing
        self.vars["getConfirmation"]                = True          # Get Trend Confirmation from longer timeframe?
        self.vars["confirmationResolution"]         = 'D'           # Confirmation Timeframe
        self.vars["lrsiApplyFractalsEnergy"]        = True          # LRSI: Apply Fractals Energy?
        self.vars["lrsiApplyNormalization"]         = False         # LRSI:Apply Normalization to [0, 100]?
        
        # Long
        self.lvars["atrSLMultipier"]                = 1.3           # Short ATR SL Multipier
        self.lvars["atrTPMultipier"]                = 2.5             # Short ATR TP Multipier
        # self.lvars["enableTrailingSL"]              = False         # Enable Trailing SL Type 1
        self.lvars["trailingSLPercent"]             = 0.5           # Trailing SL 1 Percent
        # self.lvars["enableTrailingSL2"]             = True          # Enable Trailing SL Type 2: 3 steps
        self.lvars["trailingSLPercent1"]            = 0.8           # Step 1: Red Zone
        self.lvars["trailingSLPercent2"]            = 1             # Step 2: Red Zone
        self.lvars["trailingSLPercent3"]            = 1.1           # Step 3: Green Zone
        self.lvars["trailingTrigger1"]              = 0.33          # Step 1 Trigger: Low > X%
        self.lvars["trailingTrigger2"]              = 0.66          # Step 2 Trigger: High > X%

        self.lvars["st1Factor"]                     = 1.5           # SuperTrend 1: Factor
        self.lvars["st1Period"]                     = 7             # SuperTrend 1: Period
        self.lvars["st2Factor"]                     = 1.65          # SuperTrend 2: Factor
        self.lvars["st2Period"]                     = 100           # SuperTrend 2: Period    
        self.lvars["emaFast"]                       = 8             # EMA Cross: Fast
        self.lvars["emaSlow"]                       = 15            # EMA Cross: Slow
        self.lvars["aroonLength"]                   = 8             # Aroon: Length
        self.lvars["dmiLength"]                     = 8             # DMI: Length
        self.lvars["lrsiAlpha"]                     = 0.7           # LRSI: Alpha
        self.lvars["lrsiFeLength"]                  = 13            # LRSI: Fractals Energy Length
        self.lvars["threshold"]                     = 3             # Indicator Threshold
        
        # Short
        self.svars["atrSLMultipier"]                = 1.6           # Short ATR SL Multipier
        self.svars["atrTPMultipier"]                = 3             # Short ATR TP Multipier
        # self.svars["enableTrailingSL"]              = False         # Enable Trailing SL Type 1
        self.svars["trailingSLPercent"]             = 0.5           # Trailing SL 1 Percent
        # self.svars["enableTrailingSL2"]             = True          # Enable Trailing SL Type 2: 3 steps
        self.svars["trailingSLPercent1"]            = 0.8           # Step 1: Red Zone
        self.svars["trailingSLPercent2"]            = 1             # Step 2: Red Zone
        self.svars["trailingSLPercent3"]            = 1.1           # Step 3: Green Zone
        self.svars["trailingTrigger1"]              = 0.33          # Step 1 Trigger: Low > X%
        self.svars["trailingTrigger2"]              = 0.66          # Step 2 Trigger: High > X%

        self.svars["st1Factor"]                     = 1.5           # SuperTrend 1: Factor
        self.svars["st1Period"]                     = 7             # SuperTrend 1: Period
        self.svars["st2Factor"]                     = 1.65          # SuperTrend 2: Factor
        self.svars["st2Period"]                     = 100           # SuperTrend 2: Period    
        self.svars["emaFast"]                       = 8             # EMA Cross: Fast
        self.svars["emaSlow"]                       = 15            # EMA Cross: Slow
        self.svars["aroonLength"]                   = 8             # Aroon: Length
        self.svars["dmiLength"]                     = 8             # DMI: Length
        self.svars["lrsiAlpha"]                     = 0.7           # LRSI: Alpha
        self.svars["lrsiFeLength"]                  = 13            # LRSI: Fractals Energy Length
        self.svars["threshold"]                     = 3             # Indicator Threshold

        self.longStop                               = 0
        self.longProfit1                            = 0
        self.longProfit2                            = 0
        self.shortStop                              = 0
        self.shortProfit1                           = 0
        self.shortProfit2                           = 0
        self.entryPrice                             = 0
        self.entryAtr                               = 0
        self.trailSLStep                            = 0
        self.trailTPStep                            = 0
        self.pyramiding                             = 0

        self.onlyLong                               = False
        self.onlyShort                              = False
        self.LS                                     = True

        self.dmiTrend                               = 0
        self.pre_dmiTrend                           = 0
        self.lrsiSignal                             = 0
        self.pre_lrsiSignal                         = 0
        self.aroonIndicatorTrend                    = 0
        self.pre_aroonIndicatorTrend                = 0
        self.aroonOscillatorSignal                  = 0
        self.pre_aroonOscillatorSignal              = 0
        self.trendStrength                          = 0
        self.pre_trendStrength                      = 0


    def hyperparameters(self):
        return [ 

            {'name': 'longAtrSLMultipier', 'title': 'Long ATR SL Multipier', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.6},
            {'name': 'longAtrTPMultipier', 'title': 'Long ATR TP Multipier', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 3.0},
            {'name': 'longTrailingSLPercent', 'title': 'Long Trailing SL Percent', 'type': float, 'min': 0.05, 'max': 0.95, 'default': 0.5},
            {'name': 'longTrailingSLPercent1', 'title': 'Long Trailing SL Percent Step 1: Red Zone',  'type': float,'min': 0.6, 'max': 1.0, 'default': 0.8},
            {'name': 'longTrailingSLPercent2', 'title': 'Long Trailing SL Percent Step 1: Red Zone', 'type': float, 'min': 0.8, 'max': 1.2, 'default': 1.0},
            {'name': 'longTrailingSLPercent3', 'title': 'Long Trailing SL Percent Step 3: Green Zone', 'type': float, 'min': 0.9, 'max': 1.3, 'default': 1.1},
            {'name': 'longTrailingTrigger1', 'title': 'Long Trailing Trigger 1 Step 1 Trigger: Low > X%', 'type': float, 'min': 0.1, 'max': 0.45, 'default': 0.33},
            {'name': 'LongTrailingTrigger2', 'title': 'Long Trailing Trigger 2 Step 2 Trigger: High > X%', 'type': float, 'min': 0.54, 'max': 0.89, 'default': 0.66},
            {'name': 'longSt1Factor', 'title': 'Long SuperTrend 1: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.5},
            {'name': 'longSt1Period', 'title': 'Long SuperTrend 1: Period', 'type': int, 'min': 3, 'max': 10, 'default': 7},
            {'name': 'longSt2Factor', 'title': 'Long SuperTrend 2: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.65},
            {'name': 'longSt2Period', 'title': 'Long SuperTrend 2: Period', 'type': int, 'min': 90, 'max': 110, 'default': 100},
            {'name': 'longEmaFast', 'title': 'Long EMA Fast', 'type': int, 'min': 5, 'max': 20, 'default': 8},
            {'name': 'longEmaSlow', 'title': 'Long EMA Slow', 'type': int, 'min': 10, 'max': 30, 'default': 15},
            {'name': 'longAroonLength', 'title': 'Long Aroon Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'longDmiLength', 'title': 'Long DMI Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'longLrsiAlpha', 'title': 'Long LRSI Alpha', 'type': float, 'min': 0.4, 'max': 0.9, 'default': 0.7},
            {'name': 'longLrsiFeLength', 'title': 'Long LRSI Fractals Energy Length', 'type': int, 'min': 5, 'max': 20, 'default': 13},
            {'name': 'longThreshold', 'title': 'Long Indicator Threshold', 'type': int, 'min': 3, 'max': 5, 'default': 3 }, 

            {'name': 'shortAtrSLMultipier', 'title': 'Short ATR SL Multipier', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.6},
            {'name': 'shortAtrTPMultipier', 'title': 'Short ATR TP Multipier', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 3.0},
            {'name': 'shortTrailingSLPercent', 'title': 'Short Trailing SL Percent', 'type': float, 'min': 0.05, 'max': 0.95, 'default': 0.5},
            {'name': 'shortTrailingSLPercent1', 'title': 'Short Trailing SL Percent Step 1: Red Zone',  'type': float,'min': 0.6, 'max': 1.0, 'default': 0.8},
            {'name': 'shortTrailingSLPercent2', 'title': 'Short Trailing SL Percent Step 1: Red Zone', 'type': float, 'min': 0.8, 'max': 1.2, 'default': 1.0},
            {'name': 'shortTrailingSLPercent3', 'title': 'Short Trailing SL Percent Step 3: Green Zone', 'type': float, 'min': 0.9, 'max': 1.3, 'default': 1.1},
            {'name': 'shortTrailingTrigger1', 'title': 'Short Trailing Trigger 1 Step 1 Trigger: Low > X%', 'type': float, 'min': 0.1, 'max': 0.45, 'default': 0.33},
            {'name': 'shortTrailingTrigger2', 'title': 'Short Trailing Trigger 2 Step 2 Trigger: High > X%', 'type': float, 'min': 0.54, 'max': 0.89, 'default': 0.66},
            {'name': 'shortSt1Factor', 'title': 'Short SuperTrend 1: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.5},
            {'name': 'shortSt1Period', 'title': 'Short SuperTrend 1: Period', 'type': int, 'min': 3, 'max': 10, 'default': 7},
            {'name': 'shortSt2Factor', 'title': 'Short SuperTrend 2: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.65},
            {'name': 'shortSt2Period', 'title': 'Short SuperTrend 2: Period', 'type': int, 'min': 90, 'max': 110, 'default': 100},
            {'name': 'shortEmaFast', 'title': 'Short EMA Fast', 'type': int, 'min': 5, 'max': 20, 'default': 8},
            {'name': 'shortEmaSlow', 'title': 'Short EMA Slow', 'type': int, 'min': 10, 'max': 30, 'default': 15},
            {'name': 'shortAroonLength', 'title': 'Short Aroon Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'shortDmiLength', 'title': 'Short DMI Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'shortLrsiAlpha', 'title': 'Short LRSI Alpha', 'type': float, 'min': 0.4, 'max': 0.9, 'default': 0.7},
            {'name': 'shortLrsiFeLength', 'title': 'Short LRSI Fractals Energy Length', 'type': int, 'min': 5, 'max': 20, 'default': 13},
            {'name': 'shortThreshold', 'title': 'Short Indicator Threshold', 'type': int, 'min': 3, 'max': 5, 'default': 3 }, 

        ]

    def on_first_candle(self):
        self.starting_balance = self.capital

        # print("On First Candle")
        if jh.is_livetrading():
            self.price_precision = self._price_precision()
            self.qty_precision = self._qty_precision()
        else:
            self.price_precision = 2
            self.qty_precision = 2

        # Load params from file if not loaded
        file_name = "params/" + type(self).__name__ + '_' + self.symbol + '_' + self.timeframe +'.json'
        vars = {}
        file_exists = jh.file_exists(file_name)
        if file_exists:
            fvars = tu.load_params(file_name)
            param_update = False
            if len(self.vars) + len(self.lvars) + len(self.svars) != len(fvars['common_vars']) + len(fvars['long_vars']) + len(fvars['short_vars']):
                # print("Params file is updated")
                param_update = True
            if not self.params_overdrive:
                self.vars  = fvars['common_vars']
                self.lvars = fvars['long_vars']
                self.svars = fvars['short_vars']
            if param_update:
                vars['common_vars'] = self.vars
                vars['long_vars']   = self.lvars
                vars['short_vars']  = self.svars
                tu.save_params(file_name, vars)
               
        else:
            # Write default params
            vars['common_vars'] = self.vars
            vars['long_vars']   = self.lvars
            vars['short_vars']  = self.svars
            tu.save_params(file_name, vars)

        if jh.is_optimizing():
            # Long
            self.lvars["AtrSLMultipier"]                = self.hp["longAtrSLMultipier"]
            self.lvars["AtrTPMultipier"]                = self.hp["longAtrTPMultipier"]
            self.lvars["trailingSLPercent"]             = self.hp["longTrailingSLPercent"]
            self.lvars["trailingSLPercent1"]            = self.hp["longTrailingSLPercent1"]
            self.lvars["trailingSLPercent2"]            = self.hp["longTrailingSLPercent2"]
            self.lvars["trailingSLPercent3"]            = self.hp["longTrailingSLPercent3"]
            self.lvars["trailingTrigger1"]              = self.hp["longTrailingTrigger1"]
            self.lvars["trailingTrigger2"]              = self.hp["longTrailingTrigger2"]
            self.lvars["st1Factor"]                     = self.hp["longSt1Factor"]
            self.lvars["st1Period"]                     = self.hp["longSt1Period"]
            self.lvars["st2Factor"]                     = self.hp["longSt2Factor"]
            self.lvars["st2Period"]                     = self.hp["longSt2Period"] 
            self.lvars["emaFast"]                       = self.hp["longEmaFast"]
            self.lvars["emaSlow"]                       = self.hp["longEmaSlow"]
            self.lvars["aroonLength"]                   = self.hp["longAroonLength"]
            self.lvars["dmiLength"]                     = self.hp["longDmiLength"]
            self.lvars["lrsiAlpha"]                     = self.hp["longLrsiAlpha"]
            self.lvars["lrsiFeLength"]                  = self.hp["longLrsiFeLength"]
            self.lvars["threshold"]                     = self.hp["longThreshold"]

            # Short
            self.svars["AtrSLMultipier"]                = self.hp["shortAtrSLMultipier"]
            self.svars["AtrTPMultipier"]                = self.hp["shortAtrTPMultipier"]
            self.svars["trailingSLPercent"]             = self.hp["shortTrailingSLPercent"]
            self.svars["trailingSLPercent1"]            = self.hp["shortTrailingSLPercent1"]
            self.svars["trailingSLPercent2"]            = self.hp["shortTrailingSLPercent2"]
            self.svars["trailingSLPercent3"]            = self.hp["shortTrailingSLPercent3"]
            self.svars["trailingTrigger1"]              = self.hp["shortTrailingTrigger1"]
            self.svars["trailingTrigger2"]              = self.hp["shortTrailingTrigger2"]
            self.svars["st1Factor"]                     = self.hp["shortSt1Factor"]
            self.svars["st1Period"]                     = self.hp["shortSt1Period"]
            self.svars["st2Factor"]                     = self.hp["shortSt2Factor"]
            self.svars["st2Period"]                     = self.hp["shortSt2Period"] 
            self.svars["emaFast"]                       = self.hp["shortEmaFast"]
            self.svars["emaSlow"]                       = self.hp["shortEmaSlow"]
            self.svars["aroonLength"]                   = self.hp["shortAroonLength"]
            self.svars["dmiLength"]                     = self.hp["shortDmiLength"]
            self.svars["lrsiAlpha"]                     = self.hp["shortLrsiAlpha"]
            self.svars["lrsiFeLength"]                  = self.hp["shortLrsiFeLength"]
            self.svars["threshold"]                     = self.hp["shortThreshold"]   
        
    def on_new_candle(self):
        if self.debug_log > 0:  
            self.ts = tu.timestamp_to_gmt7(self.current_candle[0] / 1000)
        return 

    def before(self):

        # # Long
        # self.lvars["atrSLMultipier"]                = self.hp["longAtrSLMultipier"]
        # self.lvars["atrTPMultipier"]                = self.hp["longAtrTPMultipier"]
        # self.lvars["trailingSLPercent"]             = self.hp["longTrailingSLPercent"]
        # self.lvars["trailingSLPercent1"]            = self.hp["longTrailingSLPercent1"]
        # self.lvars["trailingSLPercent2"]            = self.hp["longTrailingSLPercent2"]
        # self.lvars["trailingSLPercent3"]            = self.hp["longTrailingSLPercent3"]
        # self.lvars["trailingTrigger1"]              = self.hp["longTrailingTrigger1"]
        # self.lvars["trailingTrigger2"]              = self.hp["longTrailingTrigger2"]
        # self.lvars["st1Factor"]                     = self.hp["longSt1Factor"]
        # self.lvars["st1Period"]                     = self.hp["longSt1Period"]
        # self.lvars["st2Factor"]                     = self.hp["longSt2Factor"]
        # self.lvars["st2Period"]                     = self.hp["longSt2Period"] 
        # self.lvars["emaFast"]                       = self.hp["longEmaFast"]
        # self.lvars["emaSlow"]                       = self.hp["longEmaSlow"]
        # self.lvars["aroonLength"]                   = self.hp["longAroonLength"]
        # self.lvars["dmiLength"]                     = self.hp["longDmiLength"]
        # self.lvars["lrsiAlpha"]                     = self.hp["longLrsiAlpha"]
        # self.lvars["lrsiFeLength"]                  = self.hp["longLrsiFeLength"]
        # self.lvars["threshold"]                     = self.hp["longThreshold"]

        # # Short
        # self.svars["atrSLMultipier"]                = self.hp["shortAtrSLMultipier"]
        # self.svars["atrTPMultipier"]                = self.hp["shortAtrTPMultipier"]
        # self.svars["trailingSLPercent"]             = self.hp["shortTrailingSLPercent"]
        # self.svars["trailingSLPercent1"]            = self.hp["shortTrailingSLPercent1"]
        # self.svars["trailingSLPercent2"]            = self.hp["shortTrailingSLPercent2"]
        # self.svars["trailingSLPercent3"]            = self.hp["shortTrailingSLPercent3"]
        # self.svars["trailingTrigger1"]              = self.hp["shortTrailingTrigger1"]
        # self.svars["trailingTrigger2"]              = self.hp["shortTrailingTrigger2"]
        # self.svars["st1Factor"]                     = self.hp["shortSt1Factor"]
        # self.svars["st1Period"]                     = self.hp["shortSt1Period"]
        # self.svars["st2Factor"]                     = self.hp["shortSt2Factor"]
        # self.svars["st2Period"]                     = self.hp["shortSt2Period"] 
        # self.svars["emaFast"]                       = self.hp["shortEmaFast"]
        # self.svars["emaSlow"]                       = self.hp["shortEmaSlow"]
        # self.svars["aroonLength"]                   = self.hp["shortAroonLength"]
        # self.svars["dmiLength"]                     = self.hp["shortDmiLength"]
        # self.svars["lrsiAlpha"]                     = self.hp["shortLrsiAlpha"]
        # self.svars["lrsiFeLength"]                  = self.hp["shortLrsiFeLength"]
        # self.svars["threshold"]                     = self.hp["shortThreshold"]


        # Call on first candle
        if self.index == 0:
            self.on_first_candle()
        self.sliced_candles = np.nan_to_num(jh.slice_candles(self.candles, sequential=True))

        # Call on new candle
        self.on_new_candle()

    def risk_qty_long(self):
        risk_loss = self.capital * self.vars["botRisk"]  / (self.c_atr * self.lvars["atrSLMultipier"]  * 100) 
        return risk_loss

    def risk_qty_short(self):
        risk_loss = self.capital * self.vars["botRisk"]  / (self.c_atr * self.svars["atrSLMultipier"]  * 100) 
        return risk_loss

    def f_atr(self, tr, length):
        if self.vars["atrSmoothing"] == 'RMA':
            temp = ta.rma(tr, length=length)
        elif self.vars["atrSmoothing"] == 'SMA':
            temp = ta.sma(tr, period=length)
        elif self.vars["atrSmoothing"] == 'EMA':
            temp = ta.ema(tr, period=length)
        else:
            temp = ta.wma(tr, period=length)
        return temp

    @property
    @cached
    def c_atr(self):
        tr = ta.trange(self.candles, sequential=True)
        temp = self.f_atr(tr,self.vars["atrLength"])
        return temp
    
    # Define EMA Cross and Determine Status
    def maTrend(self, emaFast, emaSlow):
        ma1 = ta.ema(self.candles, period=emaFast, source_type="close")
        ma2 = ta.ema(self.candles, period=emaSlow, source_type="close")
        if ma1 < ma2:
            return -1
        else:
            return 1

    @property
    def l_st_condition(self):
        st_condition = False

        # SuperTrend 1 Values on First TimeFrame 
        [st1_trend_tf1, st1_changed_tf1] = st(self.candles, period=self.lvars["st1Period"], factor=self.lvars["st1Factor"])
        # print("ST1 TF1: ", st1_trend_tf1, st1_changed_tf1)
        
        # SuperTrend 2 Values on First TimeFrame 
        [st2_trend_tf1, st2_changed_tf1] = st(self.candles, period=self.lvars["st2Period"], factor=self.lvars["st2Factor"])
        # print("ST2 TF1: ", st2_trend_tf1, st2_changed_tf1)
        
        # Determine SuperTrend 1 Values on Second Timeframe
        if self.vars["confirmationResolution"] == "D":
            # [st1_trend_tf2, st1_changed_tf2] = st2(self.candles, self.exchange, self.symbol, '1D', period=self.lvars["st1Period"], factor=self.lvars["st1Factor"])
            [st1_trend_tf2, st1_changed_tf2] = st2(self.get_candles(self.exchange, self.symbol, '1D'), period=self.lvars["st1Period"], factor=self.lvars["st1Factor"])
            # print("ST1 TF2: ", st1_trend_tf2, st1_changed_tf2)


        # Determine SuperTrend 2 Values on Second Timeframe
            # [st2_trend_tf2, st2_changed_tf2] = st2(self.candles, self.exchange, self.symbol, '1D', period=self.lvars["st2Period"], factor=self.lvars["st2Factor"])
            [st2_trend_tf2, st2_changed_tf2] = st2(self.get_candles(self.exchange, self.symbol, '1D'), period=self.lvars["st2Period"], factor=self.lvars["st2Factor"])
            # print("ST2 TF2: ", st2_trend_tf2, st2_changed_tf2)

        # Combine the SuperTrends on the first timeframe into one, determine values, and plot
        stComboTrend_Tf1 = 0.0
        if st1_trend_tf1 == st2_trend_tf1:
            stComboTrend_Tf1 = st1_trend_tf1
        else:
            stComboTrend_Tf1 = nan
        print("StComboTrend_tf1: ", stComboTrend_Tf1)

        # Combine the SuperTrends on the second timeframe into one, determine values, and plot
        stComboTrend_Tf2 = 0.0
        if st1_trend_tf2 == st2_trend_tf2:
            stComboTrend_Tf2 = st1_trend_tf2
        else:
            stComboTrend_Tf2 = nan
        print("StComboTrend_tf2: ", stComboTrend_Tf2)

        # Determine Overall SuperTrend Direction
        stComboTrend = 0.0
        if self.vars["getConfirmation"]:
            if stComboTrend_Tf1 == stComboTrend_Tf2:
                stComboTrend = stComboTrend_Tf1
            else:
                stComboTrend = nan
        else:
            stComboTrend = stComboTrend_Tf1
        print("StComboTrend: ", stComboTrend)
        
        
        # Define Aroon Indicator and Determine Status
        [aroonIndicatorUpper, aroonIndicatorLower] = ta.aroon(self.candles, period=self.lvars["aroonLength"], sequential=True)
        if utils.crossed(aroonIndicatorUpper, aroonIndicatorLower, 'above'):
            self.aroonIndicatorTrend = 1
        elif  utils.crossed(aroonIndicatorLower, aroonIndicatorUpper, 'above'):
            self.aroonIndicatorTrend = -1
        else:
            self.aroonIndicatorTrend = self.pre_aroonIndicatorTrend
        # print("pre aroonIndicatorTrend: ", self.pre_aroonIndicatorTrend)
        print("aroonIndicatorTrend: ", self.aroonIndicatorTrend)

        self.pre_aroonIndicatorTrend = self.aroonIndicatorTrend

        # Define Aroon Oscillator and Determine Status
        # aroonOscillator = ta.aroonosc(self.candles, period=self.lvars["aroonLength"], sequential=True)
        aroonOscillator = aroonIndicatorUpper - aroonIndicatorLower
        if utils.crossed(aroonOscillator, -80, 'above'):
            self.aroonOscillatorSignal = 1
        elif utils.crossed(aroonOscillator, 80, 'below'):
            self.aroonOscillatorSignal = -1
        else:
            self.aroonOscillatorSignal = self.pre_aroonOscillatorSignal
        # print("pre aroonOscillator Signal: ", self.pre_aroonOscillatorSignal)
        print("aroonOscillator Signal: ", self.aroonOscillatorSignal)

        self.pre_aroonOscillatorSignal = self.aroonOscillatorSignal

        # Define Directional Movement Index and Determine Values
        [dmiPlus, dmiMinus] = ta.dm(self.candles, period=self.lvars["dmiLength"], sequential=True)

        if utils.crossed(dmiPlus, dmiMinus, 'above'):
            self.dmiTrend = 1
        elif utils.crossed(dmiMinus, dmiPlus, 'above'):
            self.dmiTrend = -1
        else:
            self.dmiTrend = self.pre_dmiTrend
        # print("pre dmiTrend: ", self.pre_dmiTrend)
        print("dmiTrend: ", self.dmiTrend)

        self.pre_dmiTrend = self.dmiTrend

        # Define Laguerre RSI and Determine Values
        
        lrsi = lrsi2(self.candles, alpha=self.lvars["lrsiAlpha"], feLength=self.lvars["lrsiFeLength"], applyFactalsEnergy=self.vars["lrsiApplyFractalsEnergy"], applyNormlization=self.vars["lrsiApplyNormalization"], sequential=True)
        # lrsi = lrsi(self.candles, alpha=self.lvars["lrsiAlpha"], sequential=True)
        if self.vars["lrsiApplyNormalization"]:
            lrsiMult = 100
        else:
            lrsiMult = 1
        lrsiOverBought = 0.8 * lrsiMult
        lrsiOverSold = 0.2 * lrsiMult
        # print("lrsiOverBought: ", lrsiOverBought)
        # print("lrsiOverSold: ", lrsiOverSold)
        
        if utils.crossed(lrsi, lrsiOverSold, 'above'):
            self.lrsiSignal = 1
        elif utils.crossed(lrsi, lrsiOverBought, 'below'):
            self.lrsiSignal = -1
        else:
            self.lrsiSignal = self.pre_lrsiSignal
        # print("pre lrsiSignal: ", self.pre_lrsiSignal)
        print("lrsiSignal: ", self.lrsiSignal)

        self.pre_lrsiSignal = self.lrsiSignal

        
    # // Determine Strength of Trend Based on Status of All Indicators
         # MaTrendCalc = StComboTrend == MaTrend ? StComboTrend : 0
        if stComboTrend == self.maTrend(self.lvars["emaFast"], self.lvars["emaSlow"]):
            maTrendCalc = stComboTrend
        else:
            maTrendCalc = 0
        print("maTrend: ", maTrendCalc)
        
        # AroonOscillatorSignalCalc = StComboTrend == AroonOscillatorSignal ? StComboTrend : 0
        if stComboTrend == self.aroonOscillatorSignal:
            aroonOscillatorSignalCalc = stComboTrend
        else:
            aroonOscillatorSignalCalc = 0
        print("aroonOscillatorSignalCalc: ", aroonOscillatorSignalCalc)

        # AroonIndictorTrendCalc = StComboTrend == AroonIndictorTrend ? StComboTrend : 0
        if stComboTrend == self.aroonIndicatorTrend:
            aroonIndicatorTrendCalc = stComboTrend
        else:
            aroonIndicatorTrendCalc = 0
        print("aroonIndicatorTrendCalc: ", aroonIndicatorTrendCalc)
        
        # DmiTrendCalc = StComboTrend == DmiTrend ? StComboTrend : 0
        if stComboTrend == self.dmiTrend:
            dmiTrendCalc = stComboTrend
        else:
            dmiTrendCalc = 0
        print("dmiTrendCalc: ", dmiTrendCalc)
        
        # LrsiSignalCalc = StComboTrend == LrsiSignal ? StComboTrend : 0
        if stComboTrend == self.lrsiSignal:
            lrsiSignalCalc = stComboTrend
        else:
            lrsiSignalCalc = 0
        print("lrsiSignalCalc: ", lrsiSignalCalc)

        # TrendStrength = MaTrendCalc + AroonIndictorTrendCalc + AroonOscillatorSignalCalc + DmiTrendCalc + LrsiSignalCalc
        self.trendStrength = maTrendCalc + aroonIndicatorTrendCalc + aroonOscillatorSignalCalc + dmiTrendCalc + lrsiSignalCalc
        # print("pre trendLength: ", self.pre_trendStrength)
        print("trendLength: ", self.trendStrength)


        # longCondition := barstate.isconfirmed and enableLong and inDateRange and StComboTrend == 1 and TrendStrength >= Threshold and TrendStrength[1] < Threshold
        if stComboTrend == 1 and self.trendStrength >= self.lvars["threshold"] and self.pre_trendStrength < self.lvars["threshold"]:
            st_condition = True
        else:
            st_condition = False

        return st_condition

    @property
    def s_st_condition(self):
        st_condition = False

        # SuperTrend 1 Values on First TimeFrame 
        [st1_trend_tf1, st1_changed_tf1] = st(self.candles, period=self.svars["st1Period"], factor=self.svars["st1Factor"])
        # print("ST1 TF1: ", st1_trend_tf1, st1_changed_tf1)
        
        # SuperTrend 2 Values on First TimeFrame 
        [st2_trend_tf1, st2_changed_tf1] = st(self.candles, period=self.svars["st2Period"], factor=self.svars["st2Factor"])
        # print("ST2 TF1: ", st2_trend_tf1, st2_changed_tf1)
        
        # Determine SuperTrend 1 Values on Second Timeframe
        if self.vars["confirmationResolution"] == "D":
            
            [st1_trend_tf2, st1_changed_tf2] = st2(self.get_candles(self.exchange, self.symbol, '1D'), period=self.svars["st1Period"], factor=self.svars["st1Factor"])
            # print("ST1 TF2: ", st1_trend_tf2, st1_changed_tf2)


        # Determine SuperTrend 2 Values on Second Timeframe
            [st2_trend_tf2, st2_changed_tf2] = st2(self.get_candles(self.exchange, self.symbol, '1D'), period=self.svars["st2Period"], factor=self.svars["st2Factor"])
            # print("ST2 TF2: ", st2_trend_tf2, st2_changed_tf2)


        # Combine the SuperTrends on the first timeframe into one, determine values, and plot
        stComboTrend_Tf1 = 0.0
        if st1_trend_tf1 == st2_trend_tf1:
            stComboTrend_Tf1 = st1_trend_tf1
        else:
            stComboTrend_Tf1 = nan
        print("stComboTrend_tf1: ", stComboTrend_Tf1)

        # Combine the SuperTrends on the second timeframe into one, determine values, and plot
        stComboTrend_Tf2 = 0.0
        if st1_trend_tf2 == st2_trend_tf2:
            stComboTrend_Tf2 = st1_trend_tf2
        else:
            stComboTrend_Tf2 = nan
        print("stComboTrend_tf2: ", stComboTrend_Tf2)
        

        # Determine Overall SuperTrend Direction
        stComboTrend = 0.0
        if self.vars["getConfirmation"]:
            if stComboTrend_Tf1 == stComboTrend_Tf2:
                stComboTrend = stComboTrend_Tf1
            else:
                stComboTrend = nan
        else:
            stComboTrend = stComboTrend_Tf1
        print("stComboTrend_tf: ", stComboTrend)
        
        # Define Aroon Indicator and Determine Status
        [aroonIndicatorUpper, aroonIndicatorLower] = ta.aroon(self.candles, period=self.svars["aroonLength"], sequential=True)
        if utils.crossed(aroonIndicatorUpper, aroonIndicatorLower, 'above'):
            self.aroonIndicatorTrend = 1
        elif  utils.crossed(aroonIndicatorLower, aroonIndicatorUpper, 'above'):
            self.aroonIndicatorTrend = -1
        else:
            self.aroonIndicatorTrend = self.pre_aroonIndicatorTrend
        # print("pre aroonIndicatorTrend: ", self.pre_aroonIndicatorTrend)
        print("aroonIndicatorTrend: ", self.aroonIndicatorTrend)

        self.pre_aroonIndicatorTrend = self.aroonIndicatorTrend

        # Define Aroon Oscillator and Determine Status
        aroonOscillator = ta.aroonosc(self.candles, period=self.svars["aroonLength"], sequential=True)
        if utils.crossed(aroonOscillator, -80, 'above'):
            self.aroonOscillatorSignal = 1
        elif utils.crossed(aroonOscillator, 80, 'below'):
            self.aroonOscillatorSignal = -1
        else:
            self.aroonOscillatorSignal = self.pre_aroonOscillatorSignal
        # print("pre aroonOscillatorSignal: ", self.pre_aroonOscillatorSignal)
        print("aroonOscillatorSignal: ", self.aroonOscillatorSignal)

        self.pre_aroonOscillatorSignal = self.aroonOscillatorSignal

        # Define Directional Movement Index and Determine Values
        [dmiPlus, dmiMinus] = ta.dm(self.candles, period=self.svars["dmiLength"], sequential=True)
        # print("dmi: ", dmiPlus, dmiMinus)

        if utils.crossed(dmiPlus, dmiMinus, 'above'):
            self.dmiTrend = 1
        elif utils.crossed(dmiMinus, dmiPlus, 'above'):
            self.dmiTrend = -1
        else:
            self.dmiTrend = self.pre_dmiTrend
        # print("pre dmiTrend: ", self.pre_dmiTrend)
        print("dmiTrend: ", self.dmiTrend)

        self.pre_dmiTrend = self.dmiTrend

        # Define Laguerre RSI and Determine Values
        # lrsi = ta.lrsi(self.candles, alpha=self.svars["lrsiAlpha"], sequential=True)
        lrsi = lrsi2(self.candles, alpha=self.svars["lrsiAlpha"], feLength=self.svars["lrsiFeLength"], applyFactalsEnergy=self.vars["lrsiApplyFractalsEnergy"], applyNormlization=self.vars["lrsiApplyNormalization"], sequential=True)
        if self.vars["lrsiApplyNormalization"]:
            lrsiMult = 100
        else:
            lrsiMult = 1
        print(lrsiMult)
        lrsiOverBought = 0.8 * lrsiMult
        lrsiOverSold = 0.2 * lrsiMult
        # print("lrsiOverBought: ", lrsiOverBought)
        # print("lrsiOverSold: ", lrsiOverSold)
       
        if utils.crossed(lrsi, lrsiOverSold, 'above'):
            self.lrsiSignal = 1
        elif utils.crossed(lrsi, lrsiOverBought, 'below'):
            self.lrsiSignal = -1
        else:
            self.lrsiSignal = self.pre_lrsiSignal
        # print(" pre lrsiSignal: ", self.pre_lrsiSignal)
        print("lrsiSignal: ", self.lrsiSignal)

        self.pre_lrsiSignal = self.lrsiSignal

        # // Determine Strength of Trend Based on Status of All Indicators
         # MaTrendCalc = StComboTrend == MaTrend ? StComboTrend : 0
        if stComboTrend == self.maTrend(self.svars["emaFast"], self.svars["emaSlow"]):
            maTrendCalc = stComboTrend
        else:
            maTrendCalc = 0
        print("maTrendCalc: ", maTrendCalc)

        # AroonOscillatorSignalCalc = StComboTrend == AroonOscillatorSignal ? StComboTrend : 0
        if stComboTrend == self.aroonOscillatorSignal:
            aroonOscillatorSignalCalc = stComboTrend
        else:
            aroonOscillatorSignalCalc = 0
        print("aroonOscillatorSignalCalc: ", aroonOscillatorSignalCalc)

        # AroonIndictorTrendCalc = StComboTrend == AroonIndictorTrend ? StComboTrend : 0
        if stComboTrend == self.aroonIndicatorTrend:
            aroonIndicatorTrendCalc = stComboTrend
        else:
            aroonIndicatorTrendCalc = 0
        print("aroonIndicatorTrendCalc: ", aroonIndicatorTrendCalc)
        
        # DmiTrendCalc = StComboTrend == DmiTrend ? StComboTrend : 0
        if stComboTrend == self.dmiTrend:
            dmiTrendCalc = stComboTrend
        else:
            dmiTrendCalc = 0
        print("dmiTrendCalc: ", dmiTrendCalc)
        
        # LrsiSignalCalc = StComboTrend == LrsiSignal ? StComboTrend : 0
        if stComboTrend == self.lrsiSignal:
            lrsiSignalCalc = stComboTrend
        else:
            lrsiSignalCalc = 0
        print("lrsiSignalCalc: ", lrsiSignalCalc)
        
        # TrendStrength = MaTrendCalc + AroonIndictorTrendCalc + AroonOscillatorSignalCalc + DmiTrendCalc + LrsiSignalCalc
        self.trendStrength = maTrendCalc + aroonIndicatorTrendCalc + aroonOscillatorSignalCalc + dmiTrendCalc + lrsiSignalCalc
        print("trendLength:", self.trendStrength)
        # shortCondition := barstate.isconfirmed and enableShort and inDateRange and StComboTrend == -1 and TrendStrength <= -Threshold and TrendStrength[1] > -Threshold
        if stComboTrend == -1 and self.trendStrength <= -self.svars["threshold"] and self.pre_trendStrength > -self.svars["threshold"]:
            st_condition = True
        else:
            st_condition = False
        
        return st_condition

    def should_long(self) -> bool:
        if self.onlyLong or self.LS:
            qty = max(min(round(self.risk_qty_long(), self.qty_precision), (self.available_margin - 1)/ self.price), 0)
            if qty != 0 and self.vars["enableLong"] and self.l_st_condition:
                return True
        else:
            return False

    def should_short(self) -> bool:
        if self.onlyShort or self.LS:
            qty = max(min(round(self.risk_qty_short(), self.qty_precision), (self.available_margin - 1)/ self.price), 0)
            if qty != 0 and self.vars["enableShort"] and self.s_st_condition:
                return True
        else:
            return False

    def should_cancel(self) -> bool:
        return True

    def go_long(self):
        qty = max(min(round(self.risk_qty_long(), self.qty_precision), (self.available_margin - 1)/ self.price), 0)
        self.buy = qty, self.price
        self.pyramiding_levels = 1 # Track the pyramiding level
    
        self.entry_atr = self.c_atr
        self.entry_price = self.price
        self.initial_entry = self.price
        self.long_stop  = self.entry_price - self.entry_atr * self.lvars["atrSLMultipier"]
        self.long_tp2   = self.entry_price + self.entry_atr * self.lvars["atrTPMultipier"]
        self.long_tp1   = self.entry_price + self.entry_atr * self.lvars["atrTPMultipier"] / 2
        self.tl_sl_step = 0
        self.tl_tp_step = 0
        half_qty = round(qty/2.0, self.qty_precision)
        
        self.stop_loss   = qty, self.long_stop

        if self.vars["trailing_stoploss"] == 1:
            self.take_profit = [
                (half_qty, self.long_tp1),
                (qty - half_qty, self.long_tp2)
            ]
        elif self.vars["trailing_stoploss"] == 2:
            self.take_profit = [
                (half_qty, self.long_tp1),
                (qty - half_qty, self.long_tp2)
            ]
        else:
            self.take_profit = qty, self.long_tp2

        if self.debug_log >= 1:    
            cmt = 'L['
            
            self.pine_entryts = self.current_candle[0]
            self.pine_cmt = 'L[' #cmt
            self.qty = qty
            self.pine_reduced_ts = 0
           
            total_entry = qty * self.price
            total_loss = qty * self.price - qty * (self.price - self.atr  * self.lvars["atrSLMultipier"])
            total_profit = abs(qty * self.price - qty * (self.price + self.atr * self.lvars["atrTPMultipier"]))
            self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], "Long", 
                self.capital, qty, self.long_stop, self.long_tp1, self.long_tp2])

    def go_short(self):
        qty = max(min(round(self.risk_qty_short(), self.qty_precision), (self.available_margin - 1)/ self.price), 0)
        self.sell = qty, self.price

        self.pyramiding_levels = 1 # Track the pyramiding level

        self.entry_atr = self.c_atr
        self.entry_price = self.price
        self.initial_entry = self.price
        self.short_stop  = self.entry_price + self.entry_atr * self.svars["atrSLMultipier"]
        self.short_tp2   = self.entry_price - self.entry_atr * self.svars["atrTPMultipier"]
        self.short_tp1   = self.entry_price - self.entry_atr * self.svars["atrTPMultipier"] / 2
        self.tl_sl_step = 0
        self.tl_tp_step = 0
        half_qty = round(qty/2.0, self.qty_precision)

        self.stop_loss   = qty, self.short_stop
        if self.vars["trailing_stoploss"] == 1:
            self.take_profit = [
                (half_qty, self.short_tp1),
                (qty - half_qty, self.short_tp2)
            ]
        elif self.vars["trailing_stoploss"] == 2:
            self.take_profit = [
                (half_qty, self.short_tp1),
                (qty - half_qty, self.short_tp2)
            ]
        else:
            self.take_profit = qty, self.short_tp2

        if self.debug_log >= 1:   
            # cmt = 'S['
            
            self.pine_entryts = self.current_candle[0]
            self.pine_cmt = 'S[' #cmt
            self.qty = qty
            self.pine_reduced_ts = 0
            
            total_entry = qty * self.price
            total_loss = qty * self.price - qty * (self.price + self.atr * self.svars["atrSLMultipier"])
            total_profit = abs(qty * self.price - qty * (self.price - self.atr * self.svars["atrTPMultipier"]))
            self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], "Short Entry", 
                self.capital, self.position.qty, total_entry, total_loss, total_profit])

    def move_sltp(self, new_stoploss = 0):
        if self.is_long:
            if new_stoploss == 0:
                self.long_stop   = self.price - self.atr * self.lvars["atrSLMultipier"]
                self.long_tp2    = self.price + self.atr * self.lvars["atrTPMultipier"]
                self.long_tp1    = self.price + self.atr * self.lvars["atrTPMultipier"] / 2
            else:
                self.long_stop  = new_stoploss
            qty = abs(self.position.qty)
            if qty == 0 :
                return
            # self.broker.cancel_all_orders()
            self.stop_loss   = qty, self.long_stop
            cmt = 'Move SLTP'
            if self.vars["trailing_stoploss"] == 1 or self.vars["trailing_stoploss"] == 2:
                # Not yet TP
                half_qty = round(qty/2.0, self.qty_precision)
                athird_qty = round(qty/3.0, self.qty_precision)

                if self.tl_tp_step == 0:    
                    self.take_profit = [
                        (half_qty, self.long_tp1),
                        (utils.subtract_floats(qty,half_qty), self.long_tp2)
                        ]
                else:
                    # already take TP1
                    if self.pyramiding_levels == 1 or athird_qty == 0:
                        self.take_profit = [
                            (qty, self.long_tp2)
                            ]
                    else:
                        # TP 1/2 
                        self.take_profit = [
                            (athird_qty, self.long_tp1),
                            (utils.subtract_floats(qty,athird_qty), self.long_tp2)
                            ]
            else:
                self.take_profit = abs(self.position.qty), self.long_tp2

            if self.debug_log >= 1:
                self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, 
                    self.capital, self.position.qty, self.long_stop, self.long_tp1, self.long_tp2, self.pyramiding_levels])

        if self.is_short:
            # self.entry_atr   = self.atr
            # self.entry_price = self.price
            if new_stoploss == 0:
                self.short_stop  = self.price + self.atr * self.svars["atrSLMultipier"]
                self.short_tp2   = self.price - self.atr * self.svars["atrTPMultipier"]
                self.short_tp1   = self.price - self.atr * self.svars["atrTPMultipier"] / 2
            else:
                self.short_stop  = new_stoploss
            qty = abs(self.position.qty)
            if qty == 0 :
                return
            # self.broker.cancel_all_orders()
            self.stop_loss = qty, self.short_stop
            cmt = 'Move SLTP'
            if self.vars["trailing_stoploss"] == 1 or self.vars["trailing_stoploss"] == 2:
                # Not yet TP
                half_qty = round(qty/2, self.qty_precision)
                athird_qty = round(qty/3, self.qty_precision)

                if self.tl_tp_step == 0:    
                    self.take_profit = [
                        (half_qty, self.short_tp1),
                        (utils.subtract_floats(qty, half_qty), self.short_tp2)
                        ]
                else:
                    # already take TP1
                    if self.pyramiding_levels == 1 or athird_qty == 0:
                        self.take_profit = [
                            (qty, self.short_tp2)
                            ]
                    else:
                        # TP 1/2 
                        self.take_profit = [
                            (athird_qty, self.short_tp1),
                            (utils.subtract_floats(qty, athird_qty), self.short_tp2)
                            ]     
            else:
                self.take_profit = qty, self.short_tp2

            if self.debug_log >= 1:
                self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, 
                    self.capital, qty, self.short_stop, self.short_tp1, self.short_tp2, self.pyramiding_levels])

        return


    def update_position(self):
        # Call every new candle when in a position
        # Handle for pyramiding rules
        if self.is_long and self.should_long():
            if self.pyramiding_levels < self.vars["maximum_pyramiding_levels"]:
                #qty = round(self.risk_qty_short(),2) * self.vars["pyramiding_threshold"]
                qty = max(min(round(self.risk_qty_long()  * self.vars["pyramiding_threshold"], self.qty_precision), (self.available_margin - 1)/ self.price), 0)
               
                #utils.size_to_qty(self.unit_qty_long() * self.vars["pyramiding_threshold"], self.price, fee_rate=self.fee_rate)
                if qty > 0:
                    self.buy = qty, self.price
                    self.pyramiding_levels += 1
                    cmt = 'Long Pyramid'
                    if self.debug_log >= 1:
                        self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, 
                            self.capital, self.position.qty, self.long_stop, self.long_tp1, self.long_tp2, self.pyramiding_levels])

                    # Should Move after increases
                    self.entry_atr   = self.c_atr
                    self.entry_price = self.price
                    # self.move_sltp() 
            elif self.vars["move_on_no_entry"]:
                # Update stop loss and take profit   
                self.entry_atr   = self.c_atr
                self.entry_price = self.price
                self.move_sltp() 
            return     
 
        if self.is_short and self.should_short():
            if self.pyramiding_levels < self.vars["maximum_pyramiding_levels"]:
                #qty = round(self.risk_qty_short(),2) * self.vars["pyramiding_threshold"]
                qty = max(min(round(self.risk_qty_short() * self.vars["pyramiding_threshold"], self.qty_precision), (self.available_margin - 1)/ self.price), 0)
                #qty = utils.size_to_qty(self.unit_qty_short() * self.vars["pyramiding_threshold"], self.price, fee_rate=self.fee_rate)
                if qty == 0 :
                    return
                if qty > 0:
                    self.sell = qty, self.price
                    self.pyramiding_levels += 1
                    cmt = 'Short Pyramid'
                    if self.debug_log >= 1:
                        self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, 
                            self.capital, self.position.qty, self.long_stop, self.long_tp1, self.long_tp2, self.pyramiding_levels])
                    # Should Move after increases
                    self.entry_atr   = self.c_atr
                    self.entry_price = self.price
                    # self.move_sltp()  
 
            elif self.vars["move_on_no_entry"]:
                # Update stop loss and take profit
                self.entry_atr   = self.c_atr
                self.entry_price = self.price
                self.move_sltp()
            return
        # if not pyramiding, contunue update trailing
        self.trailing_update()      

    def trailing_update(self):
        # Trailing
        new_long_stop = 0
        new_short_stop = 0
        if self.is_long and self.vars['trailing_stoploss'] == 2 and self.position.qty > 0:
            if self.tl_sl_step == 0 and self.long_stop < self.entry_price and \
              self.price > self.entry_price + self.atr * self.lvars['atrSLMultipier'] * self.lvars['trailingTrigger1']:
                self.tl_sl_step += 1
                new_long_stop = self.entry_price - self.atr * self.lvars['atrSLMultipier'] *(1 - self.lvars['trailingSLPercent1'])
                if self.debug_log >= 1:
                    self.pine_cmt += f"M1 {new_long_stop:.2f} "

            elif self.tl_sl_step <= 1 and self.long_stop < self.entry_price and self.high >= self.long_tp1:
                self.tl_sl_step = 2
                new_long_stop = self.entry_price - self.atr * self.lvars['atrSLMultipier'] *(1 - self.lvars['trailingSLPercent2'])
                if self.debug_log >= 1:
                    self.pine_cmt += f"M2 {new_long_stop:.2f} "

            elif self.tl_sl_step == 2 and \
              self.high > self.entry_price + self.atr * self.lvars['atrTPMultipier'] * self.lvars['trailingTrigger2']:
                self.tl_sl_step += 1
                new_long_stop = self.entry_price + self.atr * self.lvars['atrTPMultipier'] *(self.lvars['trailingSLPercent3'] - 1)
                if self.debug_log >= 1:
                    self.pine_cmt += f"M3 {new_long_stop:.2f} "

        if self.is_short and self.vars['trailing_stoploss'] == 2 and self.position.qty < 0:
            if self.tl_sl_step == 0 and self.short_stop > self.entry_price and \
              self.price < self.entry_price - self.atr * self.svars['atrSLMultipier'] * self.svars['trailingTrigger1']:
                self.tl_sl_step += 1
                new_short_stop = self.entry_price + self.atr * self.svars['atrSLMultipier'] *(1 - self.svars['trailingSLPercent1'])
                if self.debug_log >= 1:
                    self.pine_cmt += f"M1 {new_short_stop:.2f} "

            elif self.tl_sl_step <= 1 and self.short_stop > self.entry_price and self.low <= self.short_tp1:
                self.tl_sl_step = 2
                new_short_stop = self.entry_price + self.atr * self.svars['atrSLMultipier'] *(1 - self.svars['trailingSLPercent2'])
                if self.debug_log >= 1:
                    self.pine_cmt += f"M2 {new_short_stop:.2f} "
            elif self.tl_sl_step == 2 and \
              self.low < self.entry_price - self.atr * self.svars['atrTPMultipier'] * self.svars['trailingTrigger2']:
                self.tl_sl_step += 1
                new_short_stop = self.entry_price - self.atr * self.svars['atrTPMultipier'] *(self.svars['trailingSLPercent3'] - 1)
                if self.debug_log >= 1:
                    self.pine_cmt += f"M3 {new_short_stop:.2f} "

        if new_long_stop > 0:
            qty = abs(self.position.qty)
            if qty == 0 :
                return
            self.long_stop = new_long_stop
            if new_long_stop > self.price:
                # print("Move Long SL Liquidate")
                cmt = "Move SL: Liquidate"
                self.liquidate()
            else:
                # print("Move Long SL Only")
                # self.cancel_stop_orders(self.orders)
                # self.stop_loss   = qty, self.long_stop
                cmt = "Move SL"
                self.move_sltp(new_long_stop)

            # self.cancel_stop_orders(self.orders)
            
            if self.debug_log >= 1:
                self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, 
                    self.capital, qty, self.long_stop, self.long_tp1, self.long_tp2])

        if new_short_stop > 0:
            qty = abs(self.position.qty)
            if qty == 0:
                return
            self.short_stop = new_short_stop
            # sl = self.stop_loss
            # tp = self.take_profit
            # self.cancel_stop_orders(self.orders)
            if new_short_stop < self.price:
                # print("Move Short SL Liquidate")
                cmt = "Move SL: Liquidate"
                self.liquidate()
            else:
                # print("Move Short SL Only")
                # self.cancel_stop_orders(self.orders)
                # self.stop_loss   = qty, self.short_stop
                cmt = "Move SL"
                self.move_sltp(new_short_stop)
                # self.view_orders(self.orders)
            # self.take_profit = tp
            if self.debug_log >= 1:
                self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, 
                    self.capital, qty, self.short_stop, self.short_tp1, self.short_tp2])
    def view_orders(self,orders):
        for order in orders:

            print(f"Type {order.type} active {order.is_active} price ={order.price}")
    def on_increased_position(self, order):
        # Reset stop loss and take profit

        # Must clear all orders before setting pyramiding SL TP
        if self.pyramiding_levels == 2:
            self.broker.cancel_all_orders()
        self.move_sltp()

    
    def cancel_stop_orders(self,orders):
        for order in orders:
            if order.type == "STOP":
                order.cancel()
                #self.broker.cancel_order(order)
 
    def on_close_position(self, order):
        self.last_was_profitable = True
        # print(f"Close Position {self.price} {self.short_stop} {self.long_stop}")

        if self.debug_log >= 1 and self.short_stop > 0:
            self.pine_short(self.pine_cmt + "]", self.pine_entryts, self.qty, self.current_candle[0], self.short_stop, self.short_tp2)
   
        if self.debug_log >= 1 and self.long_stop > 0:
            self.pine_long(self.pine_cmt + "]", self.pine_entryts, self.qty, self.current_candle[0], self.long_stop, self.long_tp2)

        price = order.price
        if self.debug_log >= 1:
            if (self.short_stop > 0 and price < self.initial_entry) or (self.long_stop and price > self.initial_entry):
                wl = 'Win'
            else:
                wl = 'Lose'
            if price == self.short_stop or self.price == self.long_stop:
                cmt = f"Exit: {wl} Hit SL"
            elif price == self.short_tp1 or self.price == self.long_tp1:
                cmt = f"Exit: {wl} TP1"
            elif price == self.short_tp2 or self.price == self.long_tp2:
                cmt = f"Exit: {wl} TP2"
            else:
                cmt = f"Exit: {wl} Moved SL"
            row = len(self.data_log) + 2
            self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], cmt, self.capital, self.position.qty ,
                '','','', wl,f"=I{row}-I{row - 1}"])

        self.short_stop = 0
        self.short_tp1 = 0
        self.short_tp2 = 0
        self.long_stop = 0
        self.long_tp1 = 0
        self.long_tp2 = 0
        self.pyramiding_levels = 0 
        self.initial_entry = 0  
    
    def on_reduced_position(self, order):
        if self.vars["trailing_stoploss"] == 1 and abs(self.position.qty) > 0:
            self.stop_loss = (abs(self.position.qty), self.entry_price) 
        if self.vars["trailing_stoploss"] == 2 and abs(self.position.qty) > 0:
            self.tl_tp_step += 1

        if self.debug_log >= 1 and self.short_stop > 0:
            self.pine_reduced_ts = self.current_candle[0]
            self.pine_reduced_price = self.short_tp1
   
        if self.debug_log >= 1 and self.long_stop > 0:
            self.pine_reduced_ts = self.current_candle[0]
            self.pine_reduced_price = self.long_tp1

        if self.debug_log >= 1:
            row = len(self.data_log) + 2
            self.data_log.append([self.index, self.ts, self.open, self.close, self.high, self.low, self.current_candle[5], "Reduce: WIN TP1", self.capital, self.position.qty,'','','','Win',f"=I{row}-I{row - 1}"])
    
    def on_cancel(self):
        self.pyramiding_levels = 0 

        
    def watch_list(self):
        return [
            
        ]
    def terminate(self):
        print(f'Backtest is done, Total Capital : {self.capital}')
        if self.debug_log >= 1:
            print(self.indicator_log)
            tu.write_csv(type(self).__name__ +'-' + self.symbol +'-' + self.timeframe, self.data_header, self.data_log)
            tu.write_csv(type(self).__name__ +'-' + self.symbol +'-' + self.timeframe + '-indicator', self.indicator_header, self.indicator_log)
            tu.write_pine(type(self).__name__ +'-' + self.symbol +'-' + self.timeframe, self.starting_balance, self.pine_log)

    def pine_long(self, comment, ts, qty, ts_out, sl, tp):
        self.pine_orderid += 1
        ts = int(ts) + jh.timeframe_to_one_minutes(self.timeframe) * 60 * 1000
        
        self.pine_log += f'strategy.entry("{self.pine_orderid}", strategy.long, {qty}, {tp:.2f}, when = time_close == {ts:.0f}, comment="{comment}")\n'
        self.pine_log += f'strategy.exit("{self.pine_orderid}","{self.pine_orderid}", stop = {sl:.2f}, limit = {tp:.2f}, when = time_close >= {ts_out:.0f})\n'

    def pine_short(self, comment, ts, qty, ts_out, sl, tp):
        self.pine_orderid += 1
        ts = int(ts) + jh.timeframe_to_one_minutes(self.timeframe) * 60 * 1000
        
        self.pine_log += f'strategy.entry("{self.pine_orderid}", strategy.short, {qty}, {tp:.2f}, when = time_close == {ts:.0f}, comment="{comment}")\n'
        self.pine_log += f'strategy.exit("{self.pine_orderid}","{self.pine_orderid}", stop = {sl:.2f}, limit = {tp:.2f}, when = time_close >= {ts_out:.0f})\n'

   
