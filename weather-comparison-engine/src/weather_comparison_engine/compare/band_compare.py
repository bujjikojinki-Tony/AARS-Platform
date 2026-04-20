from __future__ import annotations


class BandCompare:
    SCHEME_ORDERS = {
        "temperature_4_bucket": [
            "26_or_below",
            "27",
            "28",
            "29_plus",
        ],
        "sea_ice_range_3way": [
            "below_range",
            "in_range",
            "above_range",
        ],
        "precipitation_range_3way": [
            "below_range",
            "in_range",
            "above_range",
        ],
        "snowfall_range_3way": [
            "below_range",
            "in_range",
            "above_range",
        ],
        "wind_speed_range_3way": [
            "below_range",
            "in_range",
            "above_range",
        ],
        "probability_quartile_4": [
            "26_or_below",
            "27",
            "28",
            "29_plus",
        ],
        "global_temperature_index_ordinal": [
            "top_1",
            "top_2",
            "top_3",
            "top_4",
            "top_5",
            "top_6",
            "top_7",
            "top_8",
            "top_9",
            "top_10",
        ],
    }

    def distance(
        self,
        model_band: str | None,
        market_band: str | None,
        band_scheme: str | None = None,
    ) -> int:
        if model_band is None or market_band is None:
            return 999

        try:
            order = self.SCHEME_ORDERS.get(band_scheme or "temperature_4_bucket")
            if order is None:
                return 999
            i = order.index(model_band)
            j = order.index(market_band)
            return abs(i - j)
        except ValueError:
            return 999


def compare_bands(
    model_band: str | None,
    market_band: str | None,
    band_scheme: str | None = None,
) -> str:
    distance = BandCompare().distance(model_band, market_band, band_scheme=band_scheme)
    if distance >= 999:
        return "unknown"
    if distance == 0:
        return "aligned"
    return "divergent"
