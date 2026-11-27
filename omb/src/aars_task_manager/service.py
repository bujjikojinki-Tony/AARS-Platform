"""Internal application facade. No MCP endpoints and no operator approval provider."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import base64
import hashlib
import hmac
import json
from uuid import uuid4

from .domain import (Task, State, OPERATOR_ACTIONS, canonical, hash_json, new_id, parse_time,
                     request_shape, require_id, require_key, require_version, stamp, text)
from .errors import TaskError
from . import evidence

class Clock:
    def now(self):return datetime.now(timezone.utc)

class TaskManager:
    def __init__(self,repository,binding_id,boot_id,*,clock=None):
        self.repository=repository;self.binding_id=require_id(binding_id,'binding');self.boot_id=require_id(boot_id,'boot');self.clock=clock or Clock()

    def _principal(self,db,capability):
        if self.repository.meta(db,'active_boot')!=self.boot_id:raise TaskError('RUNTIME_INACTIVE')
        self.repository.assert_runtime(self.boot_id)
        p,caps=self.repository.principal(db,self.binding_id)
        if capability not in caps:raise TaskError('FORBIDDEN')
        return p

    def _now(self,task=None):
        now=stamp(self.clock.now())
        if task and parse_time(now)<parse_time(task.updated_at):raise TaskError('CLOCK_UNTRUSTED')
        return now

    @staticmethod
    def _view(task,attempt=None,link=None):
        return {'task':task.snapshot(),'attempt':attempt,'review':None,'link':link}

    @staticmethod
    def _envelope(data,*,replayed=False):
        result={'schema_version':'omb-task/1.0','ok':True,'request_id':new_id('request'),'replayed':replayed,'data':data,'execution_authorized':False}
        if len(canonical(result).encode('utf-8'))>16384:raise TaskError('RESPONSE_TOO_LARGE')
        return result

    def execute(self,operation,arguments):
        if not isinstance(operation,str):raise TaskError('INVALID_ARGUMENT')
        if operation in OPERATOR_ACTIONS:raise TaskError('APPROVAL_LOCKED')
        if operation == 'review_request':raise TaskError('PHASE_HOLD')
        if operation=='get':return self.get(**self._read_args(arguments,{'task_id'}))
        if operation=='list':
            request_shape(arguments,(),('state','limit','cursor'));return self.list_tasks(**arguments)
        if operation=='events':
            request_shape(arguments,('task_id',),('after_seq','limit'));return self.events(**arguments)
        if operation=='create':
            request_shape(arguments,('idempotency_key','title','description','purpose'))
            text(arguments['title'],200);text(arguments['description'],4000,empty=True)
            if not isinstance(arguments['purpose'],str) or arguments['purpose'] not in {'LOCAL_SYNTHETIC_VALIDATION','CATALOG_METADATA'}:raise TaskError('INVALID_ARGUMENT')
            capability='task.create';permission='READ'
        elif operation=='update':
            request_shape(arguments,('task_id','expected_version','idempotency_key','patch'));capability='task.update';permission='READ'
        elif operation in {'transition','renew','evidence_link'}:
            required=['task_id','expected_version','idempotency_key']
            if operation=='transition':required+=['action']
            else:required+=['attempt_id','fencing_token']
            if operation == 'evidence_link':required += ['snapshot_id']
            request_shape(arguments,required,('reason','attempt_id','fencing_token') if operation=='transition' else ())
            if operation=='transition':
                action=arguments['action']
                if not isinstance(action,str):raise TaskError('INVALID_ARGUMENT')
                if action in OPERATOR_ACTIONS:raise TaskError('APPROVAL_LOCKED')
                if action=='request_review':raise TaskError('PHASE_HOLD')
                if action not in {'start','pause','fail','cancel'}:raise TaskError('INVALID_TRANSITION')
                if action in {'pause','fail','cancel'}:text(arguments.get('reason'),2000)
                elif 'reason' in arguments:text(arguments['reason'],2000)
            if operation == 'evidence_link':evidence.require_snapshot_id(arguments['snapshot_id'])
            capability='evidence.link' if operation=='evidence_link' else 'task.work';permission='WORK'
        else:raise TaskError('UNKNOWN_COMMAND')
        key=require_key(arguments['idempotency_key'])
        if operation!='create':
            require_id(arguments['task_id'],'task');require_version(arguments['expected_version'])
        has_lease='attempt_id' in arguments or 'fencing_token' in arguments
        if has_lease:
            require_id(arguments.get('attempt_id'),'attempt');require_version(arguments.get('fencing_token'))
        request_hash=hash_json({'operation':operation,'binding_id':self.binding_id,'arguments':{k:v for k,v in arguments.items() if k!='idempotency_key'}})

        def change(db):
            p=self._principal(db,capability);ws=p['workspace_id'];pid=p['principal_id']
            task=None
            if operation=='evidence_link':
                _, caps = self.repository.principal(db,self.binding_id)
                if 'task.work' not in caps:raise TaskError('FORBIDDEN')
            if operation!='create':
                task=self.repository.task(db,arguments['task_id'],p,permission=permission)
                if (operation=='update' or (operation=='transition' and arguments['action']=='cancel')) and task.owner_principal_id!=pid:raise TaskError('NOT_FOUND_OR_FORBIDDEN')
            # Recheck current access before replaying any cached successful result.
            cached=db.execute('SELECT * FROM idempotency_records WHERE workspace_id=? AND principal_id=? AND idem_key=?',(ws,pid,key)).fetchone()
            if cached:
                if cached['request_hash']!=request_hash or cached['method']!=operation:raise TaskError('IDEMPOTENCY_CONFLICT')
                data=json.loads(cached['response_json'])
                if hash_json(data)!=cached['response_hash']:raise TaskError('INTEGRITY_FAILURE')
                if operation=='create':self.repository.task(db,data['task']['task_id'],p)
                if operation=='evidence_link' and not evidence.grant_usable(db, evidence.verified_graph(db,ws), self._now(task)):
                    raise TaskError('EVIDENCE_UNUSABLE')
                return self._envelope(data,replayed=True)
            if task and task.version!=arguments['expected_version']:raise TaskError('VERSION_CONFLICT')
            now=self._now(task)
            link=None
            if operation=='create':
                result=Task(task_id=new_id('task'),workspace_id=ws,owner_principal_id=pid,title=arguments['title'],description=arguments['description'],purpose=arguments['purpose'],state=State.DRAFT,version=1,definition_revision=1,created_at=now,updated_at=now)
                self.repository.save(db,None,result,actor=pid,event_type='CREATED',now=now,request_hash=request_hash)
            elif operation=='update':
                result=task.edit(arguments['patch'],now)
                self.repository.save(db,task,result,actor=pid,event_type='UPDATED',now=now,request_hash=request_hash)
            elif operation=='evidence_link':
                if task.purpose != 'LOCAL_SYNTHETIC_VALIDATION':raise TaskError('PURPOSE_NOT_EXECUTABLE')
                if task.state != State.RUNNING:raise TaskError('INVALID_TRANSITION')
                self._lease(db,task,p,arguments,now)
                link=evidence.append_link(db,task,snapshot_id=arguments['snapshot_id'],now=now)
                result=replace(task,version=task.version+1,updated_at=now)
                self.repository.save(db,task,result,actor=pid,event_type='EVIDENCE_LINKED',now=now,
                    request_hash=request_hash,related_ids=(link['link_id'],link['snapshot_id']))
            elif operation=='renew':
                # Operator plan verification belongs to 003D; there is no production bypass hook.
                if task.state!=State.RUNNING:raise TaskError('INVALID_TRANSITION')
                self._lease(db,task,p,arguments,now)
                raise TaskError('APPROVAL_LOCKED')
            else:
                action=arguments['action']
                if action=='start' and has_lease:raise TaskError('INVALID_ARGUMENT')
                if task.state==State.RUNNING and action in {'pause','fail','cancel'}:
                    self._lease(db,task,p,arguments,now)
                elif has_lease:raise TaskError('INVALID_ARGUMENT')
                result=task.transition(action,now)
                if task.state==State.RUNNING:
                    db.execute("UPDATE attempts SET status=?,finished_at=? WHERE workspace_id=? AND task_id=? AND status IN ('ACQUIRED','RUNNING')",({'pause':'PAUSED','fail':'FAILED','cancel':'CANCELLED'}[action],now,ws,task.task_id))
                self.repository.save(db,task,result,actor=pid,event_type={'pause':'PAUSED','fail':'FAILED','cancel':'CANCELLED'}[action],now=now,request_hash=request_hash,reason=arguments.get('reason'))
            data=self._view(result,link=link)
            response=self._envelope(data)
            db.execute('INSERT INTO idempotency_records VALUES (?,?,?,?,?,?,?,?)',(ws,pid,key,operation,request_hash,canonical(data),hash_json(data),result.version))
            return response
        return self.repository.write(change)

    @staticmethod
    def _read_args(arguments,required):
        request_shape(arguments,required);return arguments

    def _lease(self,db,task,p,args,now):
        require_id(args.get('attempt_id'),'attempt');require_version(args.get('fencing_token'))
        attempt=db.execute("SELECT * FROM attempts WHERE workspace_id=? AND task_id=? AND status IN ('ACQUIRED','RUNNING')",(task.workspace_id,task.task_id)).fetchone()
        if attempt is None or attempt['attempt_id']!=args['attempt_id'] or attempt['fencing_token']!=args['fencing_token'] or attempt['actor_principal_id']!=p['principal_id'] or attempt['boot_id']!=self.boot_id:raise TaskError('FENCING_CONFLICT')
        if parse_time(attempt['lease_expires_at'])<=parse_time(now):raise TaskError('LEASE_EXPIRED')
        return attempt

    def get(self,task_id):
        require_id(task_id,'task')
        def read(db):
            p=self._principal(db,'task.read');task=self.repository.task(db,task_id,p)
            return self._envelope(self._view(task))
        return self.repository.read(read)

    def list_tasks(self,*,state=None,limit=50,cursor=None):
        if state is not None and (not isinstance(state,str) or state not in {s.value for s in State}):raise TaskError('INVALID_ARGUMENT')
        if type(limit) is not int or not 1<=limit<=50:raise TaskError('INVALID_ARGUMENT')
        if cursor is not None and (not isinstance(cursor,str) or len(cursor)>2048):raise TaskError('INVALID_ARGUMENT')
        def read(db):
            p=self._principal(db,'task.read');ws=p['workspace_id'];pid=p['principal_id'];now=self.clock.now().timestamp()
            generation=db.execute('SELECT generation FROM workspaces WHERE workspace_id=?',(ws,)).fetchone()[0]
            try:secret=bytes.fromhex(self.repository.meta(db,'cursor_key'))
            except ValueError:raise TaskError('INTEGRITY_FAILURE') from None
            if len(secret)!=32:raise TaskError('INTEGRITY_FAILURE')
            last='';filter_hash=hash_json({'state':state,'limit':limit})
            if cursor:
                try:
                    payload,sig=cursor.split('.')
                    expected=hmac.new(secret,payload.encode(),hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(sig,expected):raise ValueError()
                    c=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
                    if c['workspace']!=ws or c['principal']!=pid or c['filter']!=filter_hash or c['generation']!=generation or c['expires']<=now or c['issued']>now:raise ValueError()
                    last=require_id(c['last'],'task')
                except (ValueError,KeyError,TypeError):raise TaskError('CURSOR_EXPIRED') from None
            params=[ws,pid,pid,last]
            sql="SELECT t.* FROM tm_tasks t WHERE t.workspace_id=? AND (t.owner_principal_id=? OR EXISTS(SELECT 1 FROM task_acl a WHERE a.workspace_id=t.workspace_id AND a.task_id=t.task_id AND a.principal_id=? AND a.permission='READ' AND a.active=1)) AND t.task_id>?"
            if state is not None:sql+=' AND t.state=?';params.append(state)
            rows=db.execute(sql+' ORDER BY t.task_id LIMIT ?',(*params,limit+1)).fetchall()
            summaries=[];more=False
            for row in rows:
                if len(summaries)>=limit:more=True;break
                task=self.repository.verify_task(db,row).snapshot()
                summary={k:task[k] for k in ('task_id','workspace_id','title','state','version','updated_at','usage_state')}
                # Reserve room for the signed cursor and the fixed envelope.
                if len(canonical({'tasks':summaries+[summary]}).encode('utf-8'))>14500:more=True;break
                summaries.append(summary)
            nxt=None
            if more:
                if not summaries:raise TaskError('RESPONSE_TOO_LARGE')
                c={'workspace':ws,'principal':pid,'filter':filter_hash,'generation':generation,'last':summaries[-1]['task_id'],'issued':now,'expires':now+600}
                payload=base64.urlsafe_b64encode(canonical(c).encode()).decode().rstrip('=')
                nxt=payload+'.'+hmac.new(secret,payload.encode(),hashlib.sha256).hexdigest()
            return self._envelope({'tasks':summaries,'next_cursor':nxt})
        return self.repository.read(read)

    def events(self,task_id,*,after_seq=0,limit=50):
        require_id(task_id,'task')
        if type(after_seq) is not int or not 0<=after_seq<=2**63-1 or type(limit) is not int or not 1<=limit<=50:raise TaskError('INVALID_ARGUMENT')
        def read(db):
            p=self._principal(db,'task.read');self.repository.task(db,task_id,p)
            rows=db.execute('SELECT event_json FROM task_events WHERE workspace_id=? AND task_id=? AND seq>? ORDER BY seq LIMIT ?',(p['workspace_id'],task_id,after_seq,limit+1)).fetchall()
            result=[];more=False
            for row in rows:
                if len(result)>=limit:more=True;break
                e=json.loads(row[0]);summary={k:e[k] for k in ('event_id','task_id','seq','event_type','at','from_version','to_version','payload_hash','prev_hash','event_hash')}
                if len(canonical({'events':result+[summary]}).encode('utf-8'))>15000:more=True;break
                result.append(summary)
            return self._envelope({'events':result,'next_after_seq':result[-1]['seq'] if more and result else None})
        return self.repository.read(read)

    def evidence_trace(self, task_id):
        """Read-only projection of evidence revisions and the verified event chain."""
        require_id(task_id, 'task')
        def read(db):
            principal = self._principal(db, 'task.read')
            task = self.repository.task(db, task_id, principal)
            return evidence.trace(db, task, self._now(task))
        return self.repository.read(read)
