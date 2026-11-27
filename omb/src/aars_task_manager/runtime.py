"""One recovery coordinator; clients do not restart or interrupt each other."""
from contextlib import suppress
from dataclasses import replace
import fcntl
import os
import stat

from .domain import State, canonical, hash_json, new_id, parse_time, stamp
from .errors import TaskError
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
            if not all_previous:
                if task.state!=State.RUNNING:continue
                if attempt is None:raise TaskError('INTEGRITY_FAILURE')
                if parse_time(attempt['lease_expires_at'])>parse_time(now) and attempt['principal_active']:continue
            result=task.interrupted(now)
            db.execute("UPDATE attempts SET status='EXPIRED',finished_at=? WHERE workspace_id=? AND task_id=? AND status IN ('ACQUIRED','RUNNING')",(now,ws,task.task_id))
            repo.save(db,task,result,actor=actor,event_type='RECOVERED',now=now,request_hash=hash_json({'reason':reason,'boot':self.boot_id,'task':task.task_id}),reason=reason)
            count+=1
        return count

    def recover_expired(self):
        if self._fd is None:raise TaskError('RUNTIME_INACTIVE')
        def recover(db):
            if self.repository.meta(db,'active_boot')!=self.boot_id:raise TaskError('RUNTIME_INACTIVE')
            return self._recover(db,all_previous=False,reason='lease_or_binding_expired')
        return self.repository.write(recover)

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
