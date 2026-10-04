from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from math import floor
from typing import Sequence

from .models import FundingCadenceObservation, FundingRate


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class FundingGap:
    start: str
    end: str
    hours: float
    estimated_missing_events: int
    location: str
    cadence_units: float
    effective_cadence_hours: float


@dataclass(frozen=True)
class FundingCadencePeriod:
    effective_from: str
    interval_hours: float
    source_status: str
    observed_at: str | None


@dataclass(frozen=True)
class FundingCoverage:
    status: str
    required: bool
    cadence_hours: float
    observed_events: int
    estimated_missing_events: int
    coverage_ratio: float
    largest_gap_hours: float
    largest_gap_cadence_units: float
    cadence_source: str
    cadence_observed_at: str | None
    cadence_schedule: tuple[FundingCadencePeriod, ...]
    gaps: tuple[FundingGap, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["cadence_schedule"] = [asdict(period) for period in self.cadence_schedule]
        payload["gaps"] = [asdict(gap) for gap in self.gaps]
        return payload


def _build_schedule(
    observations: Sequence[FundingCadenceObservation],
    start: datetime,
    end: datetime,
    fallback: timedelta,
) -> list[tuple[datetime, timedelta, str, datetime | None]]:
    relevant = sorted(
        (item for item in observations if _utc(item.observed_at) <= end),
        key=lambda item: _utc(item.observed_at),
    )
    prior = [item for item in relevant if _utc(item.observed_at) <= start]
    if prior:
        initial = prior[-1]
        schedule = [
            (
                start,
                timedelta(hours=initial.interval_hours),
                initial.source_status,
                _utc(initial.observed_at),
            )
        ]
    else:
        schedule = [(start, fallback, "DEFAULT_8H_FALLBACK", None)]
    schedule.extend(
        (
            _utc(item.observed_at),
            timedelta(hours=item.interval_hours),
            item.source_status,
            _utc(item.observed_at),
        )
        for item in relevant
        if start < _utc(item.observed_at) <= end
    )
    return schedule


def _cadence_at(
    schedule: Sequence[tuple[datetime, timedelta, str, datetime | None]],
    at: datetime,
) -> tuple[timedelta, str, datetime | None]:
    active = schedule[0]
    for item in schedule[1:]:
        if item[0] > at:
            break
        active = item
    return active[1], active[2], active[3]


def _cadence_units(
    schedule: Sequence[tuple[datetime, timedelta, str, datetime | None]],
    start: datetime,
    end: datetime,
) -> float:
    cursor = start
    units = 0.0
    changes = [item[0] for item in schedule[1:] if start < item[0] < end]
    for boundary in [*changes, end]:
        cadence, _, _ = _cadence_at(schedule, cursor)
        units += (boundary - cursor) / cadence
        cursor = boundary
    return units


def analyze_funding_coverage(
    rates: Sequence[FundingRate],
    start: datetime,
    end: datetime,
    *,
    cadence: timedelta = timedelta(hours=8),
    cadence_observations: Sequence[FundingCadenceObservation] = (),
    required: bool = True,
    tolerance: float = 1.5,
) -> FundingCoverage:
    start_utc = _utc(start)
    end_utc = _utc(end)
    if end_utc < start_utc:
        raise ValueError("end must be at or after start")
    if cadence <= timedelta(0):
        raise ValueError("cadence must be positive")
    if tolerance < 1:
        raise ValueError("tolerance must be at least 1")

    events = sorted(
        {
            _utc(item.funding_time)
            for item in rates
            if start_utc <= _utc(item.funding_time) <= end_utc
        }
    )
    schedule = _build_schedule(cadence_observations, start_utc, end_utc, cadence)
    boundaries = [start_utc, *events, end_utc]
    gaps: list[FundingGap] = []
    for index in range(len(boundaries) - 1):
        left = boundaries[index]
        right = boundaries[index + 1]
        duration = right - left
        cadence_units = _cadence_units(schedule, left, right)
        if cadence_units <= tolerance:
            continue
        location = "internal"
        if index == 0:
            location = "leading"
        elif index == len(boundaries) - 2:
            location = "trailing"
        missing = max(1, floor(cadence_units) - (0 if location != "internal" else 1))
        active_cadence, _, _ = _cadence_at(schedule, left)
        gaps.append(
            FundingGap(
                start=left.isoformat(),
                end=right.isoformat(),
                hours=duration.total_seconds() / 3600.0,
                estimated_missing_events=missing,
                location=location,
                cadence_units=cadence_units,
                effective_cadence_hours=active_cadence.total_seconds() / 3600.0,
            )
        )

    estimated_missing = sum(gap.estimated_missing_events for gap in gaps)
    denominator = len(events) + estimated_missing
    ratio = 1.0 if not required else len(events) / denominator if denominator else 0.0
    if not required:
        status = "NOT_REQUIRED"
    elif not events:
        status = "MISSING"
    elif gaps:
        status = "GAPPED"
    else:
        status = "COMPLETE"
    active_cadence, active_source, active_observed_at = _cadence_at(schedule, end_utc)
    periods = tuple(
        FundingCadencePeriod(
            effective_from=item[0].isoformat(),
            interval_hours=item[1].total_seconds() / 3600.0,
            source_status=item[2],
            observed_at=item[3].isoformat() if item[3] is not None else None,
        )
        for item in schedule
    )
    return FundingCoverage(
        status=status,
        required=required,
        cadence_hours=active_cadence.total_seconds() / 3600.0,
        observed_events=len(events),
        estimated_missing_events=estimated_missing,
        coverage_ratio=ratio,
        largest_gap_hours=max((gap.hours for gap in gaps), default=0.0),
        largest_gap_cadence_units=max((gap.cadence_units for gap in gaps), default=0.0),
        cadence_source=active_source,
        cadence_observed_at=(
            active_observed_at.isoformat() if active_observed_at is not None else None
        ),
        cadence_schedule=periods,
        gaps=tuple(gaps),
    )
