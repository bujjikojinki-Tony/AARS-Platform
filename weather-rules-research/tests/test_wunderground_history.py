from weather_rules_research.models import Station
from weather_rules_research.official_obs import WundergroundHistoryHelper


def test_station_code_from_source() -> None:
    assert WundergroundHistoryHelper.station_code_from_source("wunderground:zspd") == "ZSPD"


def test_build_history_weekly_url() -> None:
    assert (
        WundergroundHistoryHelper.build_history_weekly_url("zspd")
        == "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD"
    )


def test_build_history_url_for_station() -> None:
    station = Station(
        station_name="Shanghai Pudong International Airport",
        nws_station_id=None,
        cdo_station_id=None,
        latitude=31.1434,
        longitude=121.8052,
        timezone="Asia/Shanghai",
        source="wunderground:zspd",
    )

    assert (
        WundergroundHistoryHelper.build_history_url_for_station(station)
        == "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD"
    )
