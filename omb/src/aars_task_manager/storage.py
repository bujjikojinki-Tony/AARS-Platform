"""Private SQLite unit of work. No connection to the frozen evidence database."""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import json
import fcntl
import os
import random
import sqlite3
import stat
import time

from .domain import Task, canonical, hash_json, new_id, require_id, text, ZERO_HASH, parse_time
from .errors import TaskError
from . import evidence, reviews

APPLICATION_ID = 0x4F4D4233
SCHEMA_VERSION = 3
CAPABILITIES = frozenset({'task.create','task.read','task.update','task.work','evidence.link','review.request'})
SCHEMA = '''
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE workspaces(workspace_id TEXT PRIMARY KEY,db_instance_id TEXT NOT NULL UNIQUE,mode TEXT NOT NULL CHECK(mode='LOCAL_SYNTHETIC'),policy_version INTEGER NOT NULL CHECK(policy_version>=1),generation INTEGER NOT NULL CHECK(generation>=0),created_at TEXT NOT NULL);
CREATE TABLE principals(workspace_id TEXT NOT NULL,principal_id TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind IN ('BOT','SERVICE')),binding_id TEXT NOT NULL,binding_version INTEGER NOT NULL CHECK(binding_version>=1),active INTEGER NOT NULL CHECK(active IN (0,1)),capabilities_json TEXT NOT NULL CHECK(json_valid(capabilities_json)),PRIMARY KEY(workspace_id,principal_id),UNIQUE(workspace_id,binding_id),FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id));
CREATE TABLE tm_tasks(workspace_id TEXT NOT NULL,task_id TEXT NOT NULL,owner_principal_id TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('DRAFT','READY','RUNNING','PAUSED','REVIEW_PENDING','COMPLETED','REJECTED','FAILED','CANCELLED')),version INTEGER NOT NULL CHECK(version>=1),snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json)),snapshot_hash TEXT NOT NULL,PRIMARY KEY(workspace_id,task_id),FOREIGN KEY(workspace_id,owner_principal_id) REFERENCES principals(workspace_id,principal_id));
CREATE TABLE task_events(workspace_id TEXT NOT NULL,task_id TEXT NOT NULL,seq INTEGER NOT NULL CHECK(seq>=1),event_id TEXT NOT NULL UNIQUE,event_json TEXT NOT NULL CHECK(json_valid(event_json)),event_hash TEXT NOT NULL,PRIMARY KEY(workspace_id,task_id,seq),FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id));
CREATE TABLE task_revisions(workspace_id TEXT NOT NULL,task_id TEXT NOT NULL,version INTEGER NOT NULL CHECK(version>=1),event_id TEXT NOT NULL REFERENCES task_events(event_id),snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json)),snapshot_hash TEXT NOT NULL,PRIMARY KEY(workspace_id,task_id,version),FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id));
CREATE TABLE attempts(workspace_id TEXT NOT NULL,task_id TEXT NOT NULL,attempt_id TEXT NOT NULL UNIQUE,attempt_no INTEGER NOT NULL CHECK(attempt_no>=1),fencing_token INTEGER NOT NULL CHECK(fencing_token>=1),actor_principal_id TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('ACQUIRED','RUNNING','SUBMITTED','PAUSED','FAILED','EXPIRED','CANCELLED')),boot_id TEXT NOT NULL,lease_expires_at TEXT NOT NULL,started_at TEXT NOT NULL,finished_at TEXT,PRIMARY KEY(workspace_id,task_id,attempt_no),UNIQUE(workspace_id,task_id,fencing_token),FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),FOREIGN KEY(workspace_id,actor_principal_id) REFERENCES principals(workspace_id,principal_id));
CREATE UNIQUE INDEX one_live_attempt ON attempts(workspace_id,task_id) WHERE status IN ('ACQUIRED','RUNNING');
CREATE TABLE task_acl(workspace_id TEXT NOT NULL,task_id TEXT NOT NULL,principal_id TEXT NOT NULL,permission TEXT NOT NULL CHECK(permission IN ('READ','PROPOSE','WORK')),active INTEGER NOT NULL CHECK(active IN (0,1)),PRIMARY KEY(workspace_id,task_id,principal_id,permission),FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),FOREIGN KEY(workspace_id,principal_id) REFERENCES principals(workspace_id,principal_id));
CREATE TABLE idempotency_records(workspace_id TEXT NOT NULL,principal_id TEXT NOT NULL,idem_key TEXT NOT NULL,method TEXT NOT NULL,request_hash TEXT NOT NULL,response_json TEXT NOT NULL CHECK(json_valid(response_json)),response_hash TEXT NOT NULL,result_version INTEGER NOT NULL,PRIMARY KEY(workspace_id,principal_id,idem_key),FOREIGN KEY(workspace_id,principal_id) REFERENCES principals(workspace_id,principal_id));
CREATE INDEX task_owner_state ON tm_tasks(workspace_id,owner_principal_id,state,task_id);
'''

