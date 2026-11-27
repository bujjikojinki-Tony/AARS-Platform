"""OMB-003D Bot-facing stdio transport. The operator control plane is separate."""
from __future__ import annotations

from contextlib import contextmanager

import argparse
import json
import logging
import os
from pathlib import Path
import sys

import anyio
from jsonschema import Draft202012Validator
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .domain import canonical, new_id
from .errors import TaskError
from .service import TaskManager
from .storage import Repository

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.3.0b7'
MAX_WIRE_BYTES = 64 * 1024
OPERATIONS = {
    'aars_task_create_v1': ('create', 'Create a task draft within the assigned workspace.'),
    'aars_task_get_v1': ('get', 'Read a task and its pending review summary.'),
    'aars_task_list_v1': ('list', 'List visible tasks, using continuation cursors.'),
    'aars_task_update_v1': ('update', 'Edit a draft using its expected version.'),
    'aars_task_transition_v1': ('transition', 'Request an allowed task transition. Starts require operator approval.'),
    'aars_task_lease_renew_v1': ('renew', 'Request lease renewal. This operation requires operator approval.'),
    'aars_task_evidence_link_v1': ('evidence_link', 'Link a registered synthetic Evidence snapshot to an active task.'),
    'aars_task_review_request_v1': ('review_request', 'Submit a result for human review using the current task and lease.'),
    'aars_task_events_v1': ('events', 'Read verified, paginated task event summaries.'),
}


def _error(code, message, retryable=False):
    return {'schema_version': 'omb-task/1.0', 'request_id': new_id('request'),
            'execution_authorized': False, 'ok': False,
            'error': {'code': code, 'message': message, 'retryable': retryable}}


class ToolAdapter:
    def __init__(self, manager):
        self.manager = manager
        design = ROOT / 'design' / 'omb003a'
        contract = json.loads((design / 'MCP_TOOLS_CONTRACT.json').read_text())
        tools = contract['new_tools_separate_server_only']
        if {tool['name'] for tool in tools} != set(OPERATIONS) or len(tools) != len(OPERATIONS):
            raise TaskError('INTEGRITY_FAILURE')
        self.tools = [types.Tool(name=tool['name'], description=OPERATIONS[tool['name']][1],
                                 inputSchema=tool['inputSchema'], annotations=tool['annotations']) for tool in tools]
        self.inputs = {tool['name']: Draft202012Validator(tool['inputSchema']) for tool in tools}
        result_schema = json.loads((design / 'MCP_RESULT_SCHEMA.json').read_text())
        self.output = Draft202012Validator(result_schema)
        self.error_codes = set(result_schema['oneOf'][1]['properties']['error']['properties']['code']['enum'])

    def call(self, name, arguments):
        try:
            if name not in self.inputs:
                raise TaskError('INVALID_ARGUMENT')
            # Bound the semantic request size and reject invalid JSON values at the boundary.
            if len(canonical(arguments).encode('utf-8')) > 16384 or not self.inputs[name].is_valid(arguments):
                raise TaskError('INVALID_ARGUMENT')
            result = self.manager.execute(OPERATIONS[name][0], arguments)
            if not self.output.is_valid(result):
                raise TaskError('INTEGRITY_FAILURE')
            return result
        except TaskError as error:
            code = error.code
            if code in {'APPROVAL_LOCKED', 'PHASE_HOLD'}:
                return _error('REVIEW_LOCKED', 'Operator approval is locked pending platform verification.')
            if code in {'FORBIDDEN', 'RUNTIME_INACTIVE'}:
                return _error('NOT_FOUND_OR_FORBIDDEN', 'The task or its runtime is unavailable to this binding.')
            if code in {'INVALID_ARGUMENT', 'REQUEST_TOO_LARGE', 'RESPONSE_TOO_LARGE'}:
                return _error('INVALID_ARGUMENT', 'The request does not satisfy the task contract.')
            if code == 'COMMIT_OUTCOME_UNKNOWN':
                return _error('INTERNAL_ERROR', 'Retry with the original idempotency key.', True)
            if code in self.error_codes:
                return _error(code, error.to_dict()['message'], error.retryable)
            return _error('INTERNAL_ERROR', 'The task operation failed.')
        except (ValueError, TypeError, UnicodeError, RecursionError):
            return _error('INVALID_ARGUMENT', 'The request does not satisfy the task contract.')
        except Exception:
            # Server paths, model input, SQL and tracebacks must stay off the tool wire.
            logging.getLogger(__name__).error('Internal task adapter error')
            return _error('INTERNAL_ERROR', 'The task operation failed.')


