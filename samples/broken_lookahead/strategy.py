import numpy as np
import pandas as pd


def run(df, capital=10000):
    equity = capital
    trades = []
    for i in range(2, len(df) - 1):
        if df["close"][i] > df["close"][i - 1] and df["close"][i - 1] > df["close"][i - 2]:
            entry = df["close"][i]          # fill on the bar that produced the signal
            exit_ = df["close"][i + 1]
            pnl = (exit_ - entry) * 100
            equity += pnl
            trades.append({"i": i, "pnl": pnl})
    peak = capital
    mdd = 0
    for t in trades:
        cap = t.get("cap")
        if cap:
            peak = cap
        peak = max(peak, peak + t["pnl"])
        mdd = min(mdd, peak - (peak + t["pnl"]))
    signal = pd.Series(np.diff(df["close"], prepend=df["close"][0]))
    return equity, mdd, signal
