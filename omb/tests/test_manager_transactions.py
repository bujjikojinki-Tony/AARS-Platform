from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
import multiprocessing
import sqlite3
import time
import pytest
from aars_task_manager import TaskError
from tests.support import create,key,process_create

def test_idempotent_create_replay_and_current_view(system):
    m=system['manager'];k=key();args={'idempotency_key':k,'title':'same','description':'','purpose':'LOCAL_SYNTHETIC_VALIDATION'}
    a=m.execute('create',args);b=m.execute('create',args)
    assert a['data']==b['data'] and not a['replayed'] and b['replayed']
    tid=a['data']['task']['task_id'];m.execute('update',{'task_id':tid,'expected_version':1,'idempotency_key':key(),'patch':{'title':'changed'}})
    old=m.execute('create',args)
    assert old['replayed'] and old['data']['task']['version']==1 and m.get(tid)['data']['task']['version']==2
    assert len(m.list_tasks()['data']['tasks'])==1

def test_key_cannot_change_request(system):
    m=system['manager'];k=key();args={'idempotency_key':k,'title':'one','description':'','purpose':'LOCAL_SYNTHETIC_VALIDATION'}
    m.execute('create',args)
    with pytest.raises(TaskError,match='IDEMPOTENCY_CONFLICT'):m.execute('create',{**args,'title':'two'})
    assert len(m.list_tasks()['data']['tasks'])==1

def test_key_cannot_change_method(system):
    m=system['manager'];k=key();t=create(m,idempotency_key=k)
    with pytest.raises(TaskError,match='IDEMPOTENCY_CONFLICT'):m.execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':k,'patch':{'title':'x'}})

@pytest.mark.parametrize('bad',['not-a-uuid','',None,'1'*32])
def test_invalid_idempotency_key(system,bad):
    with pytest.raises(TaskError,match='INVALID_ARGUMENT'):create(system['manager'],idempotency_key=bad)

def test_threaded_same_key_only_one_commit(system):
    m=system['manager'];k=key();args={'idempotency_key':k,'title':'concurrent','description':'','purpose':'LOCAL_SYNTHETIC_VALIDATION'}
    with ThreadPoolExecutor(max_workers=8) as pool:r=list(pool.map(lambda _:m.execute('create',args),range(24)))
    assert sum(not x['replayed'] for x in r)==1
    assert len({x['data']['task']['task_id'] for x in r})==1

def test_cas_two_concurrent_updates(system):
    m=system['manager'];t=create(m)
    def change(title):
        try:return m.execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'patch':{'title':title}})['data']['task']['version']
        except TaskError as e:return e.code
    with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(change,['one','two']))
    assert sorted(map(str,r))==['2','VERSION_CONFLICT']
    assert len(m.events(t['task_id'])['data']['events'])==2

def test_process_same_key_only_one_commit(system):
    repo=system['repo'];m=system['manager'];k=key();args=(str(repo.path),str(repo.root),str(system['protected']),m.binding_id,m.boot_id,k)
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures=[pool.submit(process_create,*args) for _ in range(9)];r=[x.result(timeout=25) for x in futures]
    assert sum(not x['replayed'] for x in r)==1
    assert len({x['data']['task']['task_id'] for x in r})==1

def test_mid_transaction_rollback_and_same_key_retry(system,monkeypatch):
    repo=system['repo'];m=system['manager'];t=create(m);k=key();old=repo._append_event
    def fail(*args,**kwargs):raise RuntimeError('test-only fault after task update')
    monkeypatch.setattr(repo,'_append_event',fail)
    args={'task_id':t['task_id'],'expected_version':1,'idempotency_key':k,'patch':{'title':'atomic'}}
    with pytest.raises(RuntimeError):m.execute('update',args)
    assert m.get(t['task_id'])['data']['task']==t and len(m.events(t['task_id'])['data']['events'])==1
    assert repo.read(lambda db:db.execute('SELECT count(*) FROM idempotency_records WHERE idem_key=?',(k,)).fetchone()[0])==0
    monkeypatch.setattr(repo,'_append_event',old)
    assert m.execute('update',args)['data']['task']['version']==2

def test_lock_busy_bounded_and_retriable(system):
    repo=system['repo'];m=system['manager'];k=key();db=sqlite3.connect(repo.path,isolation_level=None);db.execute('BEGIN IMMEDIATE');began=time.monotonic()
    try:
        with pytest.raises(TaskError,match='DB_BUSY') as e:create(m,idempotency_key=k)
        assert e.value.retryable and time.monotonic()-began<5
    finally:db.execute('ROLLBACK');db.close()
    assert create(m,idempotency_key=k)['version']==1

def test_independent_actor_keys_do_not_collide(system):
    k=key();a=create(system['manager'],idempotency_key=k);b=create(system['other'],idempotency_key=k)
    assert a['task_id']!=b['task_id']
    assert len(system['manager'].list_tasks()['data']['tasks'])==len(system['other'].list_tasks()['data']['tasks'])==1
