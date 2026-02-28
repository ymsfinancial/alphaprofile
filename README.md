
# AlphaProfile — Alpha Analysis & Selection

Overview
--------

`AlphaProfile` is a project to systematically analyse, profile and select the best version of a trading alpha to deploy for execution or backtesting. Given multiple candidate alphas (different parameterizations, signals, or feature variants), the toolkit computes a standard set of profiling metrics, runs statistical evaluations and ranks/selects the alpha(s) best suited to trade under user constraints.

Handover note (QR intern)
-------------------------

This repository is being handed over as a **starter kit** for a QR intern. The existing code is intentionally minimal and **not** a finished solution. The intern is expected to use whatever is helpful, modify freely, and extend or replace components as needed to achieve the objective. Do not feel constrained by the current structure or implementation—treat it as a jump-start only.

Goals
-----

- Provide a reproducible, auditable evaluation suite for any alpha time series.
- Characterize alphas along a defined set of dimensions relevant to execution and portfolio construction.
- Automate selection of the best alpha version using configurable scoring and constraints.
- Produce visual and numeric outputs for monitoring, comparison and risk review.

Characterization dimensions
---------------------------

For every alpha (time series of predicted returns/signals and matched executions or fills), compute the following dimensions:

- **Horizon (ms / seconds / minutes / days):** the timescale over which the alpha has predictive power. Compute predictive information at multiple aggregation horizons (e.g., 10ms, 100ms, 1s, 10s, 1m) by aggregating signals and forward returns to estimate information decay and identify an effective horizon.

- **Hit Rate:** fraction of times the sign of the alpha predicts the sign of the forward return over the target horizon. Compute and report both raw hit rate and hit rate conditioning on signal magnitude (e.g., deciles).

- **Conditional Return Distribution:** the distribution of forward returns conditional on signal buckets. Report mean, median, std, skew, kurtosis, and tail quantiles (1%, 5%, 95%, 99%). Provide separate stats for long/short sides.

- **Decay Curve (Information Decay):** how the alpha's predictive power falls off with increasing forward horizon. Typically estimated via correlation of signal with forward returns at various horizons or via half-life of predictivity.

- **Regime Dependence (optional):** measure how the alpha performs across market regimes (e.g., high/low volatility, trending vs mean-reverting, liquidity regimes). Implement regime labeling (volatility quantiles, roll-ups) then compute per-regime metrics and a divergence score that captures sensitivity to regime.

- **Adverse Selection Profile (optional):** measure the alpha's exposure to adverse selection at execution. Use fills/trade-level data to compute conditional slippage: expected signed slippage when alpha indicates direction, slippage distribution versus passive fills, and short-term return reversal after fills.


Evaluation suite
----------------

Inputs
- Time series of alpha signals: timestamps, instrument, signal value (signed), optionally signal id/version.
- Market data: trade prints / mid-prices / best bid/ask timestamps required to compute forward returns and slippage.
- (Optional) Execution/fill records: used to compute adverse selection and realized P&L.

Outputs
- Per-alpha metrics for all characterization dimensions.
- Visual reports: hit-rate vs magnitude, conditional return violin/box plots, decay curve plots, regime heatmaps, slippage histograms.
- Selection report: ranked list of alpha versions with scoring breakdown and recommended candidate(s).

Core components
- `data` — loaders and normalizers for alpha series, market ticks and fills; handles timezone, event-aligned resampling and aggregation.
- `metrics` — implementations for each characterization dimension: horizon analysis, hit rate, conditional distribution, decay, regime dependence, adverse selection.
- `evaluation` — orchestrates metric computation across versions, produces CSV/JSON reports and plots.
- `selection` — implements scoring, constraint filtering, and selection strategies (single-score, multi-objective, pareto-front, threshold filters).
- `visuals` — plotting utilities for common diagnostics.

Selection algorithm (example)
-----------------------------

1. Compute standardized metrics per alpha version (normalize by interquartile or z-score).
2. Apply constraints: minimum hit-rate, minimum expected return, maximum adverse selection, minimum information horizon.
3. Compute a composite score: example weighted sum of normalized metrics (weights configurable):

	 score = w1 * (normed_conditional_mean) + w2 * (normed_hit_rate) - w3 * (normed_adverse_selection) - w4 * (volatility_penalty)

4. Optionally run bootstrap stability checks: resample periods or instruments and recompute scores to ensure the ranking is robust.
5. Output top-K candidates and a recommended production candidate with confidence measures (e.g., fraction of bootstrap samples where it ranks top).

Best-practice checks
- Look for concentration of performance in a small number of events (overfit risk).
- Verify performance across regimes; prefer alphas with stable performance and low regime-sensitivity unless you have regime switch handlers.
- Prefer alphas with non-trivial horizon (not pure microstructure noise) after considering execution latencies and routing.

