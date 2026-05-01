from backend.models.weather import WeatherMarketDescriptor


class WeatherSourceRegistry:
    def __init__(self, sources: list):
        self.sources = sources

    def select_sources(self, descriptor: WeatherMarketDescriptor) -> list:
        selected = []
        for source in self.sources:
            if source.supports(descriptor):
                selected.append(source)
        return selected
