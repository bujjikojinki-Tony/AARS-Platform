# AARS OMB-003E review candidate

328 local tests passed, including 32 historical tests. Approval platform BLOCKED; application integration and UI rendering PENDING; unknown-version explicit-rejection design clause remains unmet. 003F and 003G HOLD. This snapshot is not a frozen release.

Run on macOS with Python 3.13:
```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r docs/requirements-development-lock.txt
.venv/bin/python scripts/run_tests.py --scope full
```

Source includes initialization locking, bounded configuration loading, binding validation and the independent stdio launcher. Public frozen runtime paths are placeholders. The private-host MCP acceptance harness needs the original local frozen binding and registered hashes; it is not a portable standalone acceptance command. No application configuration, live database, credentials or signing identity is included.

See evidence/003e for test evidence, provenance and outstanding gates. Evidence is sanitized; raw local XML and reports remain in the local review package.
