from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .models import CertificationReport
from .serialization import load_graph
from .service import certify_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aars", description="AARS specification certification")
    commands = parser.add_subparsers(dest="command", required=True)
    certify = commands.add_parser("certify", help="certify a JSON domain graph")
    certify.add_argument("path", help="input JSON file or directory")
    certify.add_argument("--json", action="store_true", dest="as_json", help="emit a JSON report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = certify_graph(load_graph(args.path))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"aars certify: {exc}", file=sys.stderr)
        return 2
    print(report.to_json() if args.as_json else format_human(report))
    return 0 if report.conformance.valid else 1


def format_human(report: CertificationReport) -> str:
    value = report.conformance
    lines = [
        f"AARS Certification: {report.level.value}",
        f"Spec version: {value.spec_version}",
        f"Valid: {'yes' if value.valid else 'no'}",
        f"Score: {value.score:.1f}/100",
        f"Objects: {value.object_count}  Relationships: {value.relationship_count}",
        ("Violations: " f"{value.summary['error_count']} error, " f"{value.summary['warning_count']} warning, " f"{value.summary['info_count']} info"),
    ]
    for item in value.violations:
        lines.append(f"- [{item.severity.value}] {item.rule_id}/{item.code} {item.object_id}: {item.message}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
