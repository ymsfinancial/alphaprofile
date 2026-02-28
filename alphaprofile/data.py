from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class ForwardReturnSpec:
    horizon: pd.Timedelta
    group_col: str = "name"


def list_archive_files(data_dir: str | Path) -> List[Path]:
    data_path = Path(data_dir)
    return sorted(data_path.glob("*.bn.ob.archive"))


def load_archive(file_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    if "date" in df.columns and "time" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["date"].astype(str) + " " + df["time"].astype(str),
            errors="coerce",
        )
    if "touch_bid" in df.columns and "touch_ask" in df.columns:
        df["mid"] = (df["touch_bid"] + df["touch_ask"]) / 2.0
    _add_forward_returns_from_touch(df)
    return df


def _format_horizon_label(raw: str) -> str:
    try:
        value = float(raw)
    except ValueError:
        return raw.replace(".", "p")
    if value.is_integer():
        return str(int(value))
    return str(value).replace(".", "p")


def _add_forward_returns_from_touch(df: pd.DataFrame) -> None:
    if df.empty:
        return
    bid_cols = [col for col in df.columns if col.startswith("touch_bid@")]
    for bid_col in bid_cols:
        match = re.match(r"^touch_bid@(.+)$", bid_col)
        if not match:
            continue
        horizon_raw = match.group(1)
        ask_col = f"touch_ask@{horizon_raw}"
        if ask_col not in df.columns:
            continue
        label = _format_horizon_label(horizon_raw)
        mid_col = f"mid{label}"
        ret_col = f"ret{label}"
        if mid_col not in df.columns:
            df[mid_col] = (df[bid_col] + df[ask_col]) / 2.0
        if "mid" in df.columns and ret_col not in df.columns:
            df[ret_col] = (df[mid_col] - df["mid"]) / df["mid"]


def load_archives(files: Iterable[str | Path]) -> pd.DataFrame:
    frames = [load_archive(path) for path in files]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def get_alpha_columns(df: pd.DataFrame) -> List[str]:
    return [
        col
        for col in df.columns
        if col.startswith("ob")
        and "_ret" in col
        and col.endswith("_")
    ]


def compute_forward_returns(
    df: pd.DataFrame,
    spec: ForwardReturnSpec,
    timestamp_col: str = "timestamp",
    mid_col: str = "mid",
) -> pd.DataFrame:
    if df.empty:
        return df
    if timestamp_col not in df.columns:
        raise ValueError("timestamp column missing; ensure load_archive ran")
    if mid_col not in df.columns:
        raise ValueError("mid column missing; ensure touch_bid/ask present")

    seconds = spec.horizon.total_seconds()
    if not seconds.is_integer():
        raise ValueError("Only integer-second horizons supported by archive snapshots")

    label = str(int(seconds))
    ret_col = f"ret{label}"
    mid_forward_col = f"mid{label}"
    if ret_col not in df.columns:
        raise ValueError(f"Missing forward return column: {ret_col}")

    df = df.copy()
    df["ret_forward"] = df[ret_col]
    if mid_forward_col in df.columns:
        df["mid_forward"] = df[mid_forward_col]
    return df
