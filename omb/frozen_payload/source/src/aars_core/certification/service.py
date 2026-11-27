from __future__ import annotations

from typing import Iterable

from aars_core.domain.common import AARSObject
from aars_core.domain.conformance import validate_graph

from .models import CertificationReport, ConformanceReport
from .reporting import certify_report


def certify_graph(objects: Iterable[AARSObject]) -> CertificationReport:
    report = validate_graph(objects, return_report=True)
    assert isinstance(report, ConformanceReport)
    return certify_report(report)
