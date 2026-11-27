# AARS OMB

Current version `omb-003a`. Detailed design complete with accepted source registration exception.

| Version | Local status | Original local tests |
|---|---|---:|
| `omb-002-fix` | Frozen for the local single-operator synthetic deployment | 32 |
| `omb-003a` | Detailed design complete with accepted source registration exception | Design only |

The source archive hashes and development commit identifiers are recorded in `VERSIONS.json`.
OMB-002-FIX remains scoped to the local, single-operator synthetic deployment. The 003D human approval gate is `BLOCKED_APPROVAL_PLATFORM`.
OMB-003E through 003G remain on hold. The archived fixture is synthetic and carries no production authority.

The frozen Core, SDK, MCP adapter and regression suite are under `frozen_payload/source/`.
To run the suite, use Python 3.13 with `mcp==2.3.0` and `pytest`, then run from `omb/`:

```sh
PYTHONPATH=frozen_payload/source/src python -m pytest -q frozen_payload/source/tests
```
