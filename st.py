from typing import Union
from collections import namedtuple
import math

import numpy as np
import talib
try:
    from numba import njit
except ImportError:
    njit = lambda a : a
import jesse.indicators as ta
import lib


SuperTrend = namedtuple('SuperTrend', ['stTrend', 'stTrendUp', 'stTrendDown'])

def st(candles: np.ndarray, atr, period , factor: float = 3, sequential: bool = False) -> Union[float, np.ndarray]:
    """
    SuperTrend
    :param candles: np.ndarray
    :param period: int - default=14
    :param factor: float - default=3
    :param sequential: bool - default=False
    :return: SuperTrend(trend, changed)
    """
    stUp = (candles[:, 3] + candles[:, 4])/2 - (factor * atr)
    stDn = (candles[:, 3] + candles[:, 4])/2 + (factor * atr)
    stTrend = np.zeros(len(candles))
    stTrendUp = np.zeros(len(candles))
    stTrendDown = np.zeros(len(candles))

    pre_stTrend = -1 
    for i in range(period, len(candles)):
        close = candles[:, 2][i]
        pre_close = candles[:, 2][i-1]
        pre_stTrendUp = stUp[i-1]
        pre_stTrendDown = stDn[i-1]
        if pre_close > pre_stTrendUp:
            stTrendUp[i] = max(stUp[i], pre_stTrendUp)
        else:
            stTrendUp[i] = stUp[i]

        if pre_close < pre_stTrendDown:
            stTrendDown[i] = min(stDn[i], pre_stTrendDown)
        else:
            stTrendDown[i] = stDn[i]

        if close > pre_stTrendDown:
            stTrend[i] = 1
        elif close < pre_stTrendUp:
            stTrend[i] = -1
        else:
            # stTrend[i] = lib.nz(pre_stTrend, 1)
            if math.isnan(pre_stTrend):
                stTrend[i] = 1
            else:
                stTrend[i] = pre_stTrend
                
        pre_stTrend = stTrend[i]
            
    if sequential:
        return SuperTrend(stTrend, stTrendUp, stTrendDown)
    else:
        return SuperTrend(stTrend[-1], stTrendUp[-1], stTrendDown[-1])
