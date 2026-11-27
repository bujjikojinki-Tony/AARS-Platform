from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import json

import pytest

from aars_task_manager.domain import stamp
from aars_task_manager.errors import TaskError
from aars_task_manager.mcp_server import ToolAdapter
from aars_task_manager.runtime import TaskRuntime
from tests.test_approval_transactions import counts, issue, setup


def decide(system, *, decision='APPROVE_RESULT', expires=True):
    cutoff = stamp(system['clock'].now() + timedelta(seconds=30)) if expires else None
    store, review, signer = setup(system, expires_at=cutoff)
    idem, _, raw = issue(store, review, signer, decision)
    committed = store.submit(raw, idempotency_key=idem)
    return store, review['task_id'], idem, raw, committed


def snapshot(manager, task_id):
    return manager.get(task_id)['data']['task']


def summary(manager, task_id):
    return next(row for row in manager.list_tasks()['data']['tasks'] if row['task_id'] == task_id)


def test_reads_and_evidence_trace_agree_at_expiry_without_mutating_history(system):
    _, task_id, _, _, decision = decide(system)
    manager, repo = system['manager'], system['repo']
    adapter = ToolAdapter(manager)
    system['clock'].advance(29)
    assert snapshot(manager, task_id)['usage_state'] == summary(manager, task_id)['usage_state'] == 'USABLE'
    original = repo.path.read_bytes()
    system['clock'].advance(1)
    get = adapter.call('aars_task_get_v1', {'task_id': task_id})
    listing = adapter.call('aars_task_list_v1', {'state': 'COMPLETED'})
    task = get['data']['task']
    assert task['state'] == 'COMPLETED' and task['version'] == decision['task_version']
    assert task['usage_state'] == listing['data']['tasks'][0]['usage_state'] == 'REVIEW_REQUIRED'
    trace = manager.evidence_trace(task_id)
    assert trace['current'][0]['effective_use_state'] == 'REVIEW_REQUIRED'
    assert len(trace['history']) == 1 and original == repo.path.read_bytes()


@pytest.mark.parametrize('invalidation', ['expiry', 'revocation'])
def test_invalidation_records_usability_event_and_preserves_signed_decision(system, invalidation):
    store, task_id, idem, raw, decision = decide(system, expires=invalidation == 'expiry')
    manager, runtime, repo = (system[name] for name in ('manager', 'runtime', 'repo'))
    before = manager.events(task_id)['data']['events'][-1]
    if invalidation == 'expiry':
        system['clock'].advance(30)
        assert runtime.recover_expired() == 0
        use_state = 'REVIEW_REQUIRED'
    else:
        assert runtime.revoke_frozen_fixture('retired fixture') == 1
        use_state = 'REVOKED'
    after = manager.events(task_id)['data']['events'][-1]
    task = snapshot(manager, task_id)
    assert (task['state'], task['usage_state'], task['version']) == (
        'COMPLETED', 'REVIEW_REQUIRED', decision['task_version'] + 1)
    assert before['event_type'] == 'RESULT_DECIDED' and after['event_type'] == 'TASK_USABILITY_CHANGED'
    assert after['prev_hash'] == before['event_hash']
    trace = manager.evidence_trace(task_id)
    assert trace['history'][-1]['event_hash'] == after['event_hash']
    assert trace['history'][-1]['use_state'] == use_state
    assert store.submit(raw, idempotency_key=idem) == {**decision, 'replayed': True}
    assert runtime.reevaluate_evidence() == runtime.recover_expired() == 0
    assert counts(repo) == (1, 1, task['version'], task['version']) and repo.check_integrity()


def test_restart_materializes_expiry_only_once(system):
    _, task_id, _, _, decision = decide(system)
    repo, clock = system['repo'], system['clock']
    binding = system['manager'].binding_id
    system['runtime'].close()
    clock.advance(30)
    version = decision['task_version'] + 1
    for _ in range(2):
        with TaskRuntime(repo, clock=clock) as runtime:
            manager = runtime.manager(binding)
            task = snapshot(manager, task_id)
            assert (task['usage_state'], task['version']) == ('REVIEW_REQUIRED', version)
            assert manager.events(task_id)['data']['events'][-1]['event_type'] == 'TASK_USABILITY_CHANGED'


def test_persisted_expiry_stays_unusable_after_clock_moves_back(system):
    _, task_id, _, _, _ = decide(system)
    manager, runtime, clock = (system[name] for name in ('manager', 'runtime', 'clock'))
    clock.advance(30)
    runtime.recover_expired()
    revision = snapshot(manager, task_id)['version']
    clock.advance(-10)
    assert snapshot(manager, task_id)['usage_state'] == summary(manager, task_id)['usage_state'] == 'REVIEW_REQUIRED'
    assert snapshot(manager, task_id)['version'] == revision


