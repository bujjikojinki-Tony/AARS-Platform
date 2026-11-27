"""Management values only; Task is deliberately not a Core ObjectType."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
import re
from uuid import uuid4

# Reuse the byte format actually frozen in OMB-002-FIX, without changing it.
from aars_omb.store import canonical, digest
from aars_core.domain.common import ObjectType
from .errors import TaskError

ZERO_HASH = 'sha256:' + '0' * 64
PURPOSES = frozenset({'LOCAL_SYNTHETIC_VALIDATION', 'CATALOG_METADATA'})
OPERATOR_ACTIONS = frozenset({'approve_plan','approve_result','reject_result','request_changes',
    'resume_authorize','return_to_draft','assign_worker','revoke_worker','prepare_challenge','submit_receipt'})

class State(StrEnum):
    DRAFT='DRAFT'
    READY='READY'
    RUNNING='RUNNING'
    PAUSED='PAUSED'
    REVIEW_PENDING='REVIEW_PENDING'
    COMPLETED='COMPLETED'
    REJECTED='REJECTED'
    FAILED='FAILED'
    CANCELLED='CANCELLED'

TERMINAL = frozenset({State.COMPLETED,State.REJECTED,State.FAILED,State.CANCELLED})
BOT_TRANSITIONS = {(State.DRAFT,'cancel'):State.CANCELLED,(State.READY,'cancel'):State.CANCELLED,
    (State.PAUSED,'cancel'):State.CANCELLED,(State.RUNNING,'pause'):State.PAUSED,
    (State.RUNNING,'fail'):State.FAILED,(State.RUNNING,'cancel'):State.CANCELLED}

def new_id(prefix): return prefix + '.' + uuid4().hex

def require_id(value, prefix):
    if not isinstance(value,str) or not re.fullmatch(re.escape(prefix)+r'\.[0-9a-f]{32}',value):
        raise TaskError('INVALID_ARGUMENT')
    return value

def require_version(value):
    if type(value) is not int or not 1 <= value < 2**63-1: raise TaskError('INVALID_ARGUMENT')
    return value

def require_key(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',value):
        raise TaskError('INVALID_ARGUMENT')
    return value

def text(value, maximum, *, empty=False):
    if not isinstance(value,str) or len(value)>maximum or ('\x00' in value) or (not empty and not value.strip()):
        raise TaskError('INVALID_ARGUMENT')
    try: value.encode('utf-8')
    except UnicodeError: raise TaskError('INVALID_ARGUMENT') from None
    return value

def parse_time(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z',value):
        raise TaskError('INVALID_ARGUMENT')
    try: return datetime.fromisoformat(value[:-1]+'+00:00')
    except ValueError: raise TaskError('INVALID_ARGUMENT') from None

def stamp(value: datetime):
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise TaskError('CLOCK_UNTRUSTED')
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')

def hash_json(value): return 'sha256:'+digest(canonical(value))

def request_shape(arguments, required, optional=()):
    if not isinstance(arguments,dict) or set(arguments)-set(required)-set(optional) or not set(required)<=set(arguments):
        raise TaskError('INVALID_ARGUMENT')
    try:
        if len(canonical(arguments).encode('utf-8'))>16384: raise TaskError('REQUEST_TOO_LARGE')
    except (TypeError,ValueError,UnicodeError) as exc:
        if isinstance(exc,TaskError): raise
        raise TaskError('INVALID_ARGUMENT') from None

@dataclass(frozen=True)
class Task:
    task_id: str
    workspace_id: str
    owner_principal_id: str
    title: str
    description: str
    purpose: str
    state: State
    version: int
    definition_revision: int
    created_at: str
    updated_at: str
    priority: int=3
    due_at: str|None=None
    supersedes_task_id: str|None=None
    usage_state: str='REVIEW_REQUIRED'

    def __post_init__(self):
        require_id(self.task_id,'task');require_id(self.workspace_id,'workspace');require_id(self.owner_principal_id,'principal')
        text(self.title,200);text(self.description,4000,empty=True)
        if self.purpose not in PURPOSES or not isinstance(self.state,State): raise TaskError('INVALID_ARGUMENT')
        require_version(self.version);require_version(self.definition_revision)
        if type(self.priority) is not int or not 0<=self.priority<=5: raise TaskError('INVALID_ARGUMENT')
        if self.usage_state not in {'USABLE','REVIEW_REQUIRED','UNUSABLE'}: raise TaskError('INVALID_ARGUMENT')
        if parse_time(self.updated_at)<parse_time(self.created_at): raise TaskError('CLOCK_UNTRUSTED')
        if self.due_at is not None:parse_time(self.due_at)
        if self.supersedes_task_id is not None:require_id(self.supersedes_task_id,'task')

    @property
    def scope(self):
        return {'workspace_id':self.workspace_id,'data_mode':'SYNTHETIC_ONLY' if self.purpose=='LOCAL_SYNTHETIC_VALIDATION' else 'CATALOG_METADATA','external_execution_allowed':False}

    @property
    def definition_hash(self):
        return hash_json({k:self.to_dict()[k] for k in ('title','description','purpose','owner_principal_id','priority','due_at','scope')})

    def to_dict(self):
        d={k:getattr(self,k) for k in self.__dataclass_fields__}
        d['state']=self.state.value;d['scope']=self.scope
        return d

    def snapshot(self):
        return {**self.to_dict(),'definition_hash':self.definition_hash}

    @classmethod
    def from_snapshot(cls, data):
        if not isinstance(data,dict):raise TaskError('INTEGRITY_FAILURE')
        try:
            fields={k:data[k] for k in cls.__dataclass_fields__};fields['state']=State(fields['state']);t=cls(**fields)
            if data != t.snapshot():raise TaskError('INTEGRITY_FAILURE')
            return t
        except (KeyError,TypeError,ValueError):raise TaskError('INTEGRITY_FAILURE') from None

    def edit(self,patch,now):
        if self.state!=State.DRAFT:raise TaskError('INVALID_TRANSITION')
        if not isinstance(patch,dict) or not patch or set(patch)-{'title','description','priority','due_at'}:raise TaskError('INVALID_ARGUMENT')
        if all(getattr(self,k)==v and type(getattr(self,k)) is type(v) for k,v in patch.items()):raise TaskError('NO_CHANGE')
        return replace(self,**patch,version=self.version+1,definition_revision=self.definition_revision+1,updated_at=now)

    def transition(self,action,now):
        if action in OPERATOR_ACTIONS:raise TaskError('APPROVAL_LOCKED')
        if action=='request_review':raise TaskError('PHASE_HOLD')
        if action=='start':
            if self.purpose!='LOCAL_SYNTHETIC_VALIDATION':raise TaskError('PURPOSE_NOT_EXECUTABLE')
            if self.state!=State.READY:raise TaskError('INVALID_TRANSITION')
            # No plan-verification provider is installed in 003B. Never accept a boolean approval.
            raise TaskError('APPROVAL_LOCKED')
        target=BOT_TRANSITIONS.get((self.state,action))
        if target is None:raise TaskError('INVALID_TRANSITION')
        return replace(self,state=target,version=self.version+1,updated_at=now)

    def interrupted(self,now):
        if self.state not in {State.RUNNING,State.REVIEW_PENDING}:return None
        return replace(self,state=State.PAUSED,version=self.version+1,updated_at=now,usage_state='REVIEW_REQUIRED')

# Importing Task Manager must not add a tenth business object to Core.
assert len(ObjectType)==9
