# AARS-OMB-002 / 0.2.0 — synthetic evidence store

Builds on AARS_OMB_001_MCP_MVP.zip. Original core/SDK and SDK tests unchanged. Previous README is retained as historical reference. New store is an adapter-side SQLite repository, not a replacement for Core's runtime storage interface.

## macOS installation
Extract into a new directory, then from that directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pytest
PYTHONPATH="$PWD/src" .venv/bin/python -m pytest -q
mkdir -p "$HOME/.local/share/aars-omb-sim"
chmod 700 "$HOME/.local/share/aars-omb-sim"
```

Use absolute paths in OpenMausBot's custom stdio MCP registration; enable for a single test Bot only. Example (replace all paths):

```json
{"mcpServers":{"aars-omb-002":{"command":"/ABSOLUTE/PROJECT/.venv/bin/python","args":["-m","aars_omb.server"],"env":{"PYTHONPATH":"/ABSOLUTE/PROJECT/src","AARS_OMB_DB":"/ABSOLUTE/HOME/.local/share/aars-omb-sim/evidence.sqlite"}}}}
```

Database path is operator-controlled and must be absolute. Use a dedicated private directory; do not grant other Bots OS access to it. If AARS_OMB_DB is omitted, only the original two ephemeral tools are exposed. No existing application settings are changed by this package.

## Acceptance sequence
1. aars_health {} => isolated runtime HEALTHY (not a database integrity check).
2. aars_fixture_store {"task_id":"OMB-SIM-001"} => created true, nine objects, execution_authorized false.
3. Repeat step 2 => created false, same objects. Task IDs are local synthetic correlation keys, not authenticated identities.
4. aars_evidence_query {"task_id":"OMB-SIM-001"} => one Evidence, observation reference, provenance and SHA-256 of canonical stored record. SDK provenance content_hash may be unavailable; stored record hash does not validate factual source truth.
5. aars_task_objects {"task_id":"OMB-SIM-001"} => nine objects. Restart MCP server and repeat steps 4–5.
6. Query OMB-SIM-002 => found false if not seeded. Send task_id real-task => rejected. Extra payload fields => rejected.

Writes only a fixed SDK-generated synthetic graph. SQLite transaction, foreign keys, primary key, parameterized SQL; duplicate seed is idempotent. Reads reconstruct objects using the existing SDK/Core serialization and check SHA-256 and index identity. Hashes are unkeyed and not a defense against an attacker able to change both records and hashes. Task filtering is logical partitioning, not identity-based access control. No production ingestion, authenticated task delegation, policy enforcement, deletion tool, network listener or production execution. No real OpenMausBot client test; minimal handwritten MCP stdio subset targets 2024-11-05. No remote GitHub update. Full historic AARS regression is not available here.

## Test evidence
26 passed: original SDK 6, existing adapter 9, new storage tests 11. Test runner exercised actual independent stdio processes using the same SQLite database. Original Core/SDK and SDK test files compared byte-for-byte with OMB-001. Linux container tests, not macOS tests.
