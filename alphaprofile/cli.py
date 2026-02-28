from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .data import ForwardReturnSpec, compute_forward_returns, get_alpha_columns, load_archives
from .evaluation import ProfileConfig, run_profile
from .selection import select_best


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="alphaprofile")
    sub = parser.add_subparsers(dest="command", required=True)

    profile = sub.add_parser("profile", help="Profile alpha versions")
    profile.add_argument("--data", required=True, help="Path to data directory")
    profile.add_argument("--out", required=True, help="Output directory")
    profile.add_argument("--horizon", default="1s", help="Forward horizon (e.g., 1s, 500ms)")

    select = sub.add_parser("select", help="Select best alpha")
    select.add_argument("--summary", required=True, help="Path to summary CSV")
    select.add_argument("--out", required=True, help="Output path for selection CSV")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "profile":
        data_dir = Path(args.data)
        files = sorted(data_dir.glob("*.bn.ob.archive"))
        df = load_archives(files)
        config = ProfileConfig(horizon=pd.Timedelta(args.horizon))
        run_profile(df, config=config, out_dir=args.out)
        return

    if args.command == "select":
        summary = pd.read_csv(args.summary)
        ranked = select_best(summary)
        ranked.to_csv(args.out, index=False)
        return


if __name__ == "__main__":
    main()
