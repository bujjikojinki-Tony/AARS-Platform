from dataclasses import FrozenInstanceError

import pytest

import aars_sdk
from aars_core.certification import CertificationLevel
from aars_core.domain import Decision, ObjectType, validate_graph
from aars_sdk import AARSClient, SDKRelationshipError


def build_sdk_graph():
    client = AARSClient(source_id="sdk-test", source_type="test_fixture")
    observation = client.create_observation(
        subject="subject.reference",
        payload={"value": 10, "nested": {"unit": "points"}},
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
        scope={"domain": "reference", "subject": observation.subject},
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
    return client, (observation, evidence, claim, decision, outcome, lesson, memory, knowledge, policy)


def test_sdk_creates_valid_full_reference_graph():
    _, graph = build_sdk_graph()
    assert validate_graph(graph) == ()
    assert [item.type for item in graph] == [
        ObjectType.OBSERVATION,
        ObjectType.EVIDENCE,
        ObjectType.CLAIM,
        ObjectType.DECISION,
        ObjectType.OUTCOME,
        ObjectType.LESSON,
        ObjectType.MEMORY,
        ObjectType.KNOWLEDGE,
        ObjectType.POLICY,
    ]
    assert all(item.id.startswith(f"{item.type.value}.") for item in graph)
    assert all(item.spec_version == "1.0.0" for item in graph)


def test_sdk_output_passes_certification():
    client, graph = build_sdk_graph()
    report = client.certify(graph)
    assert report.certification_level is CertificationLevel.CERTIFIED
    assert report.valid is True
    assert report.score == 100


def test_sdk_prevents_decision_from_raw_evidence():
    client, graph = build_sdk_graph()
    evidence = graph[1]
    with pytest.raises(SDKRelationshipError, match="Claim objects"):
        client.create_decision(
            claims=[evidence],  # type: ignore[list-item]
            level="spot",
            posture="wait",
            confidence=0.5,
            rationale="Invalid relationship fixture.",
        )


def test_sdk_generated_objects_preserve_traceability():
    _, graph = build_sdk_graph()
    observation, evidence, claim, decision, outcome, lesson, memory, knowledge, policy = graph
    assert evidence.observation_ids == (observation.id,)
    assert claim.evidence_ids == (evidence.id,)
    assert decision.claim_ids == (claim.id,)
    assert outcome.decision_ids == (decision.id,)
    assert outcome.claim_ids == (claim.id,)
    assert lesson.outcome_ids == (outcome.id,)
    assert memory.decision_ids == (decision.id,)
    assert knowledge.lesson_ids == (lesson.id,)
    assert policy.knowledge_ids == (knowledge.id,)
    assert decision.provenance.parent_ids == (claim.id,)


def test_sdk_does_not_expose_unsafe_constructors_for_plugin_use():
    assert "Observation" not in aars_sdk.__all__
    assert "Decision" not in aars_sdk.__all__
    assert not hasattr(aars_sdk, "Observation")
    assert not hasattr(aars_sdk, "Decision")
    assert aars_sdk.__all__ == [
        "AARSClient",
        "SDK_API_VERSION",
        "SDKConformanceError",
        "SDKRelationshipError",
        "SDKValidationError",
    ]


def test_sdk_returns_immutable_core_objects():
    _, graph = build_sdk_graph()
    decision = graph[3]
    assert isinstance(decision, Decision)
    with pytest.raises(FrozenInstanceError):
        decision.posture = "changed"
