"""Verify the Bot-facing stdio boundary on a copy of the hardware enrollment fixture."""

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from aars_task_manager import TaskRuntime
from aars_task_manager.domain import new_id
from aars_task_manager.mcp_server import VERSION
from check_enrollment_restart import ROOT, check, load_session, open_copy, snapshot


OPERATOR_TOOLS = ("approve_result", "prepare_challenge", "submit_receipt")


def launcher_args(path, binding):
    return ["-m", "aars_task_manager.mcp_server", "--data-root", str(path), "--binding-id", binding]


def refused_start(path, binding, expected):
    response = subprocess.run([sys.executable, *launcher_args(path, binding)], env={**os.environ, **child_env()},
                              input=b"", capture_output=True, timeout=10)
    check(response.returncode == 2 and response.stdout == b"" and response.stderr.decode().strip() == expected,
          f"Expected startup refusal {expected}")
    return {"exit_code": response.returncode, "stderr": expected, "stdout_empty": True}


def child_env():
    return {"PYTHONPATH": os.pathsep.join(map(str, (ROOT / "src", ROOT / "frozen_payload/source/src"))),
            "PYTHONDONTWRITEBYTECODE": "1"}


async def sdk_calls(path, binding, task_id):
    settings = StdioServerParameters(command=sys.executable, args=launcher_args(path, binding), env=child_env())
    contract = json.loads((ROOT / "design/omb003a/MCP_TOOLS_CONTRACT.json").read_text())
    expected = {tool["name"] for tool in contract["new_tools_separate_server_only"]}
    trace = []
    with anyio.fail_after(30):
        async with stdio_client(settings) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                initial = await client.initialize()
                check(initial.server_info.name == "aars-task-dev" and initial.server_info.version == VERSION,
                      "Unexpected stdio server")
                tools = [tool.name for tool in (await client.list_tools()).tools]
                check(len(tools) == 9 and set(tools) == expected and set(OPERATOR_TOOLS).isdisjoint(tools),
                      "Unexpected tool discovery surface")

                async def call(tool, arguments, error=None):
                    response = await client.call_tool(tool, arguments)
                    result = json.loads(response.content[0].text)
                    check(bool(response.is_error) == (error is not None) and result["ok"] == (error is None)
                          and result["execution_authorized"] is False, f"Unexpected result for {tool}")
                    if error is not None:
                        check(result["error"]["code"] == error, f"Unexpected error code for {tool}")
                    trace.append({"tool": tool, "arguments": arguments,
                                  "response": response.model_dump(mode="json", by_alias=True)})
                    return result

                listing = await call("aars_task_list_v1", {"limit": 10})
                check(listing["data"] == {"tasks": [], "next_cursor": None}, "Unexpected task records")
                await call("aars_task_get_v1", {"task_id": task_id}, "NOT_FOUND_OR_FORBIDDEN")
                await call("aars_task_list_v1", {"limit": 0}, "INVALID_ARGUMENT")
                draft = {"idempotency_key": str(uuid4()), "title": "Isolated MCP permission check",
                         "description": "", "purpose": "LOCAL_SYNTHETIC_VALIDATION"}
                await call("aars_task_create_v1", draft, "NOT_FOUND_OR_FORBIDDEN")
                for tool in OPERATOR_TOOLS:
                    await call(tool, {}, "INVALID_ARGUMENT")
                return {"initialize": initial.model_dump(mode="json", by_alias=True),
                        "discovered_tools": tools, "calls": trace}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("observed_evidence_archive", type=Path)
    arguments = parser.parse_args()
    session = arguments.session.resolve(strict=True)
    anchor, point, _, _ = load_session(session, arguments.observed_evidence_archive)
    original = session / "database/tasks.sqlite"
    check(original.is_file() and not original.is_symlink(), "Missing isolated diagnostic database")
    check(not any(original.with_name(original.name + suffix).exists() for suffix in ("-wal", "-shm", "-journal")),
          "Source database has a live SQLite sidecar")
    data = original.read_bytes()
    before = sha256(data).hexdigest()
    base = ROOT / ".devdata"
    base.mkdir(mode=0o700, exist_ok=True)
    check(base.resolve() == base, "Development directory symlink is forbidden")
    trace = []
    with TemporaryDirectory(prefix="f02-enrolled-mcp-", dir=base) as folder:
        target = Path(folder) / "tasks.sqlite"
        target.touch(mode=0o600, exist_ok=False)
        target.write_bytes(data)
        repo = open_copy(target)
        binding, = repo.read(lambda db: [row[0] for row in db.execute(
            "SELECT binding_id FROM principals WHERE kind='BOT' AND active=1")])
        task_id = new_id("task")
        initial = snapshot(repo, anchor, point)
        offline = refused_start(target.parent, binding, "RUNTIME_INACTIVE")
        for _ in range(2):
            with TaskRuntime(repo) as runtime:
                invalid_binding = refused_start(target.parent, new_id("binding"), "FORBIDDEN")
                observed = anyio.run(sdk_calls, target.parent, binding, task_id)
                during = snapshot(repo, anchor, point)
                check(during["boot_marker"] == runtime.boot_id, "MCP changed the coordinator")
                trace.append({**observed, "unknown_binding": invalid_binding, "database": during})
            check(snapshot(repo, anchor, point) == initial, "Shutdown changed the baseline database state")
        check(trace[0]["database"]["boot_marker"] != trace[1]["database"]["boot_marker"], "Runtime did not restart")
    after = sha256(original.read_bytes()).hexdigest()
    check(before == after, "Original database changed")
    print(json.dumps({"status": "ISOLATED_MCP_BOUNDARY_PASS", "approval_gate": "BLOCKED_APPROVAL_PLATFORM",
                      "mcp_sdk": version("mcp"), "python": sys.version.split()[0], "offline": offline,
                      "source_db_sha256_before": before, "source_db_sha256_after": after, "runs": trace}, indent=2))


if __name__ == "__main__":
    main()
