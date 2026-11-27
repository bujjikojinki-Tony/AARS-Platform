"""Local synthetic task evidence store; no production ingestion or authorization."""
import os
import stat
import hashlib
import json
import re
import sqlite3
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from contextlib import closing
from aars_core.certification.serialization import object_from_dict


def plain(x):
    if isinstance(x, Enum): return x.value
    if isinstance(x, datetime): return x.isoformat()
    if is_dataclass(x): return {f.name: plain(getattr(x,f.name)) for f in fields(x)}
    if isinstance(x, Mapping): return {k: plain(v) for k,v in x.items()}
    if isinstance(x, (tuple,list)): return [plain(v) for v in x]
    return x


def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def task_check(task):
    if not isinstance(task,str) or not re.fullmatch(r'OMB-SIM-[A-Za-z0-9_-]{1,64}',task): raise ValueError('Invalid synthetic task ID')

class Store:
    def __init__(self,path):
        self.path=Path(path)
        if not self.path.is_absolute(): raise ValueError('Absolute database path required')
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        # Refuse symlinks and non-private containing directories before opening SQLite.
        if self.path.parent.is_symlink() or self.path.parent.stat().st_mode & 0o077:
            raise ValueError('Database directory must be private (0700)')
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError('Database must be a regular file without hard links')
            os.fchmod(fd, 0o600)
        finally:
            os.close(fd)
        with closing(self.connect()) as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS tasks(task_id TEXT PRIMARY KEY, report TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS objects(task_id TEXT NOT NULL REFERENCES tasks(task_id), object_id TEXT NOT NULL, type TEXT NOT NULL, record TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(task_id,object_id));
            CREATE INDEX IF NOT EXISTS object_type_idx ON objects(task_id,type);''')
    def connect(self):
        db=sqlite3.connect(self.path, timeout=10)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            return db
        except BaseException:
            db.close()
            raise
    def seed(self,task,client,graph):
        task_check(task)
        report=client.certify(graph).to_dict()
        if not report['valid'] or len(graph)!=9 or any(o.provenance.source_type!='test_fixture' for o in graph): raise ValueError('Only valid synthetic fixture permitted')
        records=[(task,o.id,o.type.value,canonical(plain(o))) for o in graph]
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT report FROM tasks WHERE task_id=?',(task,)).fetchone()
            if existing: return {'task_id':task,'created':False,'object_count':len(self._read(db,task)), 'report':json.loads(existing[0])}
            db.execute('INSERT INTO tasks VALUES (?,?)',(task,canonical(report)))
            db.executemany('INSERT INTO objects VALUES (?,?,?,?,?)',[(*r,digest(r[3])) for r in records])
            return {'task_id':task,'created':True,'object_count':len(records),'report':report}
    def _read(self,db,task,kind=None):
        sql='SELECT object_id,type,record,sha256 FROM objects WHERE task_id=?'; params=[task]
        if kind: sql+=' AND type=?'; params.append(kind)
        rows=db.execute(sql+' ORDER BY object_id',params).fetchall()
        result=[]
        for oid,typ,record,sha in rows:
            if digest(record)!=sha: raise ValueError('Stored record integrity failure')
            obj=object_from_dict(json.loads(record))
            if obj.id!=oid or obj.type.value!=typ: raise ValueError('Stored index mismatch')
            result.append({'record':plain(obj),'record_sha256':sha})
        return result
    def query(self,task,kind=None):
        task_check(task)
        with closing(self.connect()) as db:
            found=db.execute('SELECT 1 FROM tasks WHERE task_id=?',(task,)).fetchone()
            rows=self._read(db,task,kind)
        return {'task_id':task,'found':bool(found),'objects':rows,'object_count':len(rows)}
