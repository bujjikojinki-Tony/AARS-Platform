"""OMB-003D Bot-facing stdio transport. The operator control plane is separate."""
from __future__ import annotations

from contextlib import contextmanager

import argparse
import fcntl
import json
import logging
import os
import stat
from pathlib import Path
import sys

import anyio
from jsonschema import Draft202012Validator
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .domain import canonical, new_id, stamp
from .errors import TaskError
from .runtime import TaskRuntime
from .service import TaskManager
from .storage import Binding, Repository

ROOT = Path(__file__).resolve().parents[2]
VERSION = '0.3.0b9'
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


LAUNCHER_CAPABILITIES = ('evidence.link', 'review.request', 'task.create', 'task.read', 'task.update', 'task.work')


def protected_roots():
    binding = json.loads((ROOT / 'frozen_payload' / 'RUNTIME_BINDING.json').read_text())
    return (ROOT/'frozen_payload', ROOT/'frozen_archive', Path(binding['database_path']),
            Path(binding['source_path']).parents[1])


def development_directory(data_root):
    base = (ROOT / '.devdata').absolute()
    directory = Path(data_root).absolute()
    if directory.resolve() != directory or base not in directory.parents:
        raise TaskError('INVALID_STORAGE_ROOT')
    return directory


def development_repository(data_root):
    directory = development_directory(data_root)
    return Repository.open(directory/'tasks.sqlite', allowed_root=directory, protected_roots=protected_roots())


def ensure_supervised_repository(data_root):
    """Open the launcher-owned database. The binding file is not accepted from MCP."""
    directory = development_directory(data_root)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise TaskError('UNSAFE_PERMISSIONS')
    # Serialize initialization separately from the long-lived runtime lock.
    descriptor = os.open(directory / '.launcher-init.lock',
                         os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.getuid() or info.st_mode & 0o077):
            raise TaskError('UNSAFE_FILE')
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise TaskError('LAUNCHER_INITIALIZING') from None
        return _open_launcher_repository(directory)
    finally:
        os.close(descriptor)


def _open_launcher_repository(directory):
    from datetime import datetime, timezone
    config_path = directory / 'launcher-binding.json'
    database = directory / 'tasks.sqlite'
    if os.path.lexists(config_path) != os.path.lexists(database):
        raise TaskError('INTEGRITY_FAILURE')
    if not config_path.exists():
        config = {'workspace_id': new_id('workspace'), 'binding_id': new_id('binding'),
                  'principal_id': new_id('principal'), 'capabilities': list(LAUNCHER_CAPABILITIES)}
        fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as handle:
            json.dump(config, handle)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        Repository.create(database, allowed_root=directory, protected_roots=protected_roots(),
                          workspace_id=config['workspace_id'],
                          bindings=(Binding(config['binding_id'], config['principal_id'], LAUNCHER_CAPABILITIES),),
                          created_at=stamp(datetime.now(timezone.utc)))
    descriptor = os.open(config_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'r') as handle:
        info = os.fstat(handle.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.getuid() or info.st_mode & 0o077):
            raise TaskError('UNSAFE_FILE')
        raw = handle.read(16385)
        if len(raw.encode('utf-8')) > 16384:
            raise TaskError('INVALID_ARGUMENT')
        def unique_fields(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise TaskError('INVALID_ARGUMENT')
                result[key] = value
            return result
        config = json.loads(raw, object_pairs_hook=unique_fields)
    if not isinstance(config, dict) or set(config) != {'workspace_id', 'binding_id', 'principal_id', 'capabilities'}:
        raise TaskError('INTEGRITY_FAILURE')
    if config['capabilities'] != list(LAUNCHER_CAPABILITIES):
        raise TaskError('INTEGRITY_FAILURE')
    repository = development_repository(directory)
    def verify_binding(db):
        principal, capabilities = repository.principal(db, config['binding_id'])
        if (repository.meta(db, 'workspace_id') != config['workspace_id']
                or principal['principal_id'] != config['principal_id']
                or set(capabilities) != set(LAUNCHER_CAPABILITIES)):
            raise TaskError('INTEGRITY_FAILURE')
    repository.read(verify_binding)
    return repository, config['binding_id']


def main():
    parser = argparse.ArgumentParser(description='Development stdio server. It never listens on a network port.')
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--binding-id', help='Trusted launcher setting for attach mode, never sourced from MCP.')
    parser.add_argument('--supervise', action='store_true', help='Own the coordinator and database in this process.')
    arguments = parser.parse_args()
    try:
        if arguments.supervise:
            if arguments.binding_id:
                raise TaskError('INVALID_ARGUMENT')
            repository, binding_id = ensure_supervised_repository(arguments.data_root)
            with TaskRuntime(repository) as runtime:
                anyio.run(serve, runtime.manager(binding_id))
        else:
            if not arguments.binding_id:
                raise TaskError('INVALID_ARGUMENT')
            repository = development_repository(arguments.data_root)
            def attach(db):
                repository.principal(db, arguments.binding_id)
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
