"""Controlled test preconditions only; never packaged into a runtime launcher."""
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from uuid import uuid4
from pathlib import Path
import os
from aars_task_manager import Repository,TaskManager,TaskRuntime,State
from aars_task_manager.domain import new_id,stamp,hash_json

class FakeClock:
    def __init__(self):self.value=datetime(2026,11,26,tzinfo=timezone.utc)
    def now(self):return self.value
    def advance(self,seconds):self.value+=timedelta(seconds=seconds)

def key():return str(uuid4())
def create(manager,**kwargs):
    return manager.execute('create',{'idempotency_key':key(),'title':'Synthetic task fixture','description':'Management test only','purpose':'LOCAL_SYNTHETIC_VALIDATION',**kwargs})['data']['task']

def seed_precondition(repo,manager,state,clock,*,fencing=1,expires=60):
    """Insert a labelled fixture through private repository primitives, NOT an approval API."""
    t=create(manager)
    def seed(db):
        p,_=repo.principal(db,manager.binding_id);old=repo.task(db,t['task_id'],p)
        now=stamp(clock.now());new=replace(old,state=state,version=old.version+1,updated_at=now)
        attempt=None
        if state==State.RUNNING:
            attempt={'attempt_id':new_id('attempt'),'attempt_no':1,'fencing_token':fencing,'actor_principal_id':p['principal_id'],'boot_id':manager.boot_id,'lease_expires_at':stamp(clock.now()+timedelta(seconds=expires))}
            db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?,?)',(old.workspace_id,old.task_id,attempt['attempt_id'],1,fencing,p['principal_id'],'RUNNING',manager.boot_id,attempt['lease_expires_at'],now,None))
        repo.save(db,old,new,actor=repo.meta(db,'service_principal'),event_type='TEST_PRECONDITION',now=now,request_hash=hash_json({'fixture':state.value}),reason='UNIT FIXTURE; not actual approval or execution')
        return new.snapshot(),attempt
    return repo.write(seed)

def process_create(path,root,protected,binding,boot,idem):
    repo=Repository.open(Path(path),allowed_root=Path(root),protected_roots=(Path(protected),))
    m=TaskManager(repo,binding,boot,clock=FakeClock())
    return m.execute('create',{'idempotency_key':idem,'title':'Cross-process fixture','description':'','purpose':'LOCAL_SYNTHETIC_VALIDATION'})

def crash_runtime(path,root,protected,binding):
    repo=Repository.open(Path(path),allowed_root=Path(root),protected_roots=(Path(protected),))
    clock=FakeClock()
    with TaskRuntime(repo,clock=clock) as runtime:
        m=runtime.manager(binding)
        seed_precondition(repo,m,State.RUNNING,clock)
        os._exit(0)


def process_try_runtime(path,root,protected):
    from aars_task_manager import TaskError
    repo=Repository.open(Path(path),allowed_root=Path(root),protected_roots=(Path(protected),))
    try:
        with TaskRuntime(repo,clock=FakeClock()):return 'UNEXPECTED_SUCCESS'
    except TaskError as exc:return exc.code


def orphaned_runtime(path,root,protected,binding,queue):
    repo=Repository.open(Path(path),allowed_root=Path(root),protected_roots=(Path(protected),))
    with TaskRuntime(repo,clock=FakeClock()) as runtime:
        queue.put(runtime.boot_id)
        queue.close();queue.join_thread()
        os._exit(0)
