from __future__ import annotations

from aars_sdk import AARSClient


def build_reference_graph():
    client = AARSClient(source_id="sdk-quickstart", source_type="example")
    observation = client.create_observation(
        subject="subject.reference",
        payload={"value": 10, "unit": "points"},
    )
    evidence = client.create_evidence(
        observations=[observation],
        code="aars.reference.VALUE_HIGH",
        category="measurement",
        direction="positive",
        weight=0.8,
        confidence=0.9,
        value={"value": 10},
        explanation="The observed value exceeds the declared threshold.",
    )
    claim = client.create_claim(
        evidence=[evidence],
        statement="The reference condition is elevated.",
        scope={"domain": "reference"},
    )
    decision = client.create_decision(
        claims=[claim],
        level="spot",
        posture="wait",
        confidence=0.72,
        rationale="The Claim supports a conservative research posture.",
    )
    outcome = client.create_outcome(
        decisions=[decision],
        claims=[claim],
        measurements={"value": 12},
        classification="supported",
    )
    lesson = client.create_lesson(
        outcomes=[outcome],
        alignment="supported",
        codes=["DECISION_SUPPORTED"],
        narrative="The later Outcome supported the recorded decision context.",
    )
    memory = client.create_memory(
        observations=[observation],
        evidence=[evidence],
        claims=[claim],
        decisions=[decision],
        outcomes=[outcome],
        lessons=[lesson],
    )
    knowledge = client.create_knowledge(
        lessons=[lesson],
        claim="Elevated conditions require conservative review.",
        scope={"domain": "reference"},
    )
    policy = client.create_policy(
        knowledge=[knowledge],
        rule="Require review when the elevated condition is present.",
        authority="reference.governance",
        scope={"domain": "reference"},
    )
    return (observation, evidence, claim, decision, outcome, lesson, memory, knowledge, policy)


if __name__ == "__main__":
    graph = build_reference_graph()
    report = AARSClient().certify(graph)
    print(report.to_json())
