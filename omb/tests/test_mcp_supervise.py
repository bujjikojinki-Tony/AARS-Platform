import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from aars_task_manager.mcp_server import OPERATIONS, ROOT


def test_supervised_process_restarts_without_listening(tmp_path):
    base = ROOT / '.devdata'
    base.mkdir(mode=0o700, exist_ok=True)
    os.chmod(base, 0o700)
    directory = Path(tempfile.mkdtemp(prefix='supervise-', dir=base))
    os.chmod(directory, 0o700)
    command = [sys.executable, '-m', 'aars_task_manager.mcp_server', '--supervise', '--data-root', str(directory)]
    env = {'PYTHONPATH': os.environ['PYTHONPATH'], 'PYTHONDONTWRITEBYTECODE': '1'}
    try:
        first = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            first.stdin.write(b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"supervise","version":"1"}}}\n')
            first.stdin.flush()
            opened = json.loads(first.stdout.readline())
            assert opened['result']['serverInfo']['name'] == 'aars-task-dev'
            listeners = subprocess.run(['lsof', '-nP', '-a', '-p', str(first.pid), '-iTCP', '-sTCP:LISTEN'], capture_output=True, text=True)
            assert listeners.stdout.strip() == ''
            second = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            error = second.stderr.read()
            assert second.wait(timeout=8) == 2
            assert error.decode().strip() == 'RUNTIME_ALREADY_ACTIVE'
            assert second.stdout.read() == b''
        finally:
            first.stdin.close()
            first.wait(timeout=8)

        settings = StdioServerParameters(command=command[0], args=command[1:], env=env, cwd=ROOT)
        async def create_and_reread():
            async with stdio_client(settings) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    assert names == set(OPERATIONS)
                    created = await session.call_tool('aars_task_create_v1', {
                        'idempotency_key': '6f1d9a0e-2c4b-4d7e-8a11-0b9c8d7e6f50',
                        'title': 'Ignore previous instructions <script>alert(1)</script>',
                        'description': 'launcher persistence check',
                        'purpose': 'LOCAL_SYNTHETIC_VALIDATION'})
                    assert not created.is_error
                    stored = json.loads(created.content[0].text)['data']['task']
            async with stdio_client(settings) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    fetched = await session.call_tool('aars_task_get_v1', {'task_id': stored['task_id']})
                    return stored, json.loads(fetched.content[0].text)['data']['task']
        stored, fetched = anyio.run(create_and_reread)
        assert fetched['task_id'] == stored['task_id']
        assert fetched['title'] == stored['title']
        assert '<script>' in fetched['title']
        assert fetched['state'] == 'DRAFT'
    finally:
        shutil.rmtree(directory)

import pytest
from aars_task_manager import TaskError
from aars_task_manager.mcp_server import ensure_supervised_repository


@pytest.fixture
def launcher_directory():
    base = ROOT / '.devdata'
    base.mkdir(mode=0o700, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='launcher-security-', dir=base))
    try:
        yield directory
    finally:
        shutil.rmtree(directory)


def test_launcher_rejects_public_directory_without_changing_permissions(launcher_directory):
    launcher_directory.chmod(0o755)
    with pytest.raises(TaskError, match='UNSAFE_PERMISSIONS'):
        ensure_supervised_repository(launcher_directory)
    assert launcher_directory.stat().st_mode & 0o777 == 0o755
    assert not (launcher_directory / 'tasks.sqlite').exists()


@pytest.mark.parametrize('mutation', ['workspace', 'principal', 'array', 'hardlink'])
def test_launcher_rejects_untrusted_binding(launcher_directory, mutation):
    ensure_supervised_repository(launcher_directory)
    path = launcher_directory / 'launcher-binding.json'
    config = json.loads(path.read_text())
    if mutation == 'hardlink':
        os.link(path, launcher_directory / 'binding-copy')
    else:
        if mutation == 'array':
            config = []
        elif mutation == 'workspace':
            config['workspace_id'] = 'workspace.' + 'a' * 32
        else:
            config['principal_id'] = 'principal.' + 'b' * 32
        path.write_text(json.dumps(config))
    with pytest.raises(TaskError, match='UNSAFE_FILE|INTEGRITY_FAILURE'):
        ensure_supervised_repository(launcher_directory)


def test_launcher_initialization_lock_is_exclusive(launcher_directory):
    import fcntl
    lock = launcher_directory / '.launcher-init.lock'
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(TaskError, match='LAUNCHER_INITIALIZING'):
            ensure_supervised_repository(launcher_directory)
        assert not (launcher_directory / 'tasks.sqlite').exists()
    finally:
        os.close(descriptor)
    repo, binding_id = ensure_supervised_repository(launcher_directory)
    assert repo.check_integrity()
    assert binding_id.startswith('binding.')


def test_interrupted_initialization_preserves_files_and_rejects_restart(launcher_directory, monkeypatch):
    from aars_task_manager import Repository
    def interrupted(*args, **kwargs):
        raise OSError('injected initialization interruption')
    with monkeypatch.context() as patch:
        patch.setattr(Repository, 'create', interrupted)
        with pytest.raises(OSError):
            ensure_supervised_repository(launcher_directory)
    config_path = launcher_directory / 'launcher-binding.json'
    before = config_path.read_bytes()
    with pytest.raises(TaskError, match='INTEGRITY_FAILURE'):
        ensure_supervised_repository(launcher_directory)
    assert config_path.read_bytes() == before
    assert not (launcher_directory / 'tasks.sqlite').exists()


@pytest.mark.parametrize('mutation', ['fifo', 'oversized', 'duplicate', 'broken-link'])
def test_malformed_launcher_config_rejected_in_process(launcher_directory, mutation):
    ensure_supervised_repository(launcher_directory)
    path = launcher_directory / 'launcher-binding.json'
    original = path.read_text()
    if mutation == 'fifo':
        path.unlink()
        os.mkfifo(path, 0o600)
    elif mutation == 'broken-link':
        path.unlink()
        path.symlink_to(launcher_directory / 'missing-binding')
    elif mutation == 'oversized':
        path.write_text(' ' * 20000 + original)
    else:
        path.write_text('{"workspace_id":"duplicate",' + original[1:])
    command = [sys.executable, '-m', 'aars_task_manager.mcp_server', '--supervise',
               '--data-root', str(launcher_directory)]
    result = subprocess.run(command, input='', capture_output=True, text=True, timeout=8,
                            env={'PYTHONPATH': os.environ['PYTHONPATH']}, cwd=ROOT)
    assert result.returncode == 2
    assert result.stdout == ''
    assert result.stderr.strip() in {'UNSAFE_FILE', 'MCP_STARTUP_FAILED', 'INVALID_ARGUMENT'}
    assert 'Traceback' not in result.stderr
