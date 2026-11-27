import fcntl
import sqlite3

import pytest

from aars_task_manager.approval_enrollment import EnrollmentAnchor
from aars_task_manager.approval_transactions import ResultDecisionStore
from aars_task_manager.domain import new_id
from aars_task_manager.errors import TaskError
from aars_task_manager.migration import migrate_d4_copy
from aars_task_manager.runtime import TaskRuntime
from aars_task_manager.storage import Repository, SCHEMA_VERSION, expected_schema_hash
from tests.test_approval_usability import decide


HISTORY_TABLES = (
    'task_events', 'task_revisions', 'evidence_link_versions', 'fixture_revocations',
    'result_review_requests', 'result_operator_pins', 'result_approval_challenges', 'result_approval_decisions',
)


def offline_d4(system, *, revoked=False):
    if revoked:
        _, task_id, idem, raw, decision = decide(system, expires=False)
        assert system['runtime'].revoke_frozen_fixture('fixture withdrawal in D4') == 1
        assert system['manager'].events(task_id)['data']['events'][-1]['event_type'] == 'TASK_USABILITY_CHANGED'
    else:
        _, task_id, idem, raw, decision = decide(system, expires=False)
    system['runtime'].close()
    repo = system['repo']
    assert expected_schema_hash(4) == expected_schema_hash(SCHEMA_VERSION)
    with sqlite3.connect(repo.path) as db:
        # D4 and D5 share their tables. Keep the bytes of the histories intact.
        db.execute('PRAGMA user_version=4')
    return repo, task_id, idem, raw, decision


def target_copy(repo, target, protected):
    return migrate_d4_copy(repo.path, target/'tasks.sqlite',
                           source_root=repo.root, target_root=target, protected_roots=(protected,))


def history(db):
    return {table: db.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()
            for table in HISTORY_TABLES}


@pytest.mark.parametrize('revoked', [False, True])
def test_copy_preserves_d4_history_and_rotates_runtime_identity(system, tmp_path, revoked):
    repo, task_id, idem, raw, decision = offline_d4(system, revoked=revoked)
    with sqlite3.connect(repo.path) as old:
        original = history(old)
        original_meta = dict(old.execute('SELECT key,value FROM meta'))
        old_instance, generation = old.execute('SELECT db_instance_id,generation FROM workspaces').fetchone()
    before = repo.path.read_bytes()
    target = tmp_path/'migrated'
    target.mkdir(mode=0o700)
    new = target_copy(repo, target, system['protected'])
    assert new.check_integrity() and repo.path.read_bytes() == before
    with sqlite3.connect(new.path) as copied:
        assert copied.execute('PRAGMA user_version').fetchone()[0] == SCHEMA_VERSION == 5
        assert original == history(copied)
        current_meta = dict(copied.execute('SELECT key,value FROM meta'))
        new_instance, new_generation = copied.execute('SELECT db_instance_id,generation FROM workspaces').fetchone()
        assert new_instance != old_instance and new_generation == generation + 1
        assert current_meta['cursor_key'] != original_meta['cursor_key']
        assert current_meta['active_boot'] == ''

    with TaskRuntime(new, clock=system['clock']) as runtime:
        manager = runtime.manager(system['manager'].binding_id)
        inspected = manager.get(task_id)['data']['task']
        assert inspected['state'] == 'COMPLETED'
        assert inspected['usage_state'] == ('REVIEW_REQUIRED' if revoked else 'USABLE')
        events = manager.events(task_id)['data']['events']
        assert events[decision['task_version']-1]['event_type'] == 'RESULT_DECIDED'
        workspace, operator, key_id, _, fingerprint, _ = original['result_operator_pins'][0]
        anchor = EnrollmentAnchor(workspace, old_instance, operator, key_id, fingerprint)
        store = ResultDecisionStore(new, boot_id=runtime.boot_id, anchor=anchor,
                                    now=system['clock'].now, monotonic_now=lambda: 100.0)
        with pytest.raises(TaskError, match='^APPROVAL_CONTEXT_STALE$'):
            store.submit(raw, idempotency_key=idem)
    assert repo.path.read_bytes() == before


def test_current_reader_requires_d4_copy_and_leaves_original_untouched(system):
    repo, _, _, _, _ = offline_d4(system, revoked=True)
    before = repo.path.read_bytes()
    with pytest.raises(TaskError, match='^SCHEMA_VERSION_MISMATCH$'):
        Repository.open(repo.path, allowed_root=repo.root, protected_roots=(system['protected'],))
    assert not repo.quarantined and repo.path.read_bytes() == before


@pytest.mark.parametrize('field', ['db_instance_id', 'cursor_key', 'active_boot', 'approval_reason'])
def test_copy_rejects_corrupt_d4_source_before_publishing(system, tmp_path, field):
    repo, _, _, _, _ = offline_d4(system)
    target = tmp_path/'invalid'
    target.mkdir(mode=0o700)
    with sqlite3.connect(repo.path) as db:
        if field == 'db_instance_id':
            db.execute("UPDATE workspaces SET db_instance_id='invalid'")
        elif field == 'approval_reason':
            db.execute("UPDATE result_approval_decisions SET reason='changed signed reason'")
        else:
            db.execute("UPDATE meta SET value='invalid' WHERE key=?", (field,))
    before = repo.path.read_bytes()
    with pytest.raises(TaskError, match='^INTEGRITY_FAILURE$'):
        target_copy(repo, target, system['protected'])
    assert list(target.iterdir()) == [] and repo.path.read_bytes() == before and not repo.quarantined


def test_copy_respects_runtime_lock_and_existing_target(system, tmp_path):
    repo, _, _, _, _ = offline_d4(system)
    target = tmp_path/'locked'
    target.mkdir(mode=0o700)
    original = repo.path.read_bytes()
    with (repo.root/'.task-runtime.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(TaskError, match='^MIGRATION_SOURCE_ACTIVE$'):
            target_copy(repo, target, system['protected'])
    assert list(target.iterdir()) == [] and repo.path.read_bytes() == original
    copied = target_copy(repo, target, system['protected'])
    before_retry = copied.path.read_bytes()
    with pytest.raises(TaskError, match='^DATABASE_EXISTS$'):
        target_copy(repo, target, system['protected'])
    assert copied.path.read_bytes() == before_retry and repo.path.read_bytes() == original


def test_copy_clears_a_valid_stale_boot_marker(system, tmp_path):
    repo, _, _, _, _ = offline_d4(system)
    earlier = new_id('boot')
    with sqlite3.connect(repo.path) as db:
        db.execute("UPDATE meta SET value=? WHERE key='active_boot'", (earlier,))
    target = tmp_path/'restart'
    target.mkdir(mode=0o700)
    before = repo.path.read_bytes()
    new = target_copy(repo, target, system['protected'])
    assert new.read(lambda db: new.meta(db, 'active_boot')) == ''
    assert repo.path.read_bytes() == before
