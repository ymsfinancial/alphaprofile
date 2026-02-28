import pandas as pd

from alphaprofile.data import ForwardReturnSpec, compute_forward_returns
from alphaprofile.metrics import hit_rate


def test_compute_forward_returns():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=5, freq="1s"),
            "name": ["A"] * 5,
            "touch_bid": [100, 101, 102, 103, 104],
            "touch_ask": [100.5, 101.5, 102.5, 103.5, 104.5],
        }
    )
    df["mid"] = (df["touch_bid"] + df["touch_ask"]) / 2.0
    spec = ForwardReturnSpec(horizon=pd.Timedelta("1s"))
    out = compute_forward_returns(df, spec)
    assert "ret_forward" in out.columns


def test_hit_rate():
    signal = pd.Series([1, -1, 1, -1])
    ret = pd.Series([0.1, -0.2, -0.1, -0.4])
    result = hit_rate(signal, ret)
    assert 0.0 <= result["hit_rate"] <= 1.0
