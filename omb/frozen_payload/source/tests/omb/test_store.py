import json,sqlite3,subprocess,sys,os
import pytest
from aars_omb.server import call,graph,Session
from aars_omb.store import Store

@pytest.fixture
def store(tmp_path): return Store(tmp_path/'db.sqlite')

def test_persist(store):
    r=call('aars_fixture_store',{'task_id':'OMB-SIM-1'},store); assert r['created'] and r['object_count']==9
    q=call('aars_evidence_query',{'task_id':'OMB-SIM-1'},Store(store.path)); assert q['object_count']==1 and q['objects'][0]['record']['observation_ids'] and not q['execution_authorized']

def test_idempotent(store):
    a={'task_id':'OMB-SIM-1'}; call('aars_fixture_store',a,store); before=call('aars_task_objects',a,store); assert not call('aars_fixture_store',a,store)['created']; assert before==call('aars_task_objects',a,store)

def test_isolation(store):
    call('aars_fixture_store',{'task_id':'OMB-SIM-1'},store); assert not call('aars_task_objects',{'task_id':'OMB-SIM-2'},store)['found']

@pytest.mark.parametrize('args',[{'task_id':'real'},{'task_id':'OMB-SIM-../x'},{'task_id':'OMB-SIM-1','payload':{}},{'task_id':1}])
def test_bad_args(store,args):
    with pytest.raises(ValueError): call('aars_fixture_store',args,store)

def test_no_store():
    with pytest.raises(ValueError): call('aars_fixture_store',{'task_id':'OMB-SIM-1'})

def test_invalid_graph(store):
    c,g=graph()
    with pytest.raises(ValueError): store.seed('OMB-SIM-1',c,g[1:])
    assert not store.query('OMB-SIM-1')['found']

def test_tamper(store):
    call('aars_fixture_store',{'task_id':'OMB-SIM-1'},store)
    with sqlite3.connect(store.path) as db: db.execute("UPDATE objects SET record='{}' WHERE type='evidence'")
    with pytest.raises(ValueError): store.query('OMB-SIM-1','evidence')

def test_restart_stdio(store):
    def run(name):
        msgs=[{'id':1,'method':'initialize'},{'method':'notifications/initialized'},{'id':2,'method':'tools/list'},{'id':3,'method':'tools/call','params':{'name':name,'arguments':{'task_id':'OMB-SIM-restart'}}}]
        from protocol_helper import exchange
        a=exchange(msgs,env={**os.environ,'AARS_OMB_DB':str(store.path)})
        assert len(a[1]['result']['tools'])==5; assert not a[2]['result']['isError']; return json.loads(a[2]['result']['content'][0]['text'])
    assert run('aars_fixture_store')['created']; assert run('aars_evidence_query')['object_count']==1
