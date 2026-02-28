from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, List, Optional

import pandas as pd

from .data import ForwardReturnSpec, compute_forward_returns, get_alpha_columns
from .metrics import (
    adverse_selection_proxy,
    conditional_return_distribution,
    decay_curve,
    hit_rate,
    regime_dependence,
)


@dataclass(frozen=True)
class ProfileConfig:
    horizon: pd.Timedelta = pd.Timedelta("1s")
    decay_horizons: Iterable[pd.Timedelta] = (
        pd.Timedelta("1s"),
        pd.Timedelta("5s"),
        pd.Timedelta("10s"),
        pd.Timedelta("30s"),
        pd.Timedelta("60s"),
        pd.Timedelta("120s"),
        pd.Timedelta("300s"),
    )
    group_col: str = "name"


def _available_horizons(df: pd.DataFrame) -> List[pd.Timedelta]:
    horizons = []
    for col in df.columns:
        match = re.match(r"^ret(\d+)$", col)
        if not match:
            continue
        seconds = int(match.group(1))
        horizons.append(pd.Timedelta(seconds=seconds))
    return sorted(horizons)


def run_profile(
    df: pd.DataFrame,
    signal_cols: Optional[List[str]] = None,
    config: Optional[ProfileConfig] = None,
    out_dir: Optional[str | Path] = None,
) -> pd.DataFrame:
    if config is None:
        config = ProfileConfig()
    if signal_cols is None:
        signal_cols = get_alpha_columns(df)

    available_horizons = set(_available_horizons(df))
    decay_horizons = [
        h for h in config.decay_horizons if h in available_horizons
    ]
    if not decay_horizons:
        decay_horizons = list(available_horizons)

    df = compute_forward_returns(
        df, ForwardReturnSpec(horizon=config.horizon, group_col=config.group_col)
    )

    summaries = []
    details = {}

    for col in signal_cols:
        hr = hit_rate(df[col], df["ret_forward"])
        mean_ret = (df[col].apply(lambda x: 1 if x > 0 else -1) * df["ret_forward"]).mean()
        decay = decay_curve(df, col, decay_horizons, config.group_col)
        regime = regime_dependence(df, col)
        adverse = adverse_selection_proxy(df, col)
        cond = conditional_return_distribution(df[col], df["ret_forward"])

        summaries.append(
            {
                "alpha": col,
                "hit_rate": hr["hit_rate"],
                "hit_n": hr["n"],
                "mean_signed_return": mean_ret,
                "adverse_selection": adverse["adverse_selection"],
                "adverse_n": adverse["n"],
            }
        )
        details[col] = {
            "decay_curve": decay,
            "regime_dependence": regime,
            "conditional_distribution": cond,
        }

    summary_df = pd.DataFrame(summaries).sort_values(
        by=["mean_signed_return"], ascending=False
    )

    if out_dir:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        summary_df.to_csv(out_path / "summary.csv", index=False)
        summary_df.to_json(out_path / "summary.json", orient="records")
        for alpha, components in details.items():
            alpha_dir = out_path / alpha
            alpha_dir.mkdir(parents=True, exist_ok=True)
            components["decay_curve"].to_csv(alpha_dir / "decay.csv", index=False)
            components["regime_dependence"].to_csv(alpha_dir / "regime.csv", index=False)
            components["conditional_distribution"].to_csv(
                alpha_dir / "conditional.csv", index=False
            )

    return summary_df
