from uuid import uuid4

from backend.models.weather import EvidenceConflictLevel
from backend.models.weather import EvidenceFreshness
from backend.models.weather import EvidencePack
from backend.models.weather import FreshnessStatus
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherSourceRecord


class EvidencePackBuilder:
    def build(
        self,
        descriptor: WeatherMarketDescriptor,
        sources: list[WeatherSourceRecord],
    ) -> EvidencePack:
        freshness = self._resolve_freshness(sources)
        conflict = self._resolve_conflict(sources)
        return EvidencePack(
            evidence_pack_id=f"evp_{uuid4().hex[:10]}",
            market_id=descriptor.market_id,
            descriptor=descriptor,
            sources=sources,
            evidence_freshness=freshness,
            evidence_conflict_level=conflict,
            raw_refs=[s.source_id for s in sources],
        )

    def _resolve_freshness(self, sources: list[WeatherSourceRecord]) -> EvidenceFreshness:
        if not sources:
            return EvidenceFreshness.MISSING
        statuses = [s.freshness_status for s in sources]
        if all(status == FreshnessStatus.FRESH for status in statuses):
            return EvidenceFreshness.FRESH
        if any(status == FreshnessStatus.FRESH for status in statuses):
            return EvidenceFreshness.PARTIAL
        if any(status == FreshnessStatus.STALE for status in statuses):
            return EvidenceFreshness.STALE
        return EvidenceFreshness.MISSING

    def _resolve_conflict(self, sources: list[WeatherSourceRecord]) -> EvidenceConflictLevel:
        values = [
            source.normalized_value
            for source in sources
            if source.normalized_value is not None
        ]
        if len(values) <= 1:
            return EvidenceConflictLevel.NONE
        spread = max(values) - min(values)
        if spread < 1.5:
            return EvidenceConflictLevel.LOW
        if spread < 3.5:
            return EvidenceConflictLevel.MEDIUM
        return EvidenceConflictLevel.HIGH
