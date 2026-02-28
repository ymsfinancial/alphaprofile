from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .data import ForwardReturnSpec, compute_forward_returns


def hit_rate(signal: pd.Series, ret_forward: pd.Series) -> dict:
    valid = signal.notna() & ret_forward.notna() & (signal != 0)
    if valid.sum() == 0:
        return {"hit_rate": np.nan, "n": 0}
    s = np.sign(signal[valid])
    r = np.sign(ret_forward[valid])
    return {"hit_rate": (s == r).mean(), "n": int(valid.sum())}


def conditional_return_distribution(
    signal: pd.Series,
    ret_forward: pd.Series,
    bins: int = 10,
) -> pd.DataFrame:
    df = pd.DataFrame({"signal": signal, "ret": ret_forward}).dropna()
    if df.empty:
        return pd.DataFrame()
    df["bucket"] = pd.qcut(df["signal"], bins, duplicates="drop")
    stats = (
        df.groupby("bucket")["ret"]
        .agg(["mean", "median", "std", "skew", "count"])
        .reset_index()
    )
    quantiles = df.groupby("bucket")["ret"].quantile([0.01, 0.05, 0.95, 0.99])
    quantiles = quantiles.unstack(level=-1).reset_index()
    quantiles.columns = ["bucket", "q01", "q05", "q95", "q99"]
    return stats.merge(quantiles, on="bucket", how="left")


def decay_curve(
    df: pd.DataFrame,
    signal_col: str,
    horizons: Iterable[pd.Timedelta],
    group_col: str = "name",
) -> pd.DataFrame:
    rows = []
    for horizon in horizons:
        spec = ForwardReturnSpec(horizon=horizon, group_col=group_col)
        temp = compute_forward_returns(df, spec)
        corr = temp[signal_col].corr(temp["ret_forward"])
        rows.append({"horizon": horizon, "ic": corr})
    return pd.DataFrame(rows)


def regime_dependence(
    df: pd.DataFrame,
    signal_col: str,
    ret_col: str = "ret_forward",
    mid_col: str = "mid",
    window: int = 50,
    regimes: int = 3,
) -> pd.DataFrame:
    temp = df[[signal_col, ret_col, mid_col]].dropna().copy()
    if temp.empty:
        return pd.DataFrame()
    temp["mid_ret"] = temp[mid_col].pct_change()
    temp["vol"] = temp["mid_ret"].rolling(window).std()
    temp = temp.dropna(subset=["vol"])
    if temp.empty:
        return pd.DataFrame()
    temp["regime"] = pd.qcut(temp["vol"], regimes, duplicates="drop")
    stats = (
        temp.groupby("regime")[ret_col]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    stats["signal_ic"] = (
        temp.groupby("regime")[signal_col].corr(temp[ret_col]).values
    )
    return stats


def adverse_selection_proxy(
    df: pd.DataFrame,
    signal_col: str,
    ret_short: str = "ret_forward",
) -> dict:
    temp = df[[signal_col, ret_short]].dropna()
    if temp.empty:
        return {"adverse_selection": np.nan, "n": 0}
    signed_ret = np.sign(temp[signal_col]) * temp[ret_short]
    return {"adverse_selection": -signed_ret.mean(), "n": int(len(temp))}
