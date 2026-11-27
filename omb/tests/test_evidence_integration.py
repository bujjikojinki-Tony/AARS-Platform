from datetime import timedelta
import hashlib
from pathlib import Path
import sqlite3

import pytest

from aars_task_manager import Repository, State, TaskError, TaskRuntime
from aars_task_manager.domain import stamp
from aars_task_manager.evidence import certify_fixture, FIXTURE_ARTIFACT_HASH
from aars_task_manager.migration import migrate_b1_copy
from aars_task_manager.storage import expected_schema_hash, SCHEMA_VERSION
from tests.support import create, key, seed_precondition


def link_args(task, attempt, snapshot):
    return {'task_id': task['task_id'], 'expected_version': task['version'], 'idempotency_key': key(),
            'attempt_id': attempt['attempt_id'], 'fencing_token': attempt['fencing_token'], 'snapshot_id': snapshot}


def running_fixture(system, *, expires_at=None):
    receipt = system['runtime'].register_frozen_fixture(expires_at=expires_at)
    task, attempt = seed_precondition(system['repo'], system['manager'], State.RUNNING, system['clock'])
    return task, attempt, receipt


def test_import_real_archived_bytes_with_full_sdk_closure(system):
    receipt = system['runtime'].register_frozen_fixture()
    assert receipt['artifact_sha256'] == FIXTURE_ARTIFACT_HASH
    assert receipt['object_count'] == 9
    assert receipt['execution_authorized'] is False
    assert system['runtime'].register_frozen_fixture() == receipt
    assert system['repo'].check_integrity()
    raw = Path('frozen_payload/BOT_TASK_OBJECT_SNAPSHOT.json').read_bytes()
    with pytest.raises(TaskError, match='SOURCE_UNVERIFIED'):
        certify_fixture(raw.replace(b'test_fixture', b'real_source', 1))


def test_link_atomic_idempotent_and_traceable_after_restart(system):
    task, attempt, proof = running_fixture(system)
    manager, repo, runtime = system['manager'], system['repo'], system['runtime']
    args = link_args(task, attempt, proof['evidence_snapshot_id'])
    first = manager.execute('evidence_link', args)
    replay = manager.execute('evidence_link', args)
    assert replay['replayed'] and replay['data'] == first['data']
    assert first['data']['task']['version'] == 3
    trace = manager.evidence_trace(task['task_id'])
    assert len(trace['history']) == 1 and trace['source']['graph_digest'] == proof['graph_digest']
    assert trace['provenance']['observation_ids']
    assert trace['provenance']['core_provenance']['content_hash'] == 'sha256:unavailable'
    assert trace['history'][0]['event_hash'] == manager.events(task['task_id'])['data']['events'][-1]['event_hash']
    with pytest.raises(TaskError, match='NO_CHANGE'):
        manager.execute('evidence_link', {**args, 'expected_version': 3, 'idempotency_key': key()})
    runtime.close()
    with TaskRuntime(repo, clock=system['clock']) as restarted:
        after = restarted.manager(manager.binding_id).evidence_trace(task['task_id'])
    assert after['history'] == trace['history'] and after['version'] == 4
    assert after['evidence_set_hash'] == trace['evidence_set_hash']


def test_observation_cannot_be_linked_as_evidence(system):
    task, attempt, _ = running_fixture(system)
    observation = system['repo'].read(lambda db: db.execute("SELECT snapshot_id FROM object_snapshots WHERE object_type='observation'").fetchone()[0])
    # The archived observation is intact but lacks the Evidence type required by the link.
    with pytest.raises(TaskError, match='EVIDENCE_UNUSABLE'):
        system['manager'].execute('evidence_link', link_args(task, attempt, observation))
    assert system['manager'].evidence_trace(task['task_id'])['history'] == []


def test_catalog_and_draft_restrictions_and_cross_bot_visibility(system):
    task, attempt, proof = running_fixture(system)
    manager = system['manager']
    for purpose, code in [('LOCAL_SYNTHETIC_VALIDATION', 'INVALID_TRANSITION'), ('CATALOG_METADATA', 'PURPOSE_NOT_EXECUTABLE')]:
        draft = create(manager, purpose=purpose)
        with pytest.raises(TaskError, match=code):
            manager.execute('evidence_link', link_args(draft, attempt, proof['evidence_snapshot_id']))
    with pytest.raises(TaskError, match='NOT_FOUND_OR_FORBIDDEN'):
        system['other'].evidence_trace(task['task_id'])
    with pytest.raises(TaskError, match='NOT_FOUND_OR_FORBIDDEN'):
        system['other'].execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))


