from __future__ import annotations

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.rules.question_parser import QuestionParseResult
from weather_rules_research.rules.rules_text_parser import RulesTextParseResult


class RuleAssembler:
    """
    Merge question-level parsing and rules-text parsing
    into one normalized MarketRule.

    Note:
    - station IDs are left empty at this stage unless directly
      available from parsed rules text.
    - station mapping may fill them later.
    """

    def assemble(
        self,
        market_id: str,
        question: str,
        raw_rules_text: str,
        q_result: QuestionParseResult,
        r_result: RulesTextParseResult,
    ) -> MarketRule:
        market_type = q_result.market_type or "unknown"
        location_name = q_result.location_name or "UNKNOWN"
        target_date = q_result.target_date_raw

        variable_name = r_result.variable_name or q_result.variable_name or "unknown"
        timezone = r_result.timezone or "UTC"
        source_name = r_result.source_name or "market_rules"

        station_name = r_result.station_name

        parse_confidence = max(
            q_result.parse_confidence,
            r_result.parse_confidence,
        )

        needs_review = q_result.needs_review or r_result.needs_review

        return MarketRule(
            market_id=market_id,
            market_question=question,
            market_type=market_type,
            location_name=location_name,
            target_date=target_date,
            station_name=station_name,
            nws_station_id=None,
            cdo_station_id=None,
            variable_name=variable_name,
            timezone=timezone,
            source_name=source_name,
            raw_rules_text=raw_rules_text,
            parse_confidence=parse_confidence,
            needs_review=needs_review,
        )