def schema_hash(db):
    rows=db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
    return hash_json([tuple(r) for r in rows])

@lru_cache(maxsize=3)
def expected_schema_hash(version=SCHEMA_VERSION):
    with closing(sqlite3.connect(':memory:')) as db:
        db.executescript(SCHEMA + (evidence.SCHEMA if version >= 2 else '') + (reviews.SCHEMA if version >= 3 else ''))
        return schema_hash(db)

@dataclass(frozen=True)
class Binding:
    binding_id: str
    principal_id: str
    capabilities: tuple[str,...]=('task.create','task.read','task.update','task.work')

    def __post_init__(self):
        require_id(self.binding_id,'binding');require_id(self.principal_id,'principal')
        if not isinstance(self.capabilities,tuple) or len(set(self.capabilities))!=len(self.capabilities) or any(c not in CAPABILITIES for c in self.capabilities):
            raise TaskError('INVALID_ARGUMENT')

class Repository:
    """All configuration is supplied by the embedding operator, never by a task request."""
    def __init__(self,path: Path,*,allowed_root: Path,protected_roots: tuple[Path,...]):
        self.path=Path(path);self.root=Path(allowed_root);self.protected_roots=tuple(map(Path,protected_roots));self._quarantined=False
        self._check_path()

    @property
    def quarantined(self):
        return self._quarantined or os.path.lexists(self.root/'.task-quarantine')

    def _mark_quarantine(self):
        self._quarantined=True
        try:
            fd=os.open(self.root/'.task-quarantine',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            try:os.write(fd,b'INTEGRITY_FAILURE\n');os.fsync(fd)
            finally:os.close(fd)
        except OSError:
            # Keep this process fail-closed even if the marker cannot be written.
            pass

    def _check_path(self):
        if not self.path.is_absolute() or not self.root.is_absolute() or self.path.parent!=self.root or not self.protected_roots:
            raise TaskError('INVALID_STORAGE_ROOT')
        if self.path.suffix!='.sqlite' or self.path.name.startswith('.') or any(c in self.path.name for c in '?/#\\'):
            raise TaskError('INVALID_STORAGE_ROOT')
        if self.root.resolve(strict=True)!=self.root or not self.root.is_dir():raise TaskError('INVALID_STORAGE_ROOT')
        info=self.root.stat()
        if info.st_uid!=os.getuid() or info.st_mode & 0o077:raise TaskError('UNSAFE_PERMISSIONS')
        for protected in self.protected_roots:
            p=protected.resolve()
            if self.path==p or p in self.path.parents:raise TaskError('PROTECTED_BASELINE_PATH')
            if self.path.exists() and p.exists() and os.path.samefile(self.path,p):raise TaskError('PROTECTED_BASELINE_PATH')
        if self.path.is_symlink():raise TaskError('UNSAFE_FILE')
        if self.path.exists():
            fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                s=os.fstat(fd)
                if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_uid!=os.getuid() or s.st_mode & 0o077:
                    raise TaskError('UNSAFE_FILE')
            finally:os.close(fd)

    @classmethod
    def create(cls,path,*,allowed_root,protected_roots,workspace_id,bindings,created_at):
        from .domain import parse_time
        require_id(workspace_id,'workspace');parse_time(created_at)
        bindings=tuple(bindings)
        if not bindings or any(not isinstance(b,Binding) for b in bindings):raise TaskError('INVALID_ARGUMENT')
        if len({b.binding_id for b in bindings})!=len(bindings) or len({b.principal_id for b in bindings})!=len(bindings):raise TaskError('INVALID_ARGUMENT')
        repo=cls(path,allowed_root=allowed_root,protected_roots=protected_roots)
        try:fd=os.open(repo.path,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_NOFOLLOW,0o600)
        except FileExistsError:raise TaskError('DATABASE_EXISTS') from None
        os.close(fd)
        with closing(repo._connection(initializing=True)) as db:
            try:
                db.executescript('BEGIN IMMEDIATE;' + SCHEMA + evidence.SCHEMA + reviews.SCHEMA)
                db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                db.execute('INSERT INTO workspaces VALUES (?,?,?,?,?,?)',(workspace_id,new_id('db'),'LOCAL_SYNTHETIC',1,0,created_at))
                service=new_id('principal')
                db.execute('INSERT INTO principals VALUES (?,?,?,?,?,?,?)',(workspace_id,service,'SERVICE',new_id('binding'),1,1,'[]'))
                for b in bindings:db.execute('INSERT INTO principals VALUES (?,?,?,?,?,?,?)',(workspace_id,b.principal_id,'BOT',b.binding_id,1,1,canonical(b.capabilities)))
                for k,v in {'workspace_id':workspace_id,'service_principal':service,'active_boot':'','cursor_key':os.urandom(32).hex(),'schema_hash':expected_schema_hash()}.items():
                    db.execute('INSERT INTO meta VALUES (?,?)',(k,v))
                db.execute('COMMIT')
            except BaseException:
                if db.in_transaction:db.execute('ROLLBACK')
                raise
        repo.check_integrity()
        return repo

    @classmethod
    def open(cls,path,*,allowed_root,protected_roots):
        repo=cls(path,allowed_root=allowed_root,protected_roots=protected_roots)
        if not repo.path.is_file():raise TaskError('DATABASE_NOT_FOUND')
        repo.check_integrity();return repo

    def _connection(self,*,initializing=False):
        self._check_path()
        if self.quarantined:raise TaskError('QUARANTINED')
        db=sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,isolation_level=None,timeout=.5)
        db.row_factory=sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA busy_timeout=500');db.execute('PRAGMA synchronous=FULL')
            if db.execute('PRAGMA journal_mode').fetchone()[0].lower()!='delete':raise TaskError('UNSUPPORTED_JOURNAL_MODE')
            if not initializing:
                if db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or db.execute('PRAGMA user_version').fetchone()[0]!=SCHEMA_VERSION:
                    raise TaskError('SCHEMA_VERSION_MISMATCH')
                if schema_hash(db)!=expected_schema_hash():raise TaskError('INTEGRITY_FAILURE')
            return db
        except BaseException:
            db.close();raise

    def read(self,fn):
        db=None
        try:
            db=self._connection();db.execute('BEGIN')
            result=fn(db);db.execute('COMMIT');return result
        except sqlite3.OperationalError as exc:
            busy=(getattr(exc,'sqlite_errorcode',0)&255) in {sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED}
            raise TaskError('DB_BUSY' if busy else 'STORAGE_ERROR',retryable=busy) from None
        except sqlite3.DatabaseError:
            self._mark_quarantine();raise TaskError('INTEGRITY_FAILURE') from None
        except TaskError as exc:
            if exc.code=='INTEGRITY_FAILURE':self._mark_quarantine()
            raise
        finally:
            if db is not None:
                try:
                    if db.in_transaction:db.execute('ROLLBACK')
                finally:db.close()

    def write(self,fn):
        started=time.monotonic()
        for attempt in range(4):
            db=None;began=False;phase='begin'
            try:
                db=self._connection();db.execute('BEGIN IMMEDIATE');began=True;phase='body'
                result=fn(db);phase='commit';db.execute('COMMIT');return result
            except sqlite3.OperationalError as exc:
                in_tx=db is not None and db.in_transaction
                if in_tx:db.execute('ROLLBACK')
                if phase=='commit' and began and not in_tx:raise TaskError('COMMIT_OUTCOME_UNKNOWN',retryable=True) from None
                busy=(getattr(exc,'sqlite_errorcode',0)&255) in {sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED}
                if not busy:raise TaskError('STORAGE_ERROR') from None
                if attempt==3 or time.monotonic()-started>=4:raise TaskError('DB_BUSY',retryable=True) from None
            except sqlite3.DatabaseError:
                self._mark_quarantine();raise TaskError('INTEGRITY_FAILURE') from None
            except TaskError as exc:
                if exc.code=='INTEGRITY_FAILURE':self._mark_quarantine()
                raise
            finally:
                if db is not None:
                    try:
                        if db.in_transaction:db.execute('ROLLBACK')
                    finally:db.close()
            time.sleep(random.uniform(.5,1)*(0.05*(2**attempt)))
        raise TaskError('DB_BUSY',retryable=True)

    @staticmethod
    def meta(db,key):
        r=db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
        if r is None:raise TaskError('INTEGRITY_FAILURE')
        return r[0]

    def assert_runtime(self,boot_id):
        """A persisted boot marker alone cannot prove that its coordinator is still alive."""
        try:fd=os.open(self.root/'.task-runtime.lock',os.O_RDONLY|os.O_NOFOLLOW)
        except OSError:raise TaskError('RUNTIME_INACTIVE') from None
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or info.st_mode & 0o077:raise TaskError('RUNTIME_INACTIVE')
            if os.read(fd,128)!=(boot_id+'\n').encode():raise TaskError('RUNTIME_INACTIVE')
            try:fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
            except BlockingIOError:return
            else:
                fcntl.flock(fd,fcntl.LOCK_UN)
                raise TaskError('RUNTIME_INACTIVE')
        finally:os.close(fd)

    def principal(self,db,binding_id):
        ws=self.meta(db,'workspace_id')
        row=db.execute('SELECT * FROM principals WHERE workspace_id=? AND binding_id=?',(ws,binding_id)).fetchone()
        if row is None or row['kind']!='BOT' or not row['active']:raise TaskError('FORBIDDEN')
        try:
            caps=json.loads(row['capabilities_json'])
            if not isinstance(caps,list) or any(not isinstance(c,str) or c not in CAPABILITIES for c in caps):raise TaskError('INTEGRITY_FAILURE')
        except (ValueError,TypeError):raise TaskError('INTEGRITY_FAILURE') from None
        return dict(row),frozenset(caps)

    def task(self,db,task_id,principal,*,permission='READ'):
        ws=principal['workspace_id']
        row=db.execute('SELECT * FROM tm_tasks WHERE workspace_id=? AND task_id=?',(ws,task_id)).fetchone()
        if row is None:raise TaskError('NOT_FOUND_OR_FORBIDDEN')
        if row['owner_principal_id']!=principal['principal_id']:
            acl=db.execute('SELECT 1 FROM task_acl WHERE workspace_id=? AND task_id=? AND principal_id=? AND permission=? AND active=1',(ws,task_id,principal['principal_id'],permission)).fetchone()
            if not acl:raise TaskError('NOT_FOUND_OR_FORBIDDEN')
        return self.verify_task(db,row)

    def verify_task(self,db,row):
        try:
            data=json.loads(row['snapshot_json']);task=Task.from_snapshot(data)
            if hash_json(data)!=row['snapshot_hash'] or (task.workspace_id,task.task_id,task.owner_principal_id,task.state.value,task.version)!=(row['workspace_id'],row['task_id'],row['owner_principal_id'],row['state'],row['version']):raise TaskError('INTEGRITY_FAILURE')
            events=db.execute('SELECT * FROM task_events WHERE workspace_id=? AND task_id=? ORDER BY seq',(task.workspace_id,task.task_id)).fetchall()
            revs=db.execute('SELECT * FROM task_revisions WHERE workspace_id=? AND task_id=? ORDER BY version',(task.workspace_id,task.task_id)).fetchall()
            if len(events)!=task.version or len(revs)!=task.version:raise TaskError('INTEGRITY_FAILURE')
            actors={r[0] for r in db.execute('SELECT principal_id FROM principals WHERE workspace_id=?',(task.workspace_id,)).fetchall()}
            prev_hash=ZERO_HASH;prev_state=None;prev_time=None;prior_task=None
            decoded_events, decoded_revisions = [], []
            for i,(ev,rev) in enumerate(zip(events,revs),1):
                e=json.loads(ev['event_json']);body={k:v for k,v in e.items() if k!='event_hash'}
                snapshot=json.loads(rev['snapshot_json']);old=Task.from_snapshot(snapshot)
                if e['event_hash']!=hash_json(body) or ev['event_hash']!=e['event_hash'] or e['prev_hash']!=prev_hash or e['from_version']!=i-1 or e['to_version']!=i or e['seq']!=i or ev['seq']!=i or rev['version']!=i or e['event_id']!=ev['event_id'] or rev['event_id']!=ev['event_id']:raise TaskError('INTEGRITY_FAILURE')
                if e['task_id']!=task.task_id or old.task_id!=task.task_id or old.workspace_id!=task.workspace_id or old.version!=i or e['from_state']!=prev_state or e['to_state']!=old.state.value or e['at']!=old.updated_at or hash_json(e['payload'])!=e['payload_hash'] or hash_json(snapshot)!=rev['snapshot_hash']:raise TaskError('INTEGRITY_FAILURE')
                require_id(e['event_id'],'event')
                if e['actor_principal_id'] not in actors:raise TaskError('INTEGRITY_FAILURE')
                if prior_task is None:
                    if old.version!=1 or old.definition_revision!=1 or old.state.value!='DRAFT':raise TaskError('INTEGRITY_FAILURE')
                else:
                    if old.created_at!=prior_task.created_at or old.owner_principal_id!=prior_task.owner_principal_id or old.purpose!=prior_task.purpose:raise TaskError('INTEGRITY_FAILURE')
                    expected_revision=prior_task.definition_revision+(old.definition_hash!=prior_task.definition_hash)
                    if old.definition_revision!=expected_revision:raise TaskError('INTEGRITY_FAILURE')
                decoded_events.append(e)
                decoded_revisions.append(old)
                prior_task=old
                if prev_time is not None and parse_time(old.updated_at)<parse_time(prev_time):raise TaskError('INTEGRITY_FAILURE')
                prev_time=old.updated_at;prev_state=old.state.value;prev_hash=e['event_hash']
            evidence.verify_history(db, task, decoded_events, decoded_revisions)
            reviews.verify_history(db, task, decoded_events)
            active=db.execute("SELECT * FROM attempts WHERE workspace_id=? AND task_id=? AND status IN ('ACQUIRED','RUNNING')",(task.workspace_id,task.task_id)).fetchall()
            if task.state.value=='RUNNING':
                if len(active)!=1:raise TaskError('INTEGRITY_FAILURE')
                attempt=active[0]
                require_id(attempt['attempt_id'],'attempt');require_id(attempt['boot_id'],'boot')
                if attempt['actor_principal_id'] not in actors or type(attempt['fencing_token']) is not int or attempt['fencing_token']<1 or parse_time(attempt['lease_expires_at'])<parse_time(attempt['started_at']):raise TaskError('INTEGRITY_FAILURE')
            elif active:raise TaskError('INTEGRITY_FAILURE')
            if revs[-1]['snapshot_json']!=row['snapshot_json']:raise TaskError('INTEGRITY_FAILURE')
            return task
        except (KeyError,ValueError,TypeError,IndexError):raise TaskError('INTEGRITY_FAILURE') from None

    def save(self,db,previous: Task|None,task: Task,*,actor,event_type,now,request_hash,reason=None,related_ids=()):
        snapshot=task.snapshot();serialized=canonical(snapshot);sha=hash_json(snapshot)
        if previous is None:
            db.execute('INSERT INTO tm_tasks VALUES (?,?,?,?,?,?,?)',(task.workspace_id,task.task_id,task.owner_principal_id,task.state.value,task.version,serialized,sha))
        else:
            cur=db.execute('UPDATE tm_tasks SET state=?,version=?,snapshot_json=?,snapshot_hash=? WHERE workspace_id=? AND task_id=? AND version=?',(task.state.value,task.version,serialized,sha,task.workspace_id,task.task_id,previous.version))
            if cur.rowcount!=1:raise TaskError('VERSION_CONFLICT')
        self._append_event(db,previous,task,actor,event_type,now,request_hash,reason,related_ids)
        db.execute('UPDATE workspaces SET generation=generation+1 WHERE workspace_id=?',(task.workspace_id,))

    def _append_event(self,db,previous,task,actor,event_type,now,request_hash,reason,related_ids):
        last=db.execute('SELECT event_hash FROM task_events WHERE workspace_id=? AND task_id=? ORDER BY seq DESC LIMIT 1',(task.workspace_id,task.task_id)).fetchone()
        scope=db.execute('SELECT principal_id,binding_version,active,capabilities_json FROM principals WHERE workspace_id=? ORDER BY principal_id',(task.workspace_id,)).fetchall()
        digest = evidence.evidence_digest(evidence.latest_links(evidence.link_versions(db, task)))
        payload={'reason':reason,'definition_hash':task.definition_hash,'evidence_set_hash':digest,'authorization_scope_hash':hash_json([tuple(x) for x in scope]),'request_hash':request_hash,'related_ids':list(related_ids)}
        event={'event_id':new_id('event'),'task_id':task.task_id,'seq':task.version,'event_type':event_type,'actor_principal_id':actor,'at':now,'from_version':previous.version if previous else 0,'to_version':task.version,'from_state':previous.state.value if previous else None,'to_state':task.state.value,'payload':payload,'payload_hash':hash_json(payload),'prev_hash':last[0] if last else ZERO_HASH}
        event['event_hash']=hash_json(event)
        db.execute('INSERT INTO task_events VALUES (?,?,?,?,?,?)',(task.workspace_id,task.task_id,task.version,event['event_id'],canonical(event),event['event_hash']))
        snapshot=task.snapshot()
        db.execute('INSERT INTO task_revisions VALUES (?,?,?,?,?,?)',(task.workspace_id,task.task_id,task.version,event['event_id'],canonical(snapshot),hash_json(snapshot)))

    def check_integrity(self):
        def check(db):
            if db.execute('PRAGMA quick_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchall():raise TaskError('INTEGRITY_FAILURE')
            meta=dict(db.execute('SELECT key,value FROM meta').fetchall())
            if set(meta)!={'workspace_id','service_principal','active_boot','cursor_key','schema_hash'} or meta['schema_hash']!=expected_schema_hash():raise TaskError('INTEGRITY_FAILURE')
            import re
            if not re.fullmatch('[0-9a-f]{64}',meta['cursor_key']):raise TaskError('INTEGRITY_FAILURE')
            require_id(meta['workspace_id'],'workspace');require_id(meta['service_principal'],'principal')
            if meta['active_boot']:require_id(meta['active_boot'],'boot')
            workspaces=db.execute('SELECT * FROM workspaces').fetchall()
            if len(workspaces)!=1 or workspaces[0]['workspace_id']!=meta['workspace_id']:raise TaskError('INTEGRITY_FAILURE')
            require_id(workspaces[0]['db_instance_id'],'db')
            service=db.execute("SELECT * FROM principals WHERE workspace_id=? AND principal_id=? AND kind='SERVICE' AND active=1",(meta['workspace_id'],meta['service_principal'])).fetchone()
            if service is None:raise TaskError('INTEGRITY_FAILURE')
            graph=evidence.verified_graph(db, meta['workspace_id'])
            if graph:evidence.expiration(db, graph)
            evidence.revocation(db, meta['workspace_id'])
            for row in db.execute('SELECT * FROM tm_tasks').fetchall():self.verify_task(db,row)
            for row in db.execute('SELECT response_json,response_hash FROM idempotency_records').fetchall():
                if hash_json(json.loads(row[0]))!=row[1]:raise TaskError('INTEGRITY_FAILURE')
            return True
        try:return self.read(check)
        except sqlite3.DatabaseError:
            self._mark_quarantine();raise TaskError('INTEGRITY_FAILURE') from None
        except TaskError as exc:
            if exc.code in {'INVALID_ARGUMENT','CLOCK_UNTRUSTED'}:
                self._mark_quarantine();raise TaskError('INTEGRITY_FAILURE') from None
            raise
