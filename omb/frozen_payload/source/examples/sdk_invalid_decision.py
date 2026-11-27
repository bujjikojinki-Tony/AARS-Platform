from __future__ import annotations

from aars_sdk import AARSClient, SDKRelationshipError


client = AARSClient(source_id="sdk-invalid-decision", source_type="example")
observation = client.create_observation(subject="subject.reference", payload={"value": 10})
evidence = client.create_evidence(
    observations=[observation],
    code="aars.reference.VALUE_HIGH",
    category="measurement",
    direction="positive",
    weight=0.8,
    confidence=0.9,
)

try:
    client.create_decision(
        claims=[evidence],  # type: ignore[list-item]
        level="spot",
        posture="wait",
        confidence=0.5,
        rationale="This intentionally passes Evidence where Claim is required.",
    )
except SDKRelationshipError as exc:
    print(f"SDK rejected invalid relationship: {exc}")
