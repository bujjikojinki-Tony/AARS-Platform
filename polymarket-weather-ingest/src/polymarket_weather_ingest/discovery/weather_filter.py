import re


class WeatherFilter:
    WEATHER_KEYWORDS = [
        "temperature",
        "weather",
        "rain",
        "rainfall",
        "precipitation",
        "snow",
        "snowfall",
        "wind",
        "humidity",
        "hurricane",
        "storm",
        "thunderstorm",
        "heat index",
        "heat advisory",
    ]

    EXCLUDED_KEYWORDS = [
        "ukraine",
        "russia",
        "troops",
        "sovereignty",
        "election",
        "candidate",
        "ceasefire",
        "tariff",
        "recession",
        "president",
        "prime minister",
        "capture",
        "fighting",
        "measles",
        "earthquake",
        "earthquakes",
        "megaquake",
        "volcano",
        "eruption",
        "meteor",
        "natural disaster",
        "banks will fail",
    ]

    EXCLUDED_TAGS = [
        "sports",
        "hockey",
        "soccer",
        "nhl",
        "bundesliga",
    ]

    def is_weather_event(self, event_payload: dict) -> bool:
        text_parts = []
        tags_text = []

        title = event_payload.get("title") or event_payload.get("name")
        if isinstance(title, str):
            text_parts.append(title.lower())

        category = event_payload.get("category")
        if isinstance(category, str):
            text_parts.append(category.lower())

        for market in event_payload.get("markets") or []:
            question = market.get("question") or market.get("title")
            if isinstance(question, str):
                text_parts.append(question.lower())

        tags = event_payload.get("tags") or []
        for tag in tags:
            if isinstance(tag, str):
                text_parts.append(tag.lower())
                tags_text.append(tag.lower())
            elif isinstance(tag, dict):
                label = tag.get("label") or tag.get("name") or tag.get("slug")
                if isinstance(label, str):
                    text_parts.append(label.lower())
                    tags_text.append(label.lower())

        merged = " ".join(text_parts)

        if any(keyword in merged for keyword in self.EXCLUDED_KEYWORDS):
            return False

        if any(tag in tags_text for tag in self.EXCLUDED_TAGS):
            return False

        return any(self._contains_keyword(merged, keyword) for keyword in self.WEATHER_KEYWORDS)

    @staticmethod
    def _contains_keyword(text: str, keyword: str) -> bool:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        return re.search(pattern, text) is not None
