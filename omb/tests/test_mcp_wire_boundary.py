"""Exercise process framing through the real private-development CLI."""
from datetime import datetime, timezone
import json
from pathlib import Path
import os
import selectors
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import pytest

from aars_task_manager import Binding, Repository, State, TaskRuntime
from aars_task_manager.domain import new_id, stamp
from aars_task_manager.mcp_server import MAX_WIRE_BYTES
from tests.support import seed_precondition

CAPABILITIES = ('task.create', 'task.read', 'task.update', 'task.work', 'evidence.link', 'review.request')

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_wire():
    base = ROOT / '.devdata'
    base.mkdir(mode=0o700, exist_ok=True)
    with TemporaryDirectory(dir=base, prefix='wire-test-') as tmp:
        directory = Path(tmp)
        binding = Binding(new_id('binding'), new_id('principal'), CAPABILITIES)
        repo = Repository.create(directory / 'tasks.sqlite', allowed_root=directory,
                                 protected_roots=(ROOT / 'frozen_payload',), workspace_id=new_id('workspace'),
                                 bindings=[binding], created_at=stamp(datetime.now(timezone.utc)))
        with TaskRuntime(repo) as runtime:
            args = [sys.executable, '-m', 'aars_task_manager.mcp_server', '--data-root', str(directory),
                    '--binding-id', binding.binding_id]
            yield args, runtime.manager(binding.binding_id), runtime


def request(method, params, rid=None):
    frame = {'jsonrpc': '2.0', 'method': method, 'params': params}
    if rid is not None:
        frame['id'] = rid
    return json.dumps(frame, separators=(',', ':')).encode()


def initialize(version='2025-11-25'):
    return request('initialize', {'protocolVersion': version, 'capabilities': {},
                                 'clientInfo': {'name': 'wire-boundary', 'version': '1'}}, 1)


def read_response(pipe):
    with selectors.DefaultSelector() as selector:
        selector.register(pipe, selectors.EVENT_READ)
        assert selector.select(10), 'MCP response deadline exceeded'
        return json.loads(pipe.readline())


def test_wire_boundary_accepts_exact_cap_and_keeps_sdk_negotiation(isolated_wire):
    command, _, _ = isolated_wire
    frame = initialize('2025-06-18')
    crafted = frame + b' ' * (MAX_WIRE_BYTES - len(frame) - 1) + b'\n'
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        proc.stdin.write(crafted)
        proc.stdin.flush()
        response = read_response(proc.stdout)
        assert response['result']['protocolVersion'] == '2025-06-18'
        proc.stdin.close()
        assert proc.wait(timeout=10) == 0
        assert proc.stderr.read() == b''


@pytest.mark.parametrize('bad', ['oversized', 'invalid-utf8', 'truncated'])
def test_invalid_frame_terminates_without_processing_or_echoing(isolated_wire, bad):
    command, manager, _ = isolated_wire
    task_args = {'idempotency_key': str(uuid4()), 'title': 'wire rejection fixture',
                 'description': '', 'purpose': 'LOCAL_SYNTHETIC_VALIDATION'}
    good_tool = request('tools/call', {'name': 'aars_task_create_v1', 'arguments': task_args}, 2)
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        proc.stdin.write(initialize() + b'\n')
        proc.stdin.flush()
        assert read_response(proc.stdout)['result']['serverInfo']['name'] == 'aars-task-dev'
        proc.stdin.write(request('notifications/initialized', {}) + b'\n')
        if bad == 'oversized':
            frame = good_tool + b' ' * (MAX_WIRE_BYTES - len(good_tool)) + b'\n'
        elif bad == 'invalid-utf8':
            frame = good_tool.replace(b'wire rejection fixture', b'invalid-\xff') + b'\n'
        else:
            frame = good_tool  # Full JSON without the transport delimiter.
        proc.stdin.write(frame)
        proc.stdin.flush()
        # Complete invalid frames must close the session while the peer is still open.
        if bad == 'truncated':
            proc.stdin.close()
        assert proc.wait(timeout=10) == 2
        assert proc.stdout.read() == b''
        assert proc.stderr.read() == b'INVALID_WIRE_FRAME\n'
    assert manager.list_tasks()['data']['tasks'] == []


def test_live_stdio_review_rechecks_evidence_after_host_revocation(isolated_wire):
    command, manager, runtime = isolated_wire
    source = runtime.register_frozen_fixture()
    task, attempt = seed_precondition(manager.repository, manager, State.RUNNING, runtime.clock)
    identity = {'task_id': task['task_id'], 'attempt_id': attempt['attempt_id'],
                'fencing_token': attempt['fencing_token']}
    launch = StdioServerParameters(command=command[0], args=command[1:],
        env={'PYTHONPATH': os.environ['PYTHONPATH'], 'PYTHONDONTWRITEBYTECODE': '1'})

    async def exercise():
        async with stdio_client(launch) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()

                async def call(name, args, *, error=False):
                    reply = await client.call_tool('aars_task_' + name + '_v1', args)
                    assert bool(reply.is_error) == error
                    return json.loads(reply.content[0].text)

                linked = await call('evidence_link', {**identity,
                    'expected_version': task['version'], 'idempotency_key': str(uuid4()),
                    'snapshot_id': source['evidence_snapshot_id']})
                receipt_args = {**identity, 'idempotency_key': str(uuid4()),
                                'expected_version': linked['data']['task']['version']}
                requested = await call('review_request', receipt_args)
                assert requested['data']['task']['state'] == 'REVIEW_PENDING'
                assert requested['data']['review']['status'] == 'PENDING'
                assert requested['execution_authorized'] is False
                assert (await call('review_request', receipt_args))['replayed']
                assert runtime.revoke_frozen_fixture('test grant withdrawn') == 1
                replay = await call('review_request', receipt_args, error=True)
                assert replay['error']['code'] == 'REVIEW_STALE'
                current = await call('get', {'task_id': task['task_id']})
                assert current['data']['task']['state'] == 'PAUSED'
                assert current['data']['review'] is None

    async def bounded_exercise():
        with anyio.fail_after(15):
            await exercise()

    anyio.run(bounded_exercise)
    trace = manager.evidence_trace(task['task_id'])
    assert trace['current'][0]['effective_use_state'] == 'REVOKED'
