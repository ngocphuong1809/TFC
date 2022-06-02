from typing import Union

from matplotlib.pyplot import close
import lib
import numpy as np
from cmath import nan

try:
    from numba import njit
except ImportError:
    njit = lambda a : a

from jesse.helpers import slice_candles
import math


def lrsi2(candles: np.ndarray, alpha: float = 0.2, feLength: int = 13, applyFactalsEnergy: bool = True, applyNormlization: bool = True, sequential: bool = False) -> Union[float, np.ndarray]:
    """
    RSI Laguerre Filter

    :param candles: np.ndarray
    :param alpha: float - default: 0.2
    :param sequential: bool - default: False

    :return: float | np.ndarray
    """
    candles = slice_candles(candles, sequential)

    open = candles[:, 1]
    close = candles[:, 2]
    high = candles[:, 3]
    low = candles[:, 4]

    highest = high[0]
    lowest = low[0]
    for i in range(feLength):
        if i!= 0:
            if high[-i] < high[-(i-1)]:
                highest = high[-(i-1)]
            if low[-i] > low[-(i-1)]:
                lowest = low[-(i-1)]

    price = (candles[:, 3] + candles[:, 4]) / 2
    # lrsiOC = np.copy(price)
    # lrsiHC = np.copy(price)
    # lrsiLC = np.copy(price)
    # lrsiFeSrc = np.copy(price)
    # lrsiFeAlpha = np.copy(price)
    # lrsiAlphaCalc = np.copy(price)
    lrsiL0 = np.copy(price)
    lrsiL1 = np.copy(price)
    lrsiL2 = np.copy(price)
    lrsiL3 = np.copy(price)
    rsi = np.zeros_like(price)

    for i in range(lrsiL0.shape[0]):
        lrsiOC = (open[i] + close[i-1])/2
        lrsiHC = max(high[i], close[i-1])
        lrsiLC = min(low[i], close[i-1])
        lrsiFeSrc = (lrsiOC + lrsiHC + lrsiLC + close[i])/4
        # print("A: ",lrsiHC - lrsiLC)
        # print("B: ", highest - lowest)
        if lrsiHC - lrsiLC <= 0 or highest - lowest <= 0:
            lrsiFeAlpha = 1
        else:
            lrsiFeAlpha = math.log((lrsiHC - lrsiLC)/(highest - lowest) + feLength)/math.log(feLength)
        if applyFactalsEnergy:
            lrsiAlphaCalc = lrsiFeAlpha
            temp = lrsiFeSrc
        else:
            lrsiAlphaCalc = alpha
            temp = alpha 

        gamma = 1 - lrsiAlphaCalc
        lrsiL0[i] = lrsiAlphaCalc * temp + gamma * lrsiL0[i-1]
        lrsiL1[i] = -gamma * lrsiL0[i] + lrsiL0[i-1] + gamma * lrsiL1[i-1]
        lrsiL2[i] = -gamma * lrsiL1[i] + lrsiL1[i-1] + gamma * lrsiL2[i-1]
        lrsiL3[i] = -gamma * lrsiL1[i] + lrsiL2[i-1] + gamma * lrsiL3[i-1]

    for i in range(candles[:, 2].shape[0]):
        lrsiCU = 0.0
        lrsiCD = 0.0

        if lrsiL0[i] >= lrsiL1[i]:
            lrsiCU = lrsiL0[i] - lrsiL1[i]
        else:
            lrsiCD = lrsiL1[i] - lrsiL0[i]
        
        if lrsiL1[i] >= lrsiL2[i]:
            lrsiCU = lrsiCU + lrsiL1[i] - lrsiL2[i]
        else:
            lrsiCD = lrsiCD + lrsiL2[i] - lrsiL1[i]

        if lrsiL2[i] >= lrsiL3[i]:
            lrsiCU = lrsiCU + lrsiL2[i] - lrsiL3[i]
        else:
            lrsiCD = lrsiCD + lrsiL3[i] - lrsiL2[i]
        
        if lrsiCU + lrsiCD != 0:
            if applyNormlization:
                rsi[i] = 100 * lrsiCU / (lrsiCU + lrsiCD)
            else:
                rsi[i] = lrsiCU / (lrsiCU + lrsiCD)
        else:
            rsi[i] = 0
 
    if sequential:
        return rsi
    else:
        return None if np.isnan(rsi[-1]) else rsi[-1]


