import pandas as pd

def compute_sector_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame of a sector's prices sorted by date with columns ['date', 'close', 'adjusted_close']:
    Computes 1D, 5D, 1M (21d), 3M (63d), 6M (126d), 12M (252d) returns based on adjusted_close.
    """
    df = prices_df.copy().sort_values("date").reset_index(drop=True)
    price_col = "adjusted_close" if "adjusted_close" in df.columns else "close"

    df["return_1d"] = df[price_col].pct_change(1)
    df["return_5d"] = df[price_col].pct_change(5)
    df["return_1m"] = df[price_col].pct_change(21)
    df["return_3m"] = df[price_col].pct_change(63)
    df["return_6m"] = df[price_col].pct_change(126)
    df["return_12m"] = df[price_col].pct_change(252)

    return df
