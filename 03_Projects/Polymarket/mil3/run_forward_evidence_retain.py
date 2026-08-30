from __future__ import annotations

import argparse
import json

from aars_market.evidence_offline import retain_verified_evidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retain a verified MIL-3.20 evidence bundle in a scoped archive"
    )
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--retention-days", type=int, default=365)
    parser.add_argument("--minimum-copies", type=int, default=2)
    args = parser.parse_args()
    receipt = retain_verified_evidence(
        args.bundle,
        args.archive_dir,
        retention_days=args.retention_days,
        minimum_copies=args.minimum_copies,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
