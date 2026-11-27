import json
import pytest
from aars_task_manager import TaskError
from tests.support import create,key

def test_list_pages_complete_and_sorted(system):
    m=system['manager'];ids={create(m,title='T'+str(i))['task_id'] for i in range(13)}
    cursor=None;seen=[]
    while True:
        page=m.list_tasks(limit=3,cursor=cursor)
        assert len(json.dumps(page,ensure_ascii=False).encode())<16384
        seen += [t['task_id'] for t in page['data']['tasks']]
        cursor=page['data']['next_cursor']
        if cursor is None:break
    assert seen==sorted(ids) and len(seen)==len(set(seen))

def test_list_enforces_byte_limit_without_invalid_json(system):
    m=system['manager'];ids={create(m,title='😀'*200)['task_id'] for _ in range(25)};seen=[];cursor=None;pages=0
    while True:
        r=m.list_tasks(limit=50,cursor=cursor);pages+=1
        assert len(json.dumps(r,ensure_ascii=False,separators=(',',':')).encode())<=16384
        seen.extend(t['task_id'] for t in r['data']['tasks']);cursor=r['data']['next_cursor']
        if not cursor:break
    assert set(seen)==ids and len(seen)==25 and pages>1

def test_tampered_cursor_rejected(system):
    m=system['manager'];create(m);create(m);cursor=m.list_tasks(limit=1)['data']['next_cursor']
    with pytest.raises(TaskError,match='CURSOR_EXPIRED'):m.list_tasks(limit=1,cursor=cursor[:-1]+('0' if cursor[-1]!='0' else '1'))

def test_cursor_bound_to_principal_and_filter(system):
    m=system['manager'];create(m);create(m);cursor=m.list_tasks(limit=1)['data']['next_cursor']
    with pytest.raises(TaskError,match='CURSOR_EXPIRED'):system['other'].list_tasks(limit=1,cursor=cursor)
    with pytest.raises(TaskError,match='CURSOR_EXPIRED'):m.list_tasks(limit=2,cursor=cursor)

def test_cursor_expires_on_workspace_generation_change(system):
    m=system['manager'];create(m);create(m);cursor=m.list_tasks(limit=1)['data']['next_cursor'];create(m)
    with pytest.raises(TaskError,match='CURSOR_EXPIRED'):m.list_tasks(limit=1,cursor=cursor)

def test_cursor_ttl_and_clock_rollback(system):
    m=system['manager'];create(m);create(m);cursor=m.list_tasks(limit=1)['data']['next_cursor'];system['clock'].advance(601)
    with pytest.raises(TaskError,match='CURSOR_EXPIRED'):m.list_tasks(limit=1,cursor=cursor)
    system['clock'].advance(-602)
    with pytest.raises(TaskError,match='CURSOR_EXPIRED'):m.list_tasks(limit=1,cursor=cursor)

def test_event_pages_have_no_gaps(system):
    m=system['manager'];t=create(m)
    for i in range(1,8):
        m.execute('update',{'task_id':t['task_id'],'expected_version':i,'idempotency_key':key(),'patch':{'title':'revision '+str(i)}})
    after=0;seen=[]
    while True:
        r=m.events(t['task_id'],after_seq=after,limit=3)['data'];seen += [e['seq'] for e in r['events']]
        if r['next_after_seq'] is None:break
        after=r['next_after_seq']
    assert seen==list(range(1,9))

@pytest.mark.parametrize('kwargs',[{'limit':True},{'limit':0},{'limit':51},{'state':[]},{'state':'APPROVED'},{'cursor':[]},{'cursor':'not-a-signed-cursor'}])
def test_invalid_list_inputs(system,kwargs):
    with pytest.raises(TaskError):system['manager'].list_tasks(**kwargs)

def test_event_sequence_bound(system):
    t=create(system['manager'])
    with pytest.raises(TaskError,match='INVALID_ARGUMENT'):system['manager'].events(t['task_id'],after_seq=2**64)
