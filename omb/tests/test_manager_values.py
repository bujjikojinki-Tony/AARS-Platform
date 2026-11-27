import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator,FormatChecker
from aars_task_manager import TaskError,State
from aars_task_manager.domain import OPERATOR_ACTIONS
from aars_core.domain.common import ObjectType
from tests.support import create,key

def test_create_snapshot_matches_reviewed_schema(system):
    t=create(system['manager'])
    schema=json.loads(Path('design/omb003a/TASK_MANAGER_SCHEMA.json').read_text())
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(t)
    assert t['state']=='DRAFT' and t['version']==1 and t['usage_state']=='REVIEW_REQUIRED'
    assert t['scope']['external_execution_allowed'] is False
    assert len(ObjectType)==9 and 'task' not in {x.value for x in ObjectType}

@pytest.mark.parametrize('field,value',[('title',''),('title',' '*5),('title','x'*201),('title',None),('title','\ud800'),('description',None),('description','x'*4001),('purpose','PRODUCTION'),('purpose',[]),('purpose',True)])
def test_invalid_create_no_rows(system,field,value):
    with pytest.raises(TaskError):create(system['manager'],**{field:value})
    assert system['manager'].list_tasks()['data']['tasks']==[]

@pytest.mark.parametrize('extra',['actor_id','bot_id','approved','db_path','owner_principal_id','state','license_pass'])
def test_identity_and_authority_fields_rejected(system,extra):
    with pytest.raises(TaskError,match='INVALID_ARGUMENT'):create(system['manager'],**{extra:'injected'})

@pytest.mark.parametrize('version',[True,False,0,-1,1.0,'1',None,2**63])
def test_strict_versions(system,version):
    t=create(system['manager'])
    with pytest.raises(TaskError,match='INVALID_ARGUMENT'):system['manager'].execute('update',{'task_id':t['task_id'],'expected_version':version,'idempotency_key':key(),'patch':{'title':'new'}})
    assert system['manager'].get(t['task_id'])['data']['task']['version']==1

@pytest.mark.parametrize('patch',[{}, {'state':'COMPLETED'},{'priority':True},{'priority':6},{'due_at':'2026-11-26T00:00:00'}, {'title':' '},[],None])
def test_invalid_patch_rollback(system,patch):
    t=create(system['manager'])
    with pytest.raises(TaskError):system['manager'].execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'patch':patch})
    assert system['manager'].get(t['task_id'])['data']['task']==t

def test_definition_and_task_versions(system):
    m=system['manager'];t=create(m);system['clock'].advance(1)
    r=m.execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'patch':{'title':'Changed','priority':5,'due_at':'2025-01-01T00:00:00Z'}})['data']['task']
    assert r['version']==2 and r['definition_revision']==2 and r['definition_hash']!=t['definition_hash']
    assert r['state']=='DRAFT' and r['created_at']==t['created_at']
    c=m.execute('transition',{'task_id':t['task_id'],'expected_version':2,'idempotency_key':key(),'action':'cancel','reason':'scope fixture'})['data']['task']
    assert c['version']==3 and c['definition_revision']==2 and c['definition_hash']==r['definition_hash']

def test_no_change_does_not_add_event(system):
    m=system['manager'];t=create(m)
    with pytest.raises(TaskError,match='NO_CHANGE'):m.execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'patch':{'title':t['title']}})
    assert len(m.events(t['task_id'])['data']['events'])==1

def test_clock_rollback_rejected(system):
    m=system['manager'];t=create(m);system['clock'].advance(-1)
    with pytest.raises(TaskError,match='CLOCK_UNTRUSTED'):m.execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'patch':{'title':'clock'}})
    assert m.get(t['task_id'])['data']['task']==t

def test_request_size_rejected_before_write(system):
    with pytest.raises(TaskError,match='REQUEST_TOO_LARGE'):create(system['manager'],description='😀'*4000,title='😀'*200)

def test_oversized_response_rolls_back(system):
    m=system['manager']
    with pytest.raises(TaskError,match='RESPONSE_TOO_LARGE'):create(m,description='😀'*3900)
    assert m.list_tasks()['data']['tasks']==[]

def test_catalog_task_stays_draft(system):
    m=system['manager'];t=create(m,purpose='CATALOG_METADATA')
    assert t['scope']['data_mode']=='CATALOG_METADATA'
    with pytest.raises(TaskError):m.execute('transition',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'action':'start'})
    assert m.get(t['task_id'])['data']['task']['state']=='DRAFT'

@pytest.mark.parametrize('action',sorted(OPERATOR_ACTIONS))
def test_operator_actions_locked_for_every_entry(system,action):
    m=system['manager'];t=create(m)
    with pytest.raises(TaskError,match='APPROVAL_LOCKED'):m.execute(action,{'approved':True})
    with pytest.raises(TaskError,match='APPROVAL_LOCKED'):m.execute('transition',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'action':action})
    assert m.get(t['task_id'])['data']['task']==t

def test_review_request_requires_complete_request(system):
    with pytest.raises(TaskError,match='INVALID_ARGUMENT'):system['manager'].execute('review_request',{})

def test_exhaustive_b_stage_transition_denials(system):
    from dataclasses import replace
    from aars_task_manager.domain import Task,stamp,BOT_TRANSITIONS
    base=Task.from_snapshot(create(system['manager']))
    actions={'start','pause','fail','cancel','request_review','complete','set_state','reopen'}|set(OPERATOR_ACTIONS)
    for state in State:
        task=replace(base,state=state,version=2)
        for action in actions:
            if (state,action) in BOT_TRANSITIONS:
                result=task.transition(action,stamp(system['clock'].now()))
                assert result.state==BOT_TRANSITIONS[state,action] and result.version==3
            else:
                with pytest.raises(TaskError):task.transition(action,stamp(system['clock'].now()))

def test_nan_never_reaches_storage(system):
    t=create(system['manager'])
    with pytest.raises(TaskError,match='INVALID_ARGUMENT'):system['manager'].execute('update',{'task_id':t['task_id'],'expected_version':1,'idempotency_key':key(),'patch':{'priority':float('nan')}})
