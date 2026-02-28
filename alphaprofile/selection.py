from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


def _zscore(series: pd.Series) -> pd.Series:
    if series.std() == 0 or series.isna().all():
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.mean()) / series.std()


def select_best(
    summary_df: pd.DataFrame,
    constraints: Optional[Dict[str, float]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    if summary_df.empty:
        return summary_df

    df = summary_df.copy()
    constraints = constraints or {}
    weights = weights or {
        "mean_signed_return": 0.5,
        "hit_rate": 0.3,
        "adverse_selection": 0.2,
    }

    for key, value in constraints.items():
        if key in df.columns:
            if key.startswith("max_"):
                df = df[df[key] <= value]
            else:
                df = df[df[key] >= value]

    if df.empty:
        return df

    score = pd.Series(0.0, index=df.index)
    for metric, weight in weights.items():
        if metric not in df.columns:
            continue
        normed = _zscore(df[metric])
        if metric == "adverse_selection":
            normed = -normed
        score += weight * normed

    df["score"] = score
    return df.sort_values(by="score", ascending=False)
