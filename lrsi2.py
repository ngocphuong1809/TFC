from typing import Union
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
    # candles = slice_candles(self.candles, sequential=True)
    pre_close = candles[-2:,2][0]

    open = candles[:, 1][-1]
    close = candles[:, 2][-1]
    high = candles[:, 3][-1]
    low = candles[:, 4][-1]
    if pre_close == nan:
        pre_close = 0
    lrsiOC = (open + pre_close) / 2
    lrsiHC = max(high, pre_close)
    lrsiLC = min(low, pre_close)
    lrsiFeSrc = (lrsiOC + lrsiHC + lrsiLC + close) / 4
    
    h = candles[:, 3]
    l = candles[:, 4]
    highest = h[0]
    lowest = l[0]
    for i in range(feLength):
        if i!= 0:
            if h[-i] < h[-(i-1)]:
                highest = h[-(i-1)]
            if l[-i] > l[-(i-1)]:
                lowest = l[-(i-1)]
    # LrsiFeAlpha = log(sum((LrsiHC - LrsiLC) / (highest(LrsiFeLength) - lowest(LrsiFeLength)), LrsiFeLength)) / log(LrsiFeLength)
    if lrsiHC - lrsiLC <= 0 or (highest - lowest):
        lrsiFeAlpha = 0
    else:
        lrsiFeAlpha = math.log(((lrsiHC - lrsiLC)/(highest - lowest)) + feLength) / math.log(feLength)   
    
    if applyFactalsEnergy:
        lrsiAlphaCalc = lrsiFeAlpha
    else:
        lrsiAlphaCalc = alpha
    price = (candles[:, 3] + candles[:, 4]) / 2
    l0 = np.copy(price)
    l1 = np.copy(price)
    l2 = np.copy(price)
    l3 = np.copy(price)
    rsi = np.zeros_like(price)


    for i in range(l0.shape[0]):

        if applyFactalsEnergy:
            temp = lrsiFeSrc
        else:
            temp = close

        gamma = 1 - lrsiAlphaCalc
        l0[i] = lrsiAlphaCalc * temp + gamma * l0[i-1]
        l1[i] = -gamma * l0[i] + l1[i-1] + gamma * l1[i-1]
        l2[i] = -gamma * l1[i] + l1[i-1] + gamma * l2[i-1]
        l3[i] = -gamma * l1[i] + l1[i-1] + gamma * l3[i-1]

    for i in range(candles[:, 2].shape[0]):
        cu = 0
        cd = 0
        if l0[i] >= l1[i]:
            cu = l0[i] - l1[i]
        else:
            cd = l1[i] - l0[i]
        
        if l1[i] >= l2[i]:
            cu = cu + l1[i] - l2[i]
        else:
            cd = cd + l2[i] - l1[i]

        if l2[i] >= l3[i]:
            cu = cu + l2[i] - l3[i]
        else:
            cd = cd + l3[i] - l2[i]

        if cu + cd != 0:
            if applyNormlization:
                rsi[i] = 100 * cu / (cu + cd)
            else:
                rsi[i] = cu / (cu + cd)
        else:
            rsi[i] = 0

    if sequential:
        return rsi
    else:
        return None if np.isnan(rsi[-1]) else rsi[-1]


