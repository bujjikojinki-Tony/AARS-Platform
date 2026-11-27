"""Offline B1, C2 or D3 to D4 migration into a new private database file."""
from contextlib import closing
import fcntl
import os
from pathlib import Path
import sqlite3
import stat
import time
from tempfile import TemporaryDirectory

from . import approval_history, evidence, reviews
from .domain import new_id
from .errors import TaskError
from .storage import APPLICATION_ID, SCHEMA_VERSION, Repository, expected_schema_hash, schema_hash


def migrate_b1_copy(source, target, *, source_root, target_root, protected_roots):
    return _migrate(source, target, source_root=source_root, target_root=target_root, protected_roots=protected_roots, version=1)

def migrate_c2_copy(source, target, *, source_root, target_root, protected_roots):
    return _migrate(source, target, source_root=source_root, target_root=target_root, protected_roots=protected_roots, version=2)

def migrate_d3_copy(source, target, *, source_root, target_root, protected_roots):
    return _migrate(source, target, source_root=source_root, target_root=target_root, protected_roots=protected_roots, version=3)

def _migrate(source, target, *, source_root, target_root, protected_roots, version):
    source = Path(source)
    protected = tuple(map(Path, protected_roots))
    old = Repository(source, allowed_root=source_root, protected_roots=protected)
    new = Repository(target, allowed_root=target_root, protected_roots=(*protected, old.root))
    if new.path.exists():
        raise TaskError('DATABASE_EXISTS')
    if old.quarantined or not old.path.is_file():
        raise TaskError('MIGRATION_SOURCE_UNAVAILABLE')
    try:
        lease = os.open(old.root / '.task-runtime.lock', os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        raise TaskError('MIGRATION_SOURCE_UNAVAILABLE') from None
    try:
        info = os.fstat(lease)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise TaskError('MIGRATION_SOURCE_UNAVAILABLE')
        try:
            fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            raise TaskError('MIGRATION_SOURCE_ACTIVE') from None
        with TemporaryDirectory(dir=new.root) as directory:
            destination = Path(directory) / 'migration.sqlite'
            fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd)
            with closing(sqlite3.connect(old.path.as_uri() + '?mode=ro', uri=True, timeout=.5)) as src:
                if (src.execute('PRAGMA journal_mode').fetchone()[0] != 'delete'
                    or src.execute('PRAGMA application_id').fetchone()[0] != APPLICATION_ID
                    or src.execute('PRAGMA user_version').fetchone()[0] != version
                    or schema_hash(src) != expected_schema_hash(version)):
                    raise TaskError('SCHEMA_VERSION_MISMATCH')
                if src.execute("SELECT value FROM meta WHERE key='schema_hash'").fetchone() != (expected_schema_hash(version),):
                    raise TaskError('INTEGRITY_FAILURE')
                with closing(sqlite3.connect(destination, isolation_level=None)) as dst:
                    deadline = time.monotonic() + 5
                    def check_deadline(status, remaining, total):
                        if time.monotonic() >= deadline:
                            raise TaskError('DB_BUSY', retryable=True)
                    src.backup(dst, pages=128, progress=check_deadline, sleep=.05)
                    dst.execute('PRAGMA foreign_keys=ON')
                    dst.executescript('BEGIN IMMEDIATE;' + (evidence.SCHEMA if version == 1 else '')
                                      + (reviews.SCHEMA if version < 3 else '') + approval_history.SCHEMA)
                    dst.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                    dst.execute("UPDATE meta SET value=? WHERE key='schema_hash'", (expected_schema_hash(),))
                    dst.execute("UPDATE meta SET value='' WHERE key='active_boot'")
                    dst.execute("UPDATE meta SET value=? WHERE key='cursor_key'", (os.urandom(32).hex(),))
                    dst.execute('UPDATE workspaces SET db_instance_id=?, generation=generation+1', (new_id('db'),))
                    dst.execute('COMMIT')
            Repository.open(destination, allowed_root=Path(directory), protected_roots=(*protected, old.root))
            try:
                os.link(destination, new.path)
            except FileExistsError:
                raise TaskError('DATABASE_EXISTS') from None
            destination.unlink()
        return Repository.open(new.path, allowed_root=new.root, protected_roots=(*protected, old.root))
    finally:
        os.close(lease)
