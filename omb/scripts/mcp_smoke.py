"""Exercise the actual development CLI via the official MCP SDK and real pipes."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import selectors
import subprocess
import sys
import tempfile
from uuid import uuid4

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from aars_task_manager import TaskRuntime
from aars_task_manager.migration import migrate_c2_copy, migrate_d3_copy
from aars_task_manager.storage import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[1]


def wire_initialize(command, env, version):
    with subprocess.Popen(command, cwd=ROOT, env=env, text=True, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as server:
        try:
            request = {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':version,
                        'capabilities':{},'clientInfo':{'name':'omb-003d-probe','version':'1'}}}
            server.stdin.write(json.dumps(request)+'\n'); server.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(server.stdout, selectors.EVENT_READ)
                if not selector.select(8):
                    raise TimeoutError('initialize response deadline')
                response = json.loads(server.stdout.readline())
            server.stdin.close()
            if server.wait(timeout=8) != 0:
                raise RuntimeError('stdio shutdown failed')
            assert response['result']['serverInfo']['name'] == 'aars-task-dev'
            return {'request':request,'response':response,'exit_code':server.returncode}
        finally:
            if server.poll() is None:
                server.kill(); server.wait(timeout=3)


async def sdk_exercise(command, env):
    trace = []
    args = {'idempotency_key':str(uuid4()),'title':'Isolated MCP smoke','description':'','purpose':'LOCAL_SYNTHETIC_VALIDATION'}
    config = StdioServerParameters(command=command[0], args=command[1:], env={k:env[k] for k in ('PYTHONPATH','PYTHONDONTWRITEBYTECODE')})
    async with stdio_client(config) as (reader,writer):
        async with ClientSession(reader,writer) as client:
            init = await client.initialize()
            trace.append({'method':'initialize','response':init.model_dump(mode='json',by_alias=True)})
            listing = await client.list_tools()
            tool_names = [tool.name for tool in listing.tools]
            assert len(tool_names) == 9
            assert all('approve' not in name and 'receipt' not in name and 'challenge' not in name
                       for name in tool_names)
            trace.append({'method':'tools/list','tools':tool_names})
            async def call(name, arguments, expect_error=False):
                response = await client.call_tool(name, arguments)
                assert bool(response.is_error) == expect_error
                raw = response.model_dump(mode='json',by_alias=True)
                trace.append({'method':'tools/call','tool':name,'arguments':arguments,'response':raw})
                return json.loads(response.content[0].text)
            created = await call('aars_task_create_v1',args)
            replay = await call('aars_task_create_v1',args)
            assert replay['replayed'] and replay['data'] == created['data']
            refused = await call('aars_task_create_v1',{**args,'approved':True},True)
            assert refused['error']['code']=='INVALID_ARGUMENT'
            task_id = created['data']['task']['task_id']
            await call('aars_task_get_v1',{'task_id':task_id})
            await call('aars_task_events_v1',{'task_id':task_id})
    return trace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('offline_source', type=Path)
    parser.add_argument('--source-schema', type=int, choices=(2, 3), default=2)
    args = parser.parse_args()
    source = args.offline_source.resolve(strict=True)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    base = ROOT/'.devdata';base.mkdir(mode=0o700,exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix=f'd{SCHEMA_VERSION}-mcp-',dir=base))
    frozen_path = Path(json.loads((ROOT/'frozen_payload/RUNTIME_BINDING.json').read_text())['database_path'])
    migrate = migrate_d3_copy if args.source_schema == 3 else migrate_c2_copy
    repo = migrate(source,target/'tasks.sqlite',source_root=source.parent,target_root=target,
                           protected_roots=(frozen_path.parents[1],ROOT/'frozen_payload',ROOT/'frozen_archive'))
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join((str(ROOT/'src'),str(ROOT/'frozen_payload/source/src')))
    env['PYTHONDONTWRITEBYTECODE']='1'
    binding = repo.read(lambda db:db.execute("SELECT binding_id FROM principals WHERE kind='BOT' AND active=1").fetchone()[0])
    command = [sys.executable,'-m','aars_task_manager.mcp_server','--data-root',str(target),'--binding-id',binding]
    with TaskRuntime(repo) as runtime:
        probe = [wire_initialize(command,env,version) for version in ('2024-11-05','2025-06-18','2025-11-25','2099-01-01')]
        traces = anyio.run(sdk_exercise, command, env)
        assert runtime.boot_id == repo.read(lambda db:repo.meta(db,'active_boot'))
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before == after and repo.check_integrity()
    print(json.dumps({'scope':'Local development CLI, real SDK and stdio, isolated database copy',
        'source_schema': args.source_schema, 'source_sha256_before':before, 'source_sha256_after':after,
        'target_schema': repo.read(lambda db:db.execute('PRAGMA user_version').fetchone()[0]),
        'protocol_probes':probe,'sdk_trace':traces,'coordinator_reused':True,'status':'PASS'},indent=2))

if __name__ == '__main__':
    main()
