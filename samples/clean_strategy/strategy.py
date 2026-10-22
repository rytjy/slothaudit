import pandas as pd

FEE_BPS = 4.5
COOLDOWN = 24


def run(df, capital=10000):
    equity = capital
    last_entry = -10 ** 9
    trades = []
    for i in range(2, len(df) - 1):
        signal = df["close"].iloc[i] > df["close"].iloc[i - 1] > df["close"].iloc[i - 2]
        if signal and i - last_entry >= COOLDOWN:
            entry = df["open"].iloc[i + 1]          # next bar's open, not this bar
            exit_ = df["close"].iloc[i + 2]
            gross = (exit_ - entry) * 100
            cost = (entry + exit_) * 100 * FEE_BPS / 10000.0
            pnl = gross - cost
            equity += pnl
            trades.append({"i": i, "pnl": pnl})
            last_entry = i
    return equity, trades


def drawdown(equity_curve):
    peak = equity_curve[0]
    raw = []
    for v in equity_curve:
        peak = max(peak, v)                          # peak never reset by a cap
        raw.append((v - peak) / peak)
    return min(raw), raw
