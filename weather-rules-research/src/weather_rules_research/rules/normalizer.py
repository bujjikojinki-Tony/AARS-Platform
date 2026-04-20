from __future__ import annotations

from weather_rules_research.models import MarketRule
from weather_rules_research.rules.assembler import RuleAssembler
from weather_rules_research.rules.question_parser import parse_market_question
from weather_rules_research.rules.rules_text_parser import parse_rules_text


def normalize_market_rule(
    market_id: str,
    question: str,
    rules_text: str | None = None,
    timezone: str = "UTC",
) -> MarketRule:
    question_result = parse_market_question(question=question)
    rules_text_result = parse_rules_text(rules_text)
    assembled = RuleAssembler().assemble(
        market_id=market_id,
        question=question.strip(),
        raw_rules_text=(rules_text or "").strip(),
        q_result=question_result,
        r_result=rules_text_result,
    )
    if assembled.timezone == "UTC" and timezone != "UTC":
        assembled.timezone = timezone
    return assembled
