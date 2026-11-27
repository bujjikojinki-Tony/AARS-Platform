from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import sqlite3

import pytest

from aars_task_manager import State, TaskError, TaskRuntime
from aars_task_manager.domain import stamp
from aars_task_manager.mcp_server import ToolAdapter
from tests.support import create, key, seed_precondition


def request_args(task, attempt):
    return {'task_id': task['task_id'], 'expected_version': task['version'],
            'idempotency_key': key(), 'attempt_id': attempt['attempt_id'],
            'fencing_token': attempt['fencing_token']}


def prepared(system, *, expires_at=None):
    runtime = system['runtime']; manager = system['manager']
    source = runtime.register_frozen_fixture(expires_at=expires_at)
    task, attempt = seed_precondition(system['repo'], manager, State.RUNNING, system['clock'])
    linked = manager.execute('evidence_link', {**request_args(task, attempt), 'snapshot_id': source['evidence_snapshot_id']})
    return request_args(linked['data']['task'], attempt)


def test_review_request_through_mcp_contract_keeps_approval_locked(system):
    m = system['manager']; args = prepared(system)
    tool = ToolAdapter(m)
    result = tool.call('aars_task_review_request_v1', args)
    assert result['ok'] and result['execution_authorized'] is False
    review = result['data']['review']; task = result['data']['task']
    assert task['state'] == 'REVIEW_PENDING' and review['status'] == 'PENDING'
    assert task['version'] == review['subject_version']
    assert review['evidence_set_hash'] == m.evidence_trace(task['task_id'])['evidence_set_hash']
    assert 'nonce' not in review and 'signature_base64' not in review
    assert m.get(task['task_id'])['data']['review'] == review
    assert m.execute('review_request', args)['replayed']
    for op in ['approve_result', 'prepare_challenge', 'submit_receipt']:
        with pytest.raises(TaskError, match='APPROVAL_LOCKED'):
            m.execute(op, {'task_id': task['task_id']})
    assert system['repo'].check_integrity()


def test_review_requires_verified_evidence_and_valid_lease(system):
    m = system['manager']; t, a = seed_precondition(system['repo'], m, State.RUNNING, system['clock'])
    args = request_args(t, a)
    with pytest.raises(TaskError, match='FENCING_CONFLICT'):
        m.execute('review_request', {**args, 'fencing_token': a['fencing_token'] + 1})
    with pytest.raises(TaskError, match='EVIDENCE_UNUSABLE'):
        m.execute('review_request', args)
    assert m.get(t['task_id'])['data']['task']['version'] == t['version']


def test_review_rejects_cross_bot_access(system):
    args = prepared(system)
    with pytest.raises(TaskError, match='NOT_FOUND_OR_FORBIDDEN'):
        system['other'].execute('review_request', args)


def test_concurrent_review_requests_create_one_record(system):
    m = system['manager']; args = prepared(system)
    def submit(i):
        try:
            return m.execute('review_request', {**args, 'idempotency_key': key()})['data']['review']['review_id']
        except TaskError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(4)))
    assert sum(value.startswith('review.') for value in results) == 1
    assert results.count('VERSION_CONFLICT') == 3


def test_review_locks_mutations_and_expires(system):
    m = system['manager']; args = prepared(system)
    result = m.execute('review_request', args)['data']
    with pytest.raises(TaskError, match='REVIEW_LOCKED'):
        m.execute('transition', {'task_id': args['task_id'], 'expected_version': result['task']['version'],
                                 'idempotency_key': key(), 'action': 'cancel', 'reason': 'Bot cannot cancel pending review'})
    system['clock'].advance(120)
    assert m.get(args['task_id'])['data']['review']['status'] == 'EXPIRED'
    assert system['runtime'].recover_expired() == 1
    assert m.get(args['task_id'])['data']['task']['state'] == 'PAUSED'
    with pytest.raises(TaskError, match='REVIEW_STALE'):
        m.execute('review_request', args)


def test_review_closed_by_evidence_revocation(system):
    m = system['manager']; args = prepared(system)
    m.execute('review_request', args)
    system['runtime'].revoke_frozen_fixture('synthetic grant revoked')
    assert m.get(args['task_id'])['data']['task']['state'] == 'PAUSED'
    assert system['repo'].read(lambda db:db.execute('SELECT status FROM result_review_closures').fetchone()[0]) == 'STALE'
    assert system['repo'].check_integrity()


def test_review_restart_preserves_and_closes_unconsumed_request(system):
    m = system['manager']; args = prepared(system)
    review = m.execute('review_request', args)['data']['review']
    system['runtime'].close()
    with TaskRuntime(system['repo'], clock=system['clock']) as runtime:
        assert runtime.manager(m.binding_id).get(args['task_id'])['data']['task']['state'] == 'PAUSED'
        assert system['repo'].read(lambda db:db.execute('SELECT review_id FROM result_review_closures').fetchone()[0]) == review['review_id']


def test_review_tamper_detected_before_read(system):
    m = system['manager']; args = prepared(system)
    m.execute('review_request', args)
    with sqlite3.connect(system['repo'].path) as db:
        db.execute("UPDATE result_review_requests SET record_json=json_set(record_json,'$.status','APPROVED')")
    with pytest.raises(TaskError, match='INTEGRITY_FAILURE'):
        m.get(args['task_id'])


def test_evidence_expiry_caps_review_deadline(system):
    expiry = stamp(system['clock'].now() + timedelta(seconds=30))
    args = prepared(system, expires_at=expiry)
    result = system['manager'].execute('review_request', args)
    assert result['data']['review']['expires_at'] == expiry
    system['clock'].advance(30)
    assert system['runtime'].reevaluate_evidence() == 1
    assert system['manager'].get(args['task_id'])['data']['task']['state'] == 'PAUSED'


def test_policy_change_invalidates_snapshot_before_replay(system):
    m = system['manager']; args = prepared(system)
    m.execute('review_request', args)
    system['repo'].write(lambda db:db.execute('UPDATE workspaces SET policy_version=policy_version+1'))
    with pytest.raises(TaskError, match='REVIEW_STALE'):
        m.execute('review_request', args)
    assert m.get(args['task_id'])['data']['review']['status'] == 'STALE'
    assert system['runtime'].recover_expired() == 1
    assert m.get(args['task_id'])['data']['task']['state'] == 'PAUSED'


def test_request_snapshot_and_attempt_roll_back_with_event_failure(system, monkeypatch):
    m = system['manager']; args = prepared(system)
    repo = system['repo']
    original = repo._append_event
    def fail(*args, **kwargs):
        raise RuntimeError('test transaction interruption')
    monkeypatch.setattr(repo, '_append_event', fail)
    with pytest.raises(RuntimeError, match='test transaction interruption'):
        m.execute('review_request', args)
    assert repo.read(lambda db:db.execute('SELECT count(*) FROM result_review_requests').fetchone()[0]) == 0
    assert repo.read(lambda db:db.execute('SELECT status FROM attempts WHERE attempt_id=?',(args['attempt_id'],)).fetchone()[0]) == 'RUNNING'
    assert m.get(args['task_id'])['data']['task']['version'] == args['expected_version']
    monkeypatch.setattr(repo, '_append_event', original)
    assert m.execute('review_request', args)['data']['review']['status'] == 'PENDING'
