from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherUnit


CITY_COUNTRY = {
    "Tokyo": "JP",
    "Osaka": "JP",
    "Kyoto": "JP",
    "New York": "US",
    "Los Angeles": "US",
    "Chicago": "US",
    "London": "UK",
    "Paris": "FR",
    "Seoul": "KR",
    "Hong Kong": "HK",
    "Taipei": "TW",
    "Singapore": "SG",
}


class WeatherMarketResolver:
    def resolve(self, descriptor: WeatherMarketDescriptor) -> WeatherMarketDescriptor:
        if not descriptor.country:
            descriptor.country = CITY_COUNTRY.get(descriptor.city)
        if descriptor.unit == WeatherUnit.UNKNOWN:
            if descriptor.metric in {WeatherMetric.DAILY_HIGH, WeatherMetric.DAILY_LOW}:
                descriptor.unit = WeatherUnit.C
                descriptor.parse_warnings.append("unit defaulted to C for temperature metric")
            elif descriptor.metric == WeatherMetric.PRECIPITATION:
                descriptor.unit = WeatherUnit.MM
                descriptor.parse_warnings.append("unit defaulted to MM for precipitation metric")
        return descriptor
