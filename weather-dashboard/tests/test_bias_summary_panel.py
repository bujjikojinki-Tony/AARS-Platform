import pandas as pd

from weather_dashboard.ui.bias_summary_panel import render_bias_summary_panel


def test_bias_summary_panel_smoke():
    df = pd.DataFrame(
        [
            {"metric": "mae", "value": 1.2},
            {"metric": "rmse", "value": 1.8},
            {"metric": "band_hit_rate", "value": 0.67},
        ]
    )

    render_bias_summary_panel(df)