def test_version_and_fence_checked_before_link(system):
    task, attempt, proof = running_fixture(system)
    args = link_args(task, attempt, proof['evidence_snapshot_id'])
    for change, code in [({'expected_version': 1}, 'VERSION_CONFLICT'), ({'fencing_token': 2}, 'FENCING_CONFLICT')]:
        with pytest.raises(TaskError, match=code):
            system['manager'].execute('evidence_link', {**args, **change})
    assert not system['manager'].evidence_trace(task['task_id'])['history']


def test_link_and_event_rollback_together(system, monkeypatch):
    task, attempt, proof = running_fixture(system)
    repo = system['repo']
    with monkeypatch.context() as override:
        def fail(*args, **kwargs):
            raise RuntimeError('test interruption')
        override.setattr(repo, '_append_event', fail)
        with pytest.raises(RuntimeError, match='test interruption'):
            system['manager'].execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))
    assert system['manager'].evidence_trace(task['task_id'])['history'] == []
    assert repo.check_integrity()


def test_revocation_preserves_history_and_blocks_new_use(system):
    task, attempt, proof = running_fixture(system)
    manager, runtime = system['manager'], system['runtime']
    manager.execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))
    before = manager.evidence_trace(task['task_id'])
    assert runtime.revoke_frozen_fixture('Retired synthetic test grant') == 1
    assert runtime.revoke_frozen_fixture('Duplicate') == 0
    after = manager.evidence_trace(task['task_id'])
    assert after['history'][0] == before['history'][0]
    assert after['history'][1]['revision'] == 2 and after['current'][0]['effective_use_state'] == 'REVOKED'
    assert after['evidence_set_hash'] != before['evidence_set_hash']
    next_task, next_attempt = seed_precondition(system['repo'], manager, State.RUNNING, system['clock'])
    with pytest.raises(TaskError, match='EVIDENCE_UNUSABLE'):
        manager.execute('evidence_link', link_args(next_task, next_attempt, proof['evidence_snapshot_id']))


def test_expiry_read_fails_closed_then_persists_and_can_be_revoked(system):
    task, attempt, proof = running_fixture(system, expires_at=stamp(system['clock'].now() + timedelta(seconds=30)))
    manager, runtime = system['manager'], system['runtime']
    manager.execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))
    system['clock'].advance(30)
    trace = manager.evidence_trace(task['task_id'])
    assert trace['current'][0]['effective_use_state'] == 'REVIEW_REQUIRED' and len(trace['history']) == 1
    assert runtime.reevaluate_evidence() == 1
    assert runtime.reevaluate_evidence() == 0
    assert runtime.revoke_frozen_fixture('Retired after expiry') == 1
    states = [row['use_state'] for row in manager.evidence_trace(task['task_id'])['history']]
    assert states == ['USABLE_FIXTURE', 'REVIEW_REQUIRED', 'REVOKED']


def test_mismatched_link_tamper_quarantines(system):
    task, attempt, proof = running_fixture(system)
    system['manager'].execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))
    with sqlite3.connect(system['repo'].path) as db:
        db.execute("UPDATE evidence_link_versions SET scope_hash='wrong'")
    with pytest.raises(TaskError, match='INTEGRITY_FAILURE'):
        system['manager'].evidence_trace(task['task_id'])
    assert system['repo'].quarantined


def test_unknown_or_tampered_source_not_usable(system):
    task, attempt = seed_precondition(system['repo'], system['manager'], State.RUNNING, system['clock'])
    with pytest.raises(TaskError, match='EVIDENCE_UNUSABLE'):
        system['manager'].execute('evidence_link', link_args(task, attempt, 'sha256:' + '0' * 64))
    proof = system['runtime'].register_frozen_fixture()
    with sqlite3.connect(system['repo'].path) as db:
        db.execute("UPDATE object_snapshots SET canonical_json='{}' WHERE snapshot_id=?", (proof['evidence_snapshot_id'],))
    with pytest.raises(TaskError, match='INTEGRITY_FAILURE'):
        system['manager'].execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))


def to_b1_fixture(path):
    with sqlite3.connect(path) as db:
        for table in ('evidence_link_versions', 'object_snapshots', 'fixture_revocations', 'fixture_expirations', 'fixture_graphs'):
            db.execute(f'DROP TABLE {table}')
        db.execute('PRAGMA user_version=1')
        db.execute("UPDATE meta SET value=? WHERE key='schema_hash'", (expected_schema_hash(1),))


