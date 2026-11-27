from pathlib import Path
import pytest
from aars_task_manager import Repository,Binding,TaskRuntime
from aars_task_manager.domain import new_id,stamp
from tests.support import FakeClock

@pytest.fixture
def system(tmp_path):
    root=tmp_path/'runtime';root.mkdir(mode=0o700)
    protected=tmp_path/'frozen';protected.mkdir(mode=0o700)
    clock=FakeClock()
    evidence_caps=('task.create','task.read','task.update','task.work','evidence.link','review.request')
    bindings=[Binding(new_id('binding'),new_id('principal'),evidence_caps),Binding(new_id('binding'),new_id('principal'),evidence_caps),Binding(new_id('binding'),new_id('principal'),('task.read',))]
    repo=Repository.create(root/'tasks.sqlite',allowed_root=root,protected_roots=(protected,),workspace_id=new_id('workspace'),bindings=bindings,created_at=stamp(clock.now()))
    with TaskRuntime(repo,clock=clock) as runtime:
        yield {'repo':repo,'runtime':runtime,'manager':runtime.manager(bindings[0].binding_id),'other':runtime.manager(bindings[1].binding_id),'reader':runtime.manager(bindings[2].binding_id),'bindings':bindings,'clock':clock,'root':root,'protected':protected}
