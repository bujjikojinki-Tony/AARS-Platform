"""One recovery coordinator; clients do not restart or interrupt each other."""
from contextlib import suppress
from dataclasses import replace
import fcntl
import os
import stat

from .domain import State, canonical, hash_json, new_id, parse_time, stamp
from .errors import TaskError
from . import approval_history, evidence, reviews
from .service import Clock,TaskManager

class TaskRuntime:
    def __init__(self,repository,*,clock=None):
        self.repository=repository;self.clock=clock or Clock();self.boot_id=new_id('boot');self._fd=None

    def __enter__(self):
        if self._fd is not None:raise TaskError('RUNTIME_ALREADY_ACTIVE')
        self.repository.check_integrity()
        lock=self.repository.root/'.task-runtime.lock'
        try:fd=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        except OSError:raise TaskError('UNSAFE_FILE') from None
        try:
            s=os.fstat(fd)
            if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_uid!=os.getuid() or s.st_mode & 0o077:raise TaskError('UNSAFE_FILE')
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise TaskError('RUNTIME_ALREADY_ACTIVE') from None
            self.boot_id=new_id('boot')
            os.ftruncate(fd,0);os.write(fd,(self.boot_id+'\n').encode());os.fsync(fd)
            self._fd=fd
            def start(db):
                self._recover(db,all_previous=True,reason='runtime_restart')
                self._invalidate_evidence(db)
                db.execute("UPDATE meta SET value=? WHERE key='active_boot'",(self.boot_id,))
            self.repository.write(start)
            return self
        except BaseException:
            self._fd=None;os.close(fd);raise

    def _recover(self,db,*,all_previous,reason):
        repo=self.repository;now=stamp(self.clock.now());ws=repo.meta(db,'workspace_id');actor=repo.meta(db,'service_principal');count=0
        for row in db.execute("SELECT * FROM tm_tasks WHERE workspace_id=? AND state IN ('RUNNING','REVIEW_PENDING') ORDER BY task_id",(ws,)).fetchall():
            task=repo.verify_task(db,row)
            if parse_time(now)<parse_time(task.updated_at):raise TaskError('CLOCK_UNTRUSTED')
            attempt=db.execute("SELECT a.*,p.active AS principal_active FROM attempts a JOIN principals p ON p.workspace_id=a.workspace_id AND p.principal_id=a.actor_principal_id WHERE a.workspace_id=? AND a.task_id=? AND a.status IN ('ACQUIRED','RUNNING')",(ws,task.task_id)).fetchone()
            review_status = None
            if task.state == State.REVIEW_PENDING:
                review_status = 'STALE' if all_previous else reviews.invalidation_reason(db, task, now)
                if review_status is None:
                    continue
            elif not all_previous and parse_time(attempt['lease_expires_at']) > parse_time(now) and attempt['principal_active']:
                continue
            result = task.interrupted(now)
            related = ()
            event_type = 'RECOVERED'
            if review_status:
                related = (reviews.close(db, task, review_status), review_status)
                event_type = 'REVIEW_INVALIDATED'
            else:
                db.execute("UPDATE attempts SET status='EXPIRED',finished_at=? WHERE workspace_id=? AND task_id=? AND status IN ('ACQUIRED','RUNNING')", (now, ws, task.task_id))
            repo.save(db, task, result, actor=actor, event_type=event_type, now=now,
                request_hash=hash_json({'reason':reason,'boot':self.boot_id,'task':task.task_id}), reason=reason,
                related_ids=related)
            count+=1
        return count

    def _host_write(self, operation):
        if self._fd is None:
            raise TaskError('RUNTIME_INACTIVE')
        def run(db):
            if self.repository.meta(db, 'active_boot') != self.boot_id:
                raise TaskError('RUNTIME_INACTIVE')
            self.repository.assert_runtime(self.boot_id)
            return operation(db)
        return self.repository.write(run)

    def register_frozen_fixture(self, *, expires_at=None):
        """Host-only ingestion of the pinned archive file. No caller-provided source path."""
        from pathlib import Path
        fixture = Path(__file__).resolve().parents[2] / 'frozen_payload' / evidence.FIXTURE_ARCHIVE_ENTRY
        try:
            with fixture.open('rb') as handle:
                artifact = handle.read(128 * 1024)
        except OSError:
            raise TaskError('SOURCE_UNVERIFIED') from None
        evidence.certify_fixture(artifact)
        return self._host_write(lambda db: evidence.register_fixture(db,
            self.repository.meta(db, 'workspace_id'), artifact, stamp(self.clock.now()), expires_at))

    def revoke_frozen_fixture(self, reason):
        """Record a local host withdrawal and affected task revisions atomically."""
        from .domain import text
        text(reason, 300)
        def revoke(db):
            ws = self.repository.meta(db, 'workspace_id')
            graph = evidence.verified_graph(db, ws)
            if graph is None:
                raise TaskError('EVIDENCE_UNUSABLE')
            if evidence.revocation(db, ws):
                return 0
            now = stamp(self.clock.now())
            if parse_time(now) < parse_time(graph['registered_at']):
                raise TaskError('CLOCK_UNTRUSTED')
            digest = hash_json({'workspace_id': ws, 'at': now, 'reason': reason})
            db.execute('INSERT INTO fixture_revocations VALUES (?,?,?,?)', (ws, now, reason, digest))
            return self._invalidate_evidence(db)
        return self._host_write(revoke)

    def reevaluate_evidence(self):
        return self._host_write(self._invalidate_evidence)

    def _invalidate_evidence(self, db):
        repo = self.repository
        ws = repo.meta(db, 'workspace_id')
        now = stamp(self.clock.now())
        graph = evidence.verified_graph(db, ws)
        if graph is None or evidence.grant_usable(db, graph, now):
            return 0
        revoked = evidence.revocation(db, ws)
        if not revoked and not evidence.expiration(db, graph):
            if not graph['expires_at'] or parse_time(now) < parse_time(graph['expires_at']):
                raise TaskError('CLOCK_UNTRUSTED')
            db.execute('INSERT INTO fixture_expirations VALUES (?,?,?)',
                       (ws, now, hash_json({'grant_hash': graph['grant_hash'], 'at': now})))
        target = 'REVOKED' if revoked else 'REVIEW_REQUIRED'
        actor = repo.meta(db, 'service_principal')
        affected = db.execute('SELECT t.* FROM tm_tasks t WHERE t.workspace_id=? AND EXISTS '
            '(SELECT 1 FROM evidence_link_versions l WHERE l.workspace_id=t.workspace_id AND l.task_id=t.task_id)',
            (ws,)).fetchall()
        count = 0
        for row in affected:
            task = repo.verify_task(db, row)
            current = evidence.latest_links(evidence.link_versions(db, task))
            for link in current:
                if link['use_state'] in (target, 'REVOKED'):
                    continue
                if parse_time(now) < parse_time(task.updated_at):
                    raise TaskError('CLOCK_UNTRUSTED')
                usage = 'UNUSABLE' if approval_history.result_rejected(db, task) else 'REVIEW_REQUIRED'
                updated = replace(task, version=task.version + 1, updated_at=now,
                    state=State.PAUSED if task.state == State.REVIEW_PENDING else task.state, usage_state=usage)
                db.execute('INSERT INTO evidence_link_versions VALUES (?,?,?,?,?,?,?,?,?)', (ws,
                    task.task_id, link['link_id'], link['revision'] + 1, link['snapshot_id'], updated.version,
                    target, link['scope_hash'], link['verification_hash']))
                reason = 'fixture_revoked' if revoked else 'fixture_expired'
                related = (link['link_id'],link['snapshot_id'])
                if task.state == State.REVIEW_PENDING:
                    related += (reviews.close(db, task, 'STALE'), 'STALE')
                event_type = 'EVIDENCE_INVALIDATED'
                if task.state == State.COMPLETED and task.usage_state != updated.usage_state:
                    event_type = 'TASK_USABILITY_CHANGED'
                repo.save(db, task, updated, actor=actor, event_type=event_type, now=now,
                    request_hash=hash_json({'reason': reason, 'link': link['link_id'], 'revision': link['revision'] + 1}),
                    reason=reason, related_ids=related)
                task = updated
                count += 1
        return count

    def recover_expired(self):
        def recover(db):
            recovered = self._recover(db, all_previous=False, reason='lease_or_binding_expired')
            self._invalidate_evidence(db)
            return recovered
        return self._host_write(recover)

    def manager(self,binding_id):
        if self._fd is None:raise TaskError('RUNTIME_INACTIVE')
        return TaskManager(self.repository,binding_id,self.boot_id,clock=self.clock)

    def close(self):
        if self._fd is None:return
        fd=self._fd
        try:
            def stop(db):
                if self.repository.meta(db,'active_boot')==self.boot_id:
                    self._recover(db,all_previous=True,reason='runtime_shutdown')
                    db.execute("UPDATE meta SET value='' WHERE key='active_boot'")
            if not self.repository.quarantined:self.repository.write(stop)
        finally:
            self._fd=None;fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

    def __exit__(self,*exc):self.close()
