import os
import json
import sys
from concurrent.futures import ThreadPoolExecutor
import pytest
from aars_omb.server import call
from aars_omb.store import Store

def test_private_database(tmp_path):
    s=Store(tmp_path/'private.sqlite')
    assert s.path.stat().st_mode & 0o777 == 0o600

def test_refuse_symlink(tmp_path):
    target=tmp_path/'other';target.write_text('do not overwrite')
    link=tmp_path/'linked.sqlite';link.symlink_to(target)
    with pytest.raises(OSError): Store(link)
    assert target.read_text()=='do not overwrite'

def test_refuse_shared_parent(tmp_path):
    d=tmp_path/'shared'; d.mkdir(mode=0o755)
    with pytest.raises(ValueError): Store(d/'db')

def test_concurrent_idempotency(tmp_path):
    store=Store(tmp_path/'db')
    def write(_): return call('aars_fixture_store',{'task_id':'OMB-SIM-concurrent'},store)
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(write,range(24)))
    assert sum(r['created'] for r in results)==1
    assert Store(store.path).query('OMB-SIM-concurrent')['object_count']==9

def test_transaction_rollback(tmp_path):
    store=Store(tmp_path/'db')
    from contextlib import closing
    with closing(store.connect()) as db, db:
        db.execute("CREATE TRIGGER reject_objects BEFORE INSERT ON objects BEGIN SELECT RAISE(ABORT, 'test rollback'); END")
    with pytest.raises(Exception): call('aars_fixture_store',{'task_id':'OMB-SIM-rollback'},store)
    assert not store.query('OMB-SIM-rollback')['found']

def test_official_client_restart(tmp_path):
    import anyio
    from mcp.client import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    db=tmp_path/'db'
    async def run(name):
        params=StdioServerParameters(command=sys.executable,args=['-m','aars_omb.server'],env={**os.environ,'AARS_OMB_DB':str(db)})
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=10) as session:
                init=await session.initialize()
                assert init.server_info.name=='aars-omb'
                tools=await session.list_tools();assert len(tools.tools)==5
                denied=await session.call_tool('aars_fixture_store',{'task_id':'real'})
                assert denied.is_error
                result=await session.call_tool(name,{'task_id':'OMB-SIM-official'})
                assert not result.is_error
                return json.loads(result.content[0].text)
    assert anyio.run(run,'aars_fixture_store')['created']
    assert anyio.run(run,'aars_evidence_query')['object_count']==1
