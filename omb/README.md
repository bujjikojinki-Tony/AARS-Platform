# AARS OMB

Current snapshot `omb-003d-b8`. Evidence authorization expiry and result usability audit.

| Version | Scope | Local regression |
|---|---|---:|
| `omb-002-fix` | Frozen for the local single-operator synthetic deployment | 32 |
| `omb-003a` | Detailed design complete with accepted source registration exception | Design only |
| `omb-003b` | Task Manager foundation code review | 159 |
| `omb-003c` | Task events and synthetic Evidence integration code review | 175 |
| `omb-003d-b3` | Local MCP and review request verified; approval platform blocked | 189 |
| `omb-003d-b4` | Local MCP framing hardened; approval platform blocked | 194 |
| `omb-003d-b5` | Context-bound approval receipt validation and native interoperability | 237 |
| `omb-003d-b6` | Transactional result decisions and one-time challenge consumption | 260 |
| `omb-003d-b7` | Same-session output-loss recovery for approval challenges | 278 |
| `omb-003d-b8` | Evidence authorization expiry and result usability audit | 289 |

Run from the `omb/` directory with Python 3.13.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r docs/requirements-development-lock.txt
.venv/bin/python scripts/run_tests.py --scope full
```

The approval gate is `BLOCKED_APPROVAL_PLATFORM`. OMB-003E through OMB-003G remain on hold.
Source provenance and hashes are recorded in `VERSIONS.json`. Published examples use synthetic data.
