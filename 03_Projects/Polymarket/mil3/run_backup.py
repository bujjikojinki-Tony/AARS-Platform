from __future__ import annotations

import argparse

from aars_market.operations import backup_sqlite, dumps, rotate_logs


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.10 verified SQLite backup")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--backup-dir", required=True)
    parser.add_argument("--retention-days", type=int, default=30)
    parser.add_argument("--log-dir")
    parser.add_argument("--max-log-bytes", type=int, default=10 * 1024 * 1024)
    parser.add_argument("--log-backups", type=int, default=7)
    args = parser.parse_args()
    payload = backup_sqlite(args.db, args.backup_dir, retention_days=args.retention_days)
    if args.log_dir:
        payload["log_rotation"] = rotate_logs(
            args.log_dir, max_bytes=args.max_log_bytes, keep=args.log_backups
        )
    print(dumps(payload))


if __name__ == "__main__":
    main()