def test_migration_copies_history_and_keeps_b1_bytes(system, tmp_path):
    repo, runtime = system['repo'], system['runtime']
    task = create(system['manager'])
    runtime.close()
    to_b1_fixture(repo.path)
    before = hashlib.sha256(repo.path.read_bytes()).hexdigest()
    root = tmp_path / 'c2'; root.mkdir(mode=0o700)
    copied = migrate_b1_copy(repo.path, root/'task.sqlite', source_root=repo.root,
                             target_root=root, protected_roots=(system['protected'],))
    assert hashlib.sha256(repo.path.read_bytes()).hexdigest() == before
    with TaskRuntime(copied, clock=system['clock']) as next_runtime:
        assert next_runtime.manager(system['manager'].binding_id).get(task['task_id'])['data']['task'] == task
        assert copied.read(lambda db: db.execute('PRAGMA user_version').fetchone()[0]) == SCHEMA_VERSION
        assert next_runtime.register_frozen_fixture()['object_count'] == 9


def test_migration_never_copies_active_database(system, tmp_path):
    repo = system['repo']; root = tmp_path / 'c2'; root.mkdir(mode=0o700)
    target = root/'task.sqlite'
    with pytest.raises(TaskError, match='MIGRATION_SOURCE_ACTIVE'):
        migrate_b1_copy(repo.path, target, source_root=repo.root, target_root=root, protected_roots=(system['protected'],))
    assert not target.exists()


def test_withdrawal_blocks_cached_link_result(system):
    task, attempt, proof = running_fixture(system)
    args = link_args(task, attempt, proof['evidence_snapshot_id'])
    system['manager'].execute('evidence_link', args)
    system['runtime'].revoke_frozen_fixture('Withdrawn before replay')
    with pytest.raises(TaskError, match='EVIDENCE_UNUSABLE'):
        system['manager'].execute('evidence_link', args)


def test_binding_needs_explicit_evidence_capability(system):
    task, attempt, proof = running_fixture(system)
    manager, repo = system['manager'], system['repo']
    repo.write(lambda db: db.execute("UPDATE principals SET capabilities_json='[\"task.work\",\"task.read\"]' WHERE binding_id=?",
                                    (manager.binding_id,)))
    with pytest.raises(TaskError, match='FORBIDDEN'):
        manager.execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))


def test_committed_expiry_does_not_reverse_with_clock_rollback(system):
    first, attempt, proof = running_fixture(system, expires_at=stamp(system['clock'].now() + timedelta(seconds=5)))
    other, other_attempt = seed_precondition(system['repo'], system['manager'], State.RUNNING, system['clock'])
    system['clock'].advance(6)
    assert system['runtime'].reevaluate_evidence() == 0  # Persists expiry even when no task is linked.
    system['clock'].advance(-5)
    with pytest.raises(TaskError, match='EVIDENCE_UNUSABLE'):
        system['manager'].execute('evidence_link', link_args(other, other_attempt, proof['evidence_snapshot_id']))


def test_restart_persists_expiry_and_retains_original_revision(system):
    task, attempt, proof = running_fixture(system, expires_at=stamp(system['clock'].now() + timedelta(seconds=5)))
    system['manager'].execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))
    system['runtime'].close()
    system['clock'].advance(6)
    with TaskRuntime(system['repo'], clock=system['clock']) as restarted:
        trace = restarted.manager(system['manager'].binding_id).evidence_trace(task['task_id'])
        assert trace['current'][0]['effective_use_state'] == 'REVIEW_REQUIRED'
        assert [link['revision'] for link in trace['history']] == [1, 2]


def test_migration_invalid_history_never_publishes_destination(system, tmp_path):
    repo = system['repo']; task = create(system['manager'])
    system['runtime'].close(); to_b1_fixture(repo.path)
    with sqlite3.connect(repo.path) as db:
        db.execute("UPDATE task_events SET event_hash='invalid' WHERE task_id=?", (task['task_id'],))
    root = tmp_path / 'c2'; root.mkdir(mode=0o700)
    before = repo.path.read_bytes()
    with pytest.raises(TaskError, match='INTEGRITY_FAILURE'):
        migrate_b1_copy(repo.path, root/'task.sqlite', source_root=repo.root, target_root=root,
                        protected_roots=(system['protected'],))
    assert repo.path.read_bytes() == before and list(root.iterdir()) == []
