"""Repeatable isolated-development demonstration. Does not connect to any Bot."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import json
import os
from uuid import uuid4
from aars_task_manager import Repository,Binding,TaskRuntime,TaskError
from aars_task_manager.domain import new_id,stamp

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-root',type=Path,default=ROOT/'.devdata/demo');args=parser.parse_args()
    baseline=json.loads((ROOT/'frozen_payload/RUNTIME_BINDING.json').read_text())
    protected=(Path(baseline['source_path']).parents[1],Path(baseline['database_path']),ROOT/'frozen_payload',ROOT/'frozen_archive')
    data=args.data_root.absolute()
    safe=(ROOT/'.devdata').resolve()
    resolved=data.resolve()
    if resolved!=safe and safe not in resolved.parents:raise TaskError('INVALID_STORAGE_ROOT')
    if resolved!=data:raise TaskError('INVALID_STORAGE_ROOT')
    for p in protected:
        if resolved==p.resolve() or p.resolve() in resolved.parents:raise TaskError('PROTECTED_BASELINE_PATH')
    data.mkdir(parents=True,exist_ok=True,mode=0o700)
    if data.stat().st_mode & 0o077:raise TaskError('UNSAFE_PERMISSIONS')
    config_path=data/'development-config.json'
    if not config_path.exists():
        config={'workspace_id':new_id('workspace'),'binding_id':new_id('binding'),'principal_id':new_id('principal'),'create_key':str(uuid4()),'update_key':str(uuid4())}
        fd=os.open(config_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as f:json.dump(config,f)
    fd=os.open(config_path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'r') as f:
        if os.fstat(f.fileno()).st_mode & 0o077:raise TaskError('UNSAFE_FILE')
        config=json.load(f)
    if set(config)!={'workspace_id','binding_id','principal_id','create_key','update_key'}:raise TaskError('INVALID_ARGUMENT')
    path=data/'tasks.sqlite'
    if path.exists():repo=Repository.open(path,allowed_root=data,protected_roots=protected)
    else:repo=Repository.create(path,allowed_root=data,protected_roots=protected,workspace_id=config['workspace_id'],bindings=[Binding(config['binding_id'],config['principal_id'])],created_at=stamp(datetime.now(timezone.utc)))
    report={'scope':'Isolated OMB-003B development demonstration; NOT OpenMausBot/Magpie deployment','calls':[],'execution_authorized':False}
    with TaskRuntime(repo) as runtime:
        m=runtime.manager(config['binding_id'])
        c=m.execute('create',{'idempotency_key':config['create_key'],'title':'OMB-003B development task','description':'Local management record; no observation or research conclusion','purpose':'LOCAL_SYNTHETIC_VALIDATION'})
        tid=c['data']['task']['task_id'];report['calls'].append({'operation':'create','response':c})
        u=m.execute('update',{'task_id':tid,'expected_version':1,'idempotency_key':config['update_key'],'patch':{'title':'Verified isolated development persistence'}})
        report['calls'].append({'operation':'update','response':u})
        for operation,arguments in [('update',{'task_id':tid,'expected_version':1,'idempotency_key':str(uuid4()),'patch':{'title':'stale request'}}),('approve_result',{'task_id':tid,'approved':True})]:
            try:m.execute(operation,arguments);raise AssertionError('Expected rejection')
            except TaskError as exc:report['calls'].append({'operation':operation,'rejection':exc.to_dict()})
        before=m.get(tid)['data']['task']
    with TaskRuntime(Repository.open(path,allowed_root=data,protected_roots=protected)) as runtime:
        after=runtime.manager(config['binding_id']).get(tid)['data']['task']
    assert before==after and after['version']==2 and after['state']=='DRAFT'
    report['restart_records_identical']=before==after;report['task']=after;report['integrity_check']=repo.check_integrity()
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
