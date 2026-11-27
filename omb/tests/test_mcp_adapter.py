import json
from pathlib import Path
import os
import sys

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from aars_task_manager import State
from aars_task_manager.mcp_server import ToolAdapter, OPERATIONS
from tests.support import seed_precondition, key


def test_sdk_stdio_initialize_list_call_and_eof(system):
    manager = system['manager']; repo = system['repo']
    # New OS process attaches to the existing coordinator and uses the production serve() adapter.
    code = ('import anyio,sys; from pathlib import Path; from aars_task_manager import Repository,TaskManager; '
            'from aars_task_manager.mcp_server import serve; '
            'p=Path(sys.argv[1]); r=Repository.open(p,allowed_root=p.parent,protected_roots=(Path(sys.argv[2]),)); '
            'anyio.run(serve,TaskManager(r,sys.argv[3],sys.argv[4]))')
    launch = StdioServerParameters(command=sys.executable, args=['-c',code,str(repo.path),str(system['protected']),manager.binding_id,manager.boot_id],
                                   env={'PYTHONPATH':os.environ['PYTHONPATH'],'PYTHONDONTWRITEBYTECODE':'1'})
    async def run():
        async with stdio_client(launch) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                init = await session.initialize()
                assert init.server_info.name == 'aars-task-dev'
                tools = await session.list_tools()
                assert {t.name for t in tools.tools} == set(OPERATIONS)
                args = {'idempotency_key': key(),'title':'Real stdio draft','description':'','purpose':'LOCAL_SYNTHETIC_VALIDATION'}
                created = await session.call_tool('aars_task_create_v1', args)
                assert not created.is_error
                data = json.loads(created.content[0].text)
                assert not data['execution_authorized'] and data['data']['task']['state'] == 'DRAFT'
                rejected = await session.call_tool('aars_task_create_v1', {**args,'approved':True})
                assert rejected.is_error and json.loads(rejected.content[0].text)['error']['code'] == 'INVALID_ARGUMENT'
                return data['data']['task']['task_id']
    task = anyio.run(run)
    assert manager.get(task)['data']['task']['title'] == 'Real stdio draft'


def test_locked_start_maps_to_contract_error(system):
    m=system['manager'];t,_=seed_precondition(system['repo'],m,State.READY,system['clock'])
    adapter=ToolAdapter(m)
    response=adapter.call('aars_task_transition_v1',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'action':'start'})
    assert response['error']['code']=='REVIEW_LOCKED' and adapter.output.is_valid(response)


def test_mcp_legacy_tools_separate_and_approval_absent(system):
    adapter=ToolAdapter(system['manager'])
    contract=json.loads(Path('design/omb003a/MCP_TOOLS_CONTRACT.json').read_text())
    old={x['name'] for x in contract['legacy_frozen_tools_unchanged']}
    assert old.isdisjoint(OPERATIONS)
    for name in ['approve_result','prepare_challenge','submit_receipt',*old]:
        response=adapter.call(name,{})
        assert not response['ok'] and adapter.output.is_valid(response)
