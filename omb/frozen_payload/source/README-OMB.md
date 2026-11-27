# AARS-OMB-001 — local integration prototype 0.1.0

Source: AARS_EP07_Source_Recovery.tar(1).gz. This package retains the Python source files and original SDK test, excludes AppleDouble metadata and bytecode, and adds src/aars_omb and tests/omb. Not a complete historical AARS release. Original SDK files were not edited.

## macOS
Extract this ZIP into a fresh folder (not the existing AARS-Platform checkout). From that folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pytest
PYTHONPATH="$PWD/src" .venv/bin/python -m pytest -q
PYTHONPATH="$PWD/src" .venv/bin/python -m aars_core.runtime.cli health
```

Python 3.13 was tested. No third-party dependency is needed to launch the adapter. The pytest installation needs network access unless already available.

## OpenMausBot
Register a custom stdio MCP server, if the installed engine supports it. Use the absolute path to the extracted folder in the following example. Do not overwrite any existing configuration. Set command to the venv Python, arguments to `-m aars_omb.server`, and environment PYTHONPATH to the absolute `src` path. Enable only for a separate test Bot.

```json
{"mcpServers":{"aars-omb":{"command":"/ABSOLUTE/PATH/.venv/bin/python","args":["-m","aars_omb.server"],"env":{"PYTHONPATH":"/ABSOLUTE/PATH/src"}}}}
```

Call `aars_health` with `{}`; expect HEALTHY. Call `aars_graph_certify` with `{"scenario":"valid"}`; expect CERTIFIED and 9 objects. Call `{"scenario":"missing_observation"}`; expect invalid. Neither authorizes execution. The graph is a fixed synthetic fixture generated in memory, not real task evidence. Unknown tool names, extra fields and non-allowed scenarios are denied.

## Limitations
Minimal handwritten newline-delimited JSON-RPC stdio subset targeting MCP 2024-11-05; official MCP SDK and real OpenMausBot client interoperability have not been tested. No persistence, actual evidence query, real task ingestion, authentication, production policy authorization, or external writes. The process should remain local and run under restricted OS permissions. No network listener. Do not interpret schema certification as factual validation or operational permission. Full historical regression and GitHub upload remain unverified. No existing local app configuration or remote branch was changed.

## Test evidence
Original SDK: 6 passed. New adapter tests: 9 passed (health, synthetic graph, missing observation, 4 rejected calls, initialization requirement, stdio round trip). Combined: 15 passed. This is not the historical full regression suite.