def test_unpersisted_approved_result_fails_closed_on_clock_rollback_before_decision(system):
    _, task_id, _, _, _ = decide(system)
    system['clock'].advance(-1)
    for read in (lambda: snapshot(system['manager'], task_id), lambda: summary(system['manager'], task_id)):
        with pytest.raises(TaskError, match='^CLOCK_UNTRUSTED$'):
            read()


def test_evidence_expiry_and_revocation_preserve_rejected_usage_state(system):
    _, task_id, _, _, rejected = decide(system, decision='REJECT_RESULT')
    manager, runtime, repo = (system[name] for name in ('manager', 'runtime', 'repo'))
    assert snapshot(manager, task_id)['usage_state'] == 'UNUSABLE'
    system['clock'].advance(30)
    assert runtime.recover_expired() == 0
    assert runtime.revoke_frozen_fixture('retired after expiry') == 1
    assert snapshot(manager, task_id)['usage_state'] == summary(manager, task_id)['usage_state'] == 'UNUSABLE'
    stored = repo.read(lambda db: json.loads(db.execute('SELECT snapshot_json FROM tm_tasks').fetchone()[0]))
    assert (stored['state'], stored['usage_state'], stored['version']) == (
        'REJECTED', 'UNUSABLE', rejected['task_version'] + 2)
    events = manager.events(task_id)['data']['events']
    assert [row['event_type'] for row in events[-3:]] == ['RESULT_DECIDED', 'EVIDENCE_INVALIDATED', 'EVIDENCE_INVALIDATED']
    assert repo.check_integrity()


@pytest.mark.parametrize('legacy_state', ['REJECTED', 'COMPLETED'])
def test_reads_existing_b7_invalidation_without_rewriting_history(system, monkeypatch, legacy_state):
    _, task_id, _, _, _ = decide(system, decision='REJECT_RESULT' if legacy_state == 'REJECTED' else 'APPROVE_RESULT',
                                  expires=False)
    manager, repo, runtime = (system[name] for name in ('manager', 'repo', 'runtime'))
    save = repo.save

    def save_b7(db, previous, updated, **kwargs):
        kwargs['event_type'] = 'EVIDENCE_INVALIDATED'
        return save(db, previous, replace(updated, usage_state='REVIEW_REQUIRED'), **kwargs)

    with monkeypatch.context() as override:
        override.setattr(repo, 'save', save_b7)
        assert runtime.revoke_frozen_fixture('legacy invalidation') == 1
    saved = repo.path.read_bytes()
    task = snapshot(manager, task_id)
    expected = 'UNUSABLE' if legacy_state == 'REJECTED' else 'REVIEW_REQUIRED'
    assert (task['state'], task['usage_state'], summary(manager, task_id)['usage_state']) == (
        legacy_state, expected, expected)
    assert manager.events(task_id)['data']['events'][-1]['event_type'] == 'EVIDENCE_INVALIDATED'
    assert saved == repo.path.read_bytes() and repo.check_integrity()


def test_coordinator_rolls_back_expiry_marker_link_and_usability_event_together(system, monkeypatch):
    _, task_id, _, _, decision = decide(system)
    repo, runtime = system['repo'], system['runtime']
    saved = repo.path.read_bytes()
    system['clock'].advance(30)
    save = repo.save

    def interrupted(*args, **kwargs):
        save(*args, **kwargs)
        raise RuntimeError('fixture stopped before commit')

    with monkeypatch.context() as override:
        override.setattr(repo, 'save', interrupted)
        with pytest.raises(RuntimeError, match='fixture stopped before commit'):
            runtime.recover_expired()
    assert saved == repo.path.read_bytes()
    task = snapshot(system['manager'], task_id)
    assert (task['usage_state'], task['version']) == ('REVIEW_REQUIRED', decision['task_version'])
    assert runtime.recover_expired() == 0
    assert snapshot(system['manager'], task_id)['version'] == decision['task_version'] + 1
    assert repo.check_integrity()


def test_concurrent_maintenance_does_not_duplicate_the_usability_event(system):
    _, task_id, _, _, decision = decide(system)
    system['clock'].advance(30)
    with ThreadPoolExecutor(max_workers=2) as pool:
        recovered = list(pool.map(lambda _: system['runtime'].recover_expired(), range(2)))
    assert recovered == [0, 0]
    assert snapshot(system['manager'], task_id)['version'] == decision['task_version'] + 1
    assert [event['event_type'] for event in system['manager'].events(task_id)['data']['events']].count(
        'TASK_USABILITY_CHANGED') == 1
