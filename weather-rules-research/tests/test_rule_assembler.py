from weather_rules_research.rules.assembler import RuleAssembler
from weather_rules_research.rules.question_parser import QuestionParseResult
from weather_rules_research.rules.rules_text_parser import RulesTextParseResult


def test_rule_assembler_merges_question_and_rules_results() -> None:
    assembler = RuleAssembler()

    q_result = QuestionParseResult(
        market_type="daily_high_temperature",
        location_name="Central Park",
        target_date_raw="Apr 12",
        variable_name="daily_max_temperature",
        parse_confidence=0.92,
        needs_review=False,
    )

    r_result = RulesTextParseResult(
        station_name="New York City Central Park",
        station_id="KNYC",
        source_name="official_source",
        timezone="America/New_York",
        variable_name="daily_max_temperature",
        parse_confidence=0.85,
        needs_review=False,
        extracted_flags=["official_source", "station_central_park"],
    )

    rule = assembler.assemble(
        market_id="m1",
        question="Highest temperature in Central Park on Apr 12?",
        raw_rules_text="Official station source is Central Park.",
        q_result=q_result,
        r_result=r_result,
    )

    assert rule.market_id == "m1"
    assert rule.market_type == "daily_high_temperature"
    assert rule.location_name == "Central Park"
    assert rule.nws_station_id is None
    assert rule.cdo_station_id is None
    assert rule.variable_name == "daily_max_temperature"
    assert rule.timezone == "America/New_York"
    assert rule.parse_confidence == 0.92
    assert rule.needs_review is False


def test_rule_assembler_falls_back_when_rules_parser_missing_values() -> None:
    assembler = RuleAssembler()

    q_result = QuestionParseResult(
        market_type="daily_low_temperature",
        location_name="Singapore",
        target_date_raw="March 15",
        variable_name="daily_min_temperature",
        parse_confidence=0.9,
        needs_review=False,
    )

    r_result = RulesTextParseResult(
        station_name=None,
        station_id=None,
        source_name=None,
        timezone=None,
        variable_name=None,
        parse_confidence=0.2,
        needs_review=True,
        extracted_flags=[],
    )

    rule = assembler.assemble(
        market_id="m2",
        question="Lowest temperature in Singapore on March 15?",
        raw_rules_text="stub text",
        q_result=q_result,
        r_result=r_result,
    )

    assert rule.market_type == "daily_low_temperature"
    assert rule.location_name == "Singapore"
    assert rule.variable_name == "daily_min_temperature"
    assert rule.timezone == "UTC"
    assert rule.source_name == "market_rules"
    assert rule.needs_review is True
