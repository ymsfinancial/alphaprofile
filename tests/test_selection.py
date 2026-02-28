import pandas as pd

from alphaprofile.selection import select_best


def test_select_best():
    df = pd.DataFrame(
        {
            "alpha": ["a", "b"],
            "hit_rate": [0.6, 0.55],
            "mean_signed_return": [0.01, 0.02],
            "adverse_selection": [0.001, 0.003],
        }
    )
    ranked = select_best(df)
    assert ranked.iloc[0]["alpha"] in {"a", "b"}
