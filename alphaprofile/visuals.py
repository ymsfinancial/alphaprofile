from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_decay_curve(decay_df: pd.DataFrame, title: str = "Decay Curve") -> plt.Figure:
    fig, ax = plt.subplots()
    ax.plot(decay_df["horizon"].astype(str), decay_df["ic"], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Horizon")
    ax.set_ylabel("IC")
    ax.grid(True)
    return fig


def plot_hit_rate_by_bucket(bucket_df: pd.DataFrame, title: str = "Conditional Return") -> plt.Figure:
    fig, ax = plt.subplots()
    ax.bar(bucket_df["bucket"].astype(str), bucket_df["mean"], color="#4C78A8")
    ax.set_title(title)
    ax.set_xlabel("Signal Bucket")
    ax.set_ylabel("Mean Return")
    ax.tick_params(axis="x", rotation=45)
    return fig
