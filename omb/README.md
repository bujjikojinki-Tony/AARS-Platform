# AARS OMB

Current version `omb-003d-b4`. Local MCP framing hardened; approval platform blocked.

| Version | Local status | Original local tests |
|---|---|---:|
| `omb-002-fix` | Frozen for the local single-operator synthetic deployment | 32 |
| `omb-003a` | Detailed design complete with accepted source registration exception | Design only |
| `omb-003b` | Task Manager foundation code review | 159 |
| `omb-003c` | Task events and synthetic Evidence integration code review | 175 |
| `omb-003d-b3` | Local MCP and review request verified; approval platform blocked | 189 |
| `omb-003d-b4` | Local MCP framing hardened; approval platform blocked | 194 |

The source archive hashes and development commit identifiers are recorded in `VERSIONS.json`.
OMB-002-FIX remains scoped to the local, single-operator synthetic deployment. The 003D human approval gate is `BLOCKED_APPROVAL_PLATFORM`.
OMB-003E through 003G remain on hold. The archived fixture is synthetic and carries no production authority.

Use Python 3.13 and run from the `omb/` directory.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r docs/requirements-development-lock.txt
.venv/bin/python scripts/run_tests.py --scope full
```

The development binding file uses repository-relative placeholders. The 003D stdio service attaches to an existing private TaskRuntime coordinator. The public fixture has no Bot ID, user account or live data.