Statistical considerations
- Use block bootstrap or time-series aware resampling to preserve temporal dependence when estimating confidence intervals.
- Report both point estimates and uncertainty intervals for all summary metrics.
- When comparing versions, test whether observed differences are statistically significant given the autocorrelation structure of returns.

Architecture & suggested files
-----------------------------

- `alphaprofile/` (python package)
	- `__init__.py`
	- `data.py` — loaders, resampling utilities
	- `metrics.py` — metric computations
	- `evaluation.py` — driver to run profiling for many versions
	- `selection.py` — selection logic and scoring
	- `visuals.py` — plotting helpers
	- `cli.py` — command-line entry for batch runs
- `notebooks/` — examples and exploratory notebooks
- `tests/` — unit + integration tests
- `examples/` — sample CSV inputs and minimal run scripts

Data folder structure
---------------------

The `data/` directory contains daily order book archive files with the naming pattern:

- `YYYYMMDD.bn.ob.archive`

Each file is a CSV-like archive with a single header row and then data rows. The header includes:

- **Market and Greeks**: `g1_*` fields (e.g., `g1_delta`, `g1_iv`, `g1_days_to_expiry_1`).
- **Order book alpha variants**: `ob1_*` ... `ob5_*` fields, where each `obX` corresponds to a different parameter set.
- **Touch book for forward returns**: `touch_bid`, `touch_ask`, plus depth snapshots at multiple horizons (e.g., `touch_bid@1.0`, `touch_ask@60.0`).

Alpha configuration (source of ob1–ob5)
--------------------------------------

The configuration file `alpha.bn.ini` defines the alpha variants under the `[indicators]` section:

- `ob1` … `ob5` are five order-book alphas (obnse), each with different half-life parameters.
- `ob_level_half_life2` and `ob_vol_half_life` drive **ret1/ret2**.
- `ob_level_half_life` drives **ret3/ret4**.

Objective: compare the quality of `ret1`, `ret2`, `ret3`, `ret4` across `ob1`–`ob5` using the characterization dimensions described above, and select the best-performing alpha version for deployment.

Forward return computation (required for all profiling)
------------------------------------------------------

Use `touch_bid` and `touch_ask` to compute mid prices and forward returns.

- `mid = (touch_bid + touch_ask) / 2`
- For a chosen forward horizon $h$ (seconds), compute `mid{h}` from `touch_bid@{h}` and `touch_ask@{h}`.
- `ret{h} = (mid{h} - mid) / mid`

The profiling suite should compute forward returns consistently across all alpha variants, and re-use the same `ret_forward` series for fair comparison.

Post-selection diagnostics (g1 dimensions)
-----------------------------------------

After selecting the best alpha version, analyze and report its behavior conditioned on:

- `g1_delta`
- `g1_iv`
- `g1_days_to_expiry_1`

This should include conditional performance summaries (hit rate and mean return) across bins (e.g., delta buckets, IV quantiles, DTE buckets) to reveal where the alpha is strongest or weak.

Basic usage guide (current code)
-------------------------------

Install locally (editable)

```bash
cd /home/mayank.kumar/projects/alphaprofile
python -m pip install -e .
```

Profile all `ob*` alphas in `data/` using the 1s forward return

```bash
alphaprofile profile --data data --out reports --horizon 1s
```

Select the best alpha from the summary

```bash
alphaprofile select --summary reports/summary.csv --out reports/selection.csv
```

Python API example
------------------

1. Load data and alpha versions

```python
from pathlib import Path

import pandas as pd

from alphaprofile.data import load_archives
from alphaprofile.evaluation import run_profile

files = sorted(Path("data").glob("*.bn.ob.archive"))
alpha_versions = load_archives(files)

report = run_profile(alpha_versions, market, out_dir='reports/')
```

2. Select a top alpha

```python
from alphaprofile.selection import select_best

best = select_best(report, constraints={"min_hit_rate":0.55, "max_adverse_selection":0.001}, weights={"mean":0.5, "hit_rate":0.3, "adverse":0.2})
print(best)
```

Next steps for implementation
-----------------------------

- Implement the Python package skeleton described above.
- Add metric implementations with unit tests using synthetic data.
- Create a sample dataset (sanitized) and an example notebook demonstrating the workflow.
- Add documentation pages for each metric describing formulas and interpretation.

Notes & caveats
----------------

- The toolkit focuses on alpha evaluation, not execution. Integration with execution systems requires additional consideration for latency, order routing, and market microstructure.
- Adverse selection requires fill-level data — if not available, proxy slippage measures can be used but will be weaker.

Contact
-------
Email: mayank.kumar@ymsfinancial.com