class BoundedStdin:
    """Provide complete, bounded UTF-8 lines to the SDK's JSON-RPC parser."""
    def __init__(self, source):
        self.source = source
        self.invalid = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        raw = await anyio.to_thread.run_sync(self.source.readline, MAX_WIRE_BYTES + 1)
        if not raw:
            raise StopAsyncIteration
        if len(raw) <= MAX_WIRE_BYTES and raw.endswith(b'\n'):
            try:
                return raw.decode('utf-8')
            except UnicodeDecodeError:
                pass
        # Close this session without draining attacker-controlled input or logging it.
        self.invalid = True
        raise StopAsyncIteration


@contextmanager
def wire_input():
    # Retain the SDK's usual stdin isolation when supplying an explicit reader.
    fd = os.dup(0)
    try:
        with open(os.devnull, 'rb') as empty:
            os.dup2(empty.fileno(), 0)
        with os.fdopen(fd, 'rb', closefd=False) as source:
            yield BoundedStdin(source)
    finally:
        try:
            os.dup2(fd, 0)
        finally:
            os.close(fd)


async def serve(manager):
    adapter = ToolAdapter(manager)

    async def list_tools(context, params):
        return types.ListToolsResult(tools=adapter.tools)

    async def call_tool(context, params):
        arguments = params.arguments if params.arguments is not None else {}
        result = await anyio.to_thread.run_sync(adapter.call, params.name, arguments)
        return types.CallToolResult(content=[types.TextContent(type='text', text=canonical(result))],
                                    isError=not result['ok'])

    server = Server('aars-task-dev', version=VERSION, on_list_tools=list_tools, on_call_tool=call_tool)
    with wire_input() as stdin:
        async with stdio_server(stdin=stdin) as (reader, writer):
            await server.run(reader, writer, server.create_initialization_options())
    if stdin.invalid:
        raise TaskError('INVALID_WIRE_FRAME')


def development_repository(data_root):
    base = ROOT / '.devdata'
    directory = Path(data_root).absolute()
    if directory.resolve() != directory or base not in directory.parents:
        raise TaskError('INVALID_STORAGE_ROOT')
    binding = json.loads((ROOT / 'frozen_payload' / 'RUNTIME_BINDING.json').read_text())
    protected = (ROOT/'frozen_payload', ROOT/'frozen_archive', Path(binding['database_path']),
                 Path(binding['source_path']).parents[1])
    return Repository.open(directory/'tasks.sqlite', allowed_root=directory, protected_roots=protected)


def main():
    parser = argparse.ArgumentParser(description='Attach the development stdio server to an existing coordinator.')
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--binding-id', required=True, help='Trusted launcher setting, never sourced from MCP.')
    arguments = parser.parse_args()
    try:
        repository = development_repository(arguments.data_root)
        def attach(db):
            principal, _ = repository.principal(db, arguments.binding_id)
            boot = repository.meta(db, 'active_boot')
            repository.assert_runtime(boot)
            return boot
        boot = repository.read(attach)
        anyio.run(serve, TaskManager(repository, arguments.binding_id, boot))
    except (TaskError, OSError, ValueError) as error:
        print(error.code if isinstance(error, TaskError) else 'MCP_STARTUP_FAILED', file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == '__main__':
    main()
