import pandas as pd


def safe_sort_dashboard_rows(
    df: pd.DataFrame,
    sort_by: str = "confidence_adjusted_gap",
    ascending: bool = False,
) -> pd.DataFrame:
    if sort_by not in df.columns:
        return df
    return df.sort_values(by=sort_by, ascending=ascending)


def available_sort_columns(df: pd.DataFrame) -> list[str]:
    preferred = [
        "confidence_adjusted_gap",
        "confidence_score",
        "band_distance",
        "location_name",
        "target_date",
    ]
    return [c for c in preferred if c in df.columns]
