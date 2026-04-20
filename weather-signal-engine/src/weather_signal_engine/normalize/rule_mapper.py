from weather_signal_engine.models.rule import Rule


class RuleMapper:
    def supports(self, rule: Rule) -> bool:
        return rule.market_type in {
            "daily_high_temperature",
            "daily_low_temperature",
        }
