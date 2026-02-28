from __future__ import annotations

from pathlib import Path

import pandas as pd

from alphaprofile.data import load_archives
from alphaprofile.evaluation import ProfileConfig, run_profile
from alphaprofile.selection import select_best


data_dir = Path("../data")
files = sorted(data_dir.glob("*.bn.ob.archive"))

df = load_archives(files)
config = ProfileConfig(horizon=pd.Timedelta("1s"))
summary = run_profile(df, config=config, out_dir="../reports")

ranked = select_best(summary)
print(ranked.head())
