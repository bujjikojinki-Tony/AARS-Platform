from pathlib import Path
import multiprocessing
import sqlite3
import pytest
from aars_task_manager import TaskError,TaskRuntime,Repository,State
from tests.support import create,key,seed_precondition,crash_runtime

def test_single_recovery_coordinator(system):
    t=create(system['manager']);boot=system['runtime'].boot_id
    with pytest.raises(TaskError,match='RUNTIME_ALREADY_ACTIVE'):
        with TaskRuntime(system['repo'],clock=system['clock']):pass
    assert system['manager'].get(t['task_id'])['data']['task']==t
    assert system['repo'].read(lambda db:system['repo'].meta(db,'active_boot'))==boot

def test_client_attachment_does_not_recover_other_client(system):
    t,a=seed_precondition(system['repo'],system['manager'],State.RUNNING,system['clock'])
    other=system['runtime'].manager(system['manager'].binding_id)
    assert other.get(t['task_id'])['data']['task']['state']=='RUNNING'

def test_close_then_restart_preserves_tasks_and_idempotency(system):
    m=system['manager'];repo=system['repo'];k=key();t=create(m,idempotency_key=k)
    system['runtime'].close()
    with pytest.raises(TaskError,match='RUNTIME_INACTIVE'):m.get(t['task_id'])
    with TaskRuntime(repo,clock=system['clock']) as second:
        n=second.manager(m.binding_id)
        assert n.get(t['task_id'])['data']['task']==t
        assert create(n,idempotency_key=k)['task_id']==t['task_id']

def test_real_child_crash_recovers_running_fixture(system):
    repo=system['repo'];binding=system['manager'].binding_id;system['runtime'].close()
    proc=multiprocessing.get_context('spawn').Process(target=crash_runtime,args=(str(repo.path),str(repo.root),str(system['protected']),binding))
    proc.start();proc.join(15);assert proc.exitcode==0
    reopened=Repository.open(repo.path,allowed_root=repo.root,protected_roots=(system['protected'],))
    with TaskRuntime(reopened,clock=system['clock']) as runtime:
        m=runtime.manager(binding);tasks=m.list_tasks()['data']['tasks'];assert len(tasks)==1 and tasks[0]['state']=='PAUSED'
        assert m.events(tasks[0]['task_id'])['data']['events'][-1]['event_type']=='RECOVERED'
        assert reopened.read(lambda db:db.execute('SELECT status FROM attempts').fetchone()[0])=='EXPIRED'

def test_expired_lease_recovery_is_idempotent(system):
    repo=system['repo'];t,a=seed_precondition(repo,system['manager'],State.RUNNING,system['clock']);system['clock'].advance(61)
    assert system['runtime'].recover_expired()==1
    assert system['runtime'].recover_expired()==0
    r=system['manager'].get(t['task_id'])['data']['task'];assert r['state']=='PAUSED' and r['version']==3

def test_unexpired_lease_not_interrupted(system):
    t,a=seed_precondition(system['repo'],system['manager'],State.RUNNING,system['clock'])
    assert system['runtime'].recover_expired()==0
    assert system['manager'].get(t['task_id'])['data']['task']==t

def test_late_expired_worker_write_rejected(system):
    t,a=seed_precondition(system['repo'],system['manager'],State.RUNNING,system['clock']);system['clock'].advance(61)
    with pytest.raises(TaskError,match='LEASE_EXPIRED'):system['manager'].execute('transition',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'action':'pause','reason':'late','attempt_id':a['attempt_id'],'fencing_token':a['fencing_token']})
    assert system['manager'].get(t['task_id'])['data']['task']==t

def test_stale_fencing_token_rejected(system):
    t,a=seed_precondition(system['repo'],system['manager'],State.RUNNING,system['clock'],fencing=2)
    with pytest.raises(TaskError,match='FENCING_CONFLICT'):system['manager'].execute('transition',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'action':'pause','reason':'old fence','attempt_id':a['attempt_id'],'fencing_token':1})

def test_valid_lease_holder_can_pause_without_approval(system):
    t,a=seed_precondition(system['repo'],system['manager'],State.RUNNING,system['clock']);m=system['manager']
    r=m.execute('transition',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'action':'pause','reason':'stop work safely','attempt_id':a['attempt_id'],'fencing_token':a['fencing_token']})
    assert r['data']['task']['state']=='PAUSED'
    assert system['repo'].read(lambda db:db.execute('SELECT status FROM attempts').fetchone()[0])=='PAUSED'

def test_start_still_requires_real_approval(system):
    t,_=seed_precondition(system['repo'],system['manager'],State.READY,system['clock'])
    with pytest.raises(TaskError,match='APPROVAL_LOCKED'):system['manager'].execute('transition',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'action':'start'})
    assert system['manager'].get(t['task_id'])['data']['task']==t

def test_renew_does_not_smuggle_in_plan_approval(system):
    t,a=seed_precondition(system['repo'],system['manager'],State.RUNNING,system['clock'])
    with pytest.raises(TaskError,match='APPROVAL_LOCKED'):system['manager'].execute('renew',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'attempt_id':a['attempt_id'],'fencing_token':a['fencing_token']})

@pytest.mark.parametrize('state',[State.COMPLETED,State.REJECTED,State.FAILED,State.CANCELLED])
def test_terminal_state_not_reopened(system,state):
    t,_=seed_precondition(system['repo'],system['manager'],state,system['clock']);m=system['manager']
    for action in ['start','cancel','pause','fail']:
        with pytest.raises(TaskError):m.execute('transition',{'task_id':t['task_id'],'expected_version':t['version'],'idempotency_key':key(),'action':action,'reason':'invalid'})
    assert m.get(t['task_id'])['data']['task']==t

def test_cross_process_cannot_start_second_coordinator(system):
    from concurrent.futures import ProcessPoolExecutor
    from tests.support import process_try_runtime
    repo=system['repo'];t=create(system['manager'])
    with ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn')) as pool:
        code=pool.submit(process_try_runtime,str(repo.path),str(repo.root),str(system['protected'])).result(timeout=15)
    assert code=='RUNTIME_ALREADY_ACTIVE'
    assert system['manager'].get(t['task_id'])['data']['task']==t

def test_reenter_runtime_object_does_not_reactivate_old_client(system):
    runtime=system['runtime'];old=system['manager'];t=create(old);old_boot=runtime.boot_id;runtime.close()
    with runtime:
        assert runtime.boot_id!=old_boot
        with pytest.raises(TaskError,match='RUNTIME_INACTIVE'):old.get(t['task_id'])
        assert runtime.manager(old.binding_id).get(t['task_id'])['data']['task']==t

def test_crashed_host_marker_does_not_allow_orphaned_client(system):
    from aars_task_manager import TaskManager
    from tests.support import orphaned_runtime,FakeClock
    repo=system['repo'];binding=system['manager'].binding_id;system['runtime'].close()
    ctx=multiprocessing.get_context('spawn');queue=ctx.Queue()
    p=ctx.Process(target=orphaned_runtime,args=(str(repo.path),str(repo.root),str(system['protected']),binding,queue));p.start()
    boot=queue.get(timeout=15);p.join(15);assert p.exitcode==0
    m=TaskManager(repo,binding,boot,clock=FakeClock())
    with pytest.raises(TaskError,match='RUNTIME_INACTIVE'):create(m)
    assert repo.read(lambda db:db.execute('SELECT count(*) FROM tm_tasks').fetchone()[0])==0
    queue.close();queue.join_thread()
