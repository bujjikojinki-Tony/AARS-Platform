from __future__ import annotations

import argparse

from aars_market.evidence_offline import (
    build_offline_verification_report,
    write_verification_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a MIL-3.20 evidence bundle offline without SQLite"
    )
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    report = build_offline_verification_report(args.bundle)
    if args.report:
        write_verification_report(report, args.report)
    print("execution_mode=PAPER_ONLY")
    print("database_accessed=false")
    print(f"status={report['status']}")
    print(f"file_sha256={report['source']['file_sha256']}")
    print(f"combined_sha256={report['bundle_identity']['combined_sha256'] or 'UNAVAILABLE'}")
    print("configuration_applied=false")
    print("live_execution_allowed=false")
    if report["status"] != "VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
