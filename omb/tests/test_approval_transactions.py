from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from hashlib import sha256
import sqlite3
from threading import Barrier

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import pytest

from aars_task_manager.approval_enrollment import EnrollmentAnchor
from aars_task_manager.approval_receipts import DOMAIN
from aars_task_manager.approval_transactions import ResultDecisionStore
from aars_task_manager.domain import new_id
from aars_task_manager.errors import TaskError
from aars_task_manager.migration import migrate_d3_copy
from aars_task_manager.runtime import TaskRuntime
from aars_task_manager.storage import Repository, expected_schema_hash
from tests.support import key
from tests.test_approval_receipts import fixture_signature
from tests.test_review_gate import prepared


def setup(system, *, operator=None, expires_at=None):
    repo, runtime, clock = (system[name] for name in ('repo', 'runtime', 'clock'))
    args = prepared(system, expires_at=expires_at)
    review = system['manager'].execute('review_request', args)['data']['review']
    signer = ec.generate_private_key(ec.SECP256R1())
    point = signer.public_key().public_bytes(serialization.Encoding.X962,
                                            serialization.PublicFormat.UncompressedPoint)
    operator = operator or new_id('principal')
    ws, instance = repo.read(lambda db: tuple(db.execute(
        'SELECT workspace_id,db_instance_id FROM workspaces').fetchone()))
    anchor = EnrollmentAnchor(ws, instance, operator, 'fixture-key', 'sha256:' + sha256(point).hexdigest())
    # Explicit fixture pin. Production enrollment remains inactive.
    repo.write(lambda db: db.execute('INSERT INTO result_operator_pins VALUES (?,?,?,?,?,?)',
        (ws, operator, anchor.key_id, point, anchor.pin_sha256, 1)))
    start = clock.now()
    store = ResultDecisionStore(repo, boot_id=runtime.boot_id, anchor=anchor, now=clock.now,
                                monotonic_now=lambda: 100 + (clock.now() - start).total_seconds())
    return store, review, signer


def challenge_fields(challenge, nonce):
    fields = asdict(challenge.subject)
    fields.pop('review_expires_at')
    fields.update(domain=DOMAIN, decision=challenge.decision, control_action=None, reason='测试决定',
                  nonce=nonce, issued_at=challenge.issued_at, expires_at=challenge.expires_at,
                  key_id=challenge.key_id, algorithm='ECDSA_P256_SHA256_DER')
    return fields


def issue(store, review, signer, decision='APPROVE_RESULT'):
    idem = key()
    challenge, nonce = store.prepare(review['task_id'], expected_version=review['subject_version'],
                                    idempotency_key=idem, decision=decision)
    fields = challenge_fields(challenge, nonce)
    return idem, fields, fixture_signature(signer, fields)


def counts(repo):
    return repo.read(lambda db: tuple(db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] for table in
        ('result_approval_challenges', 'result_approval_decisions', 'task_events', 'task_revisions')))


@pytest.mark.parametrize('decision,dest,usage', [
    ('APPROVE_RESULT', 'COMPLETED', 'USABLE'),
    ('REJECT_RESULT', 'REJECTED', 'UNUSABLE'),
    ('REQUEST_CHANGES', 'READY', 'REVIEW_REQUIRED'),
])
def test_decision_commits_exactly_one_event_and_consumes_nonce(system, decision, dest, usage):
    store, review, signer = setup(system)
    idem, fields, raw = issue(store, review, signer, decision)
    repo = system['repo']
    before = counts(repo)
    result = store.submit(raw, idempotency_key=idem)
    task = system['manager'].get(review['task_id'])['data']['task']
    assert (task['state'], task['usage_state'], task['version']) == (dest, usage, review['subject_version'] + 1)
    assert result['task_version'] == task['version'] and not result['replayed']
    assert counts(repo) == (before[0], before[1] + 1, before[2] + 1, before[3] + 1)
    assert repo.check_integrity()
    assert fields['nonce'].encode() not in repo.path.read_bytes()


def test_signed_same_statement_replays_and_different_statement_conflicts(system):
    store, review, signer = setup(system)
    idem, fields, raw = issue(store, review, signer)
    first = store.submit(raw, idempotency_key=idem)
    after = counts(system['repo'])
    second = store.submit(fixture_signature(signer, fields), idempotency_key=idem)
    assert second == {**first, 'replayed': True}
    with pytest.raises(TaskError, match='^IDEMPOTENCY_CONFLICT$'):
        store.submit(fixture_signature(signer, {**fields, 'reason': '修改后的理由'}), idempotency_key=idem)
    with pytest.raises(TaskError, match='^APPROVAL_INVALID_SIGNATURE$'):
        store.submit(fixture_signature(ec.generate_private_key(ec.SECP256R1()), fields), idempotency_key=idem)
    assert counts(system['repo']) == after


def test_nonce_cannot_be_used_with_another_idempotency_key(system):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    other, _, _ = issue(store, review, signer)
    with pytest.raises(TaskError, match='^APPROVAL_CHALLENGE_MISMATCH$'):
        store.submit(raw, idempotency_key=other)
    store.submit(raw, idempotency_key=idem)
    with pytest.raises(TaskError, match='^REVIEW_STALE$'):
        store.submit(raw, idempotency_key=other)
    assert counts(system['repo'])[:2] == (2, 1)


@pytest.mark.parametrize('same_challenge', [True, False])
def test_parallel_submissions_only_commit_one_decision(system, same_challenge):
    store, review, signer = setup(system)
    key_a, _, raw_a = issue(store, review, signer)
    key_b, _, raw_b = (key_a, None, raw_a) if same_challenge else issue(store, review, signer, 'REJECT_RESULT')
    barrier = Barrier(2)

    def submit(idem, raw):
        barrier.wait(timeout=5)
        try:
            return 'REPLAY' if store.submit(raw, idempotency_key=idem)['replayed'] else 'COMMITTED'
        except TaskError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(submit, idem, raw) for idem, raw in ((key_a, raw_a), (key_b, raw_b))]
        assert sorted(item.result(timeout=6) for item in results) == [
            'COMMITTED', 'REPLAY' if same_challenge else 'REVIEW_STALE']
    assert counts(system['repo'])[1] == 1
    assert system['repo'].check_integrity()


def test_failure_after_task_write_rolls_back_everything_and_retry_succeeds(system, monkeypatch):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    repo = system['repo']
    before = counts(repo)
    original = repo.save

    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('fixture rollback')

    with monkeypatch.context() as patch:
        patch.setattr(repo, 'save', fail_after_write)
        with pytest.raises(RuntimeError, match='fixture rollback'):
            store.submit(raw, idempotency_key=idem)
    assert counts(repo) == before
    assert system['manager'].get(review['task_id'])['data']['task']['state'] == 'REVIEW_PENDING'
    assert not store.submit(raw, idempotency_key=idem)['replayed']


@pytest.mark.parametrize('change,code', [
    ('revoked', 'REVIEW_STALE'),
    ('expired', 'REVIEW_STALE'),
    ('binding', 'REVIEW_STALE'),
    ('policy', 'REVIEW_STALE'),
    ('database', 'APPROVAL_CONTEXT_STALE'),
    ('disabled-pin', 'APPROVAL_KEY_UNTRUSTED'),
    ('rotated-pin', 'APPROVAL_KEY_UNTRUSTED'),
])
def test_context_changes_leave_challenge_unconsumed(system, change, code):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    repo = system['repo']
    sql = {
        'binding': "UPDATE principals SET binding_version=binding_version+1 WHERE kind='BOT'",
        'policy': 'UPDATE workspaces SET policy_version=policy_version+1',
        'database': "UPDATE workspaces SET db_instance_id='db." + "0"*32 + "'",
        'disabled-pin': 'UPDATE result_operator_pins SET active=0',
    }
    if change == 'revoked':
        system['runtime'].revoke_frozen_fixture('fixture retired')
    elif change == 'expired':
        system['clock'].advance(120)
    elif change == 'rotated-pin':
        point = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        repo.write(lambda db: db.execute('UPDATE result_operator_pins SET public_point=?,pin_sha256=?',
                                         (point, 'sha256:' + sha256(point).hexdigest())))
    else:
        repo.write(lambda db: db.execute(sql[change]))
    before = counts(repo)
    with pytest.raises(TaskError, match='^' + code + '$'):
        store.submit(raw, idempotency_key=idem)
    assert counts(repo) == before and before[1] == 0


def test_time_is_rechecked_after_signature_verification(system, monkeypatch):
    from aars_task_manager import approval_receipts

    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    original = approval_receipts._verify_signature

    def advance_time(*args):
        verified = original(*args)
        system['clock'].advance(121)
        return verified

    monkeypatch.setattr(approval_receipts, '_verify_signature', advance_time)
    with pytest.raises(TaskError, match='^APPROVAL_CHALLENGE_EXPIRED$'):
        store.submit(raw, idempotency_key=idem)
    assert counts(system['repo'])[:2] == (1, 0)


def test_pending_challenge_expires_across_boot(system):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    system['runtime'].close()
    with pytest.raises(TaskError, match='^RUNTIME_INACTIVE$'):
        store.submit(raw, idempotency_key=idem)
    with TaskRuntime(system['repo'], clock=system['clock']) as current:
        new = ResultDecisionStore(system['repo'], boot_id=current.boot_id, anchor=store.anchor,
                                  now=store.now, monotonic_now=store.monotonic_now)
        with pytest.raises(TaskError, match='^APPROVAL_CONTEXT_STALE$'):
            new.submit(raw, idempotency_key=idem)
        task = current.manager(system['bindings'][0].binding_id).get(review['task_id'])['data']['task']
        assert task['state'] == 'PAUSED'
    assert counts(system['repo'])[:2] == (1, 0)


def test_committed_result_survives_restart_and_later_evidence_revocation(system):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    first = store.submit(raw, idempotency_key=idem)
    repo = system['repo']
    system['runtime'].close()
    with TaskRuntime(repo, clock=system['clock']) as current:
        new = ResultDecisionStore(repo, boot_id=current.boot_id, anchor=store.anchor,
                                  now=store.now, monotonic_now=store.monotonic_now)
        assert current.revoke_frozen_fixture('fixture retired') == 1
        task = current.manager(system['bindings'][0].binding_id).get(review['task_id'])['data']['task']
        assert (task['state'], task['usage_state']) == ('COMPLETED', 'REVIEW_REQUIRED')
        assert new.submit(raw, idempotency_key=idem) == {**first, 'replayed': True}
    assert repo.check_integrity()


@pytest.mark.parametrize('table,column,value', [
    ('result_approval_decisions', 'reason', 'changed historical reason'),
    ('result_approval_challenges', 'boot_id', 'boot.' + '0'*32),
])
def test_audit_rejects_modified_committed_records(system, table, column, value):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    store.submit(raw, idempotency_key=idem)
    repo = system['repo']
    with sqlite3.connect(repo.path) as db:
        db.execute(f'UPDATE {table} SET {column}=?', (value,))
    with pytest.raises(TaskError, match='^INTEGRITY_FAILURE$'):
        repo.check_integrity()
    assert repo.quarantined


def test_cannot_prepare_using_bot_identity_even_if_pin_row_exists(system):
    bot = system['bindings'][0].principal_id
    store, review, _ = setup(system, operator=bot)
    with pytest.raises(TaskError, match='^APPROVAL_KEY_UNTRUSTED$'):
        store.prepare(review['task_id'], expected_version=review['subject_version'],
                      idempotency_key=key(), decision='APPROVE_RESULT')
    assert counts(system['repo'])[:2] == (0, 0)


def test_prepare_rejects_wrong_version_and_keeps_existing_challenge(system):
    store, review, signer = setup(system)
    with pytest.raises(TaskError, match='^VERSION_CONFLICT$'):
        store.prepare(review['task_id'], expected_version=review['subject_version'] + 1,
                      idempotency_key=key(), decision='APPROVE_RESULT')
    idem, _, _ = issue(store, review, signer)
    with pytest.raises(TaskError, match='^IDEMPOTENCY_CONFLICT$'):
        store.prepare(review['task_id'], expected_version=review['subject_version'],
                      idempotency_key=idem, decision='REJECT_RESULT')
    assert counts(system['repo'])[:2] == (1, 0)


def test_d3_migration_preserves_previous_history_and_does_not_touch_source(system, tmp_path):
    repo, runtime = system['repo'], system['runtime']
    args = prepared(system)
    review = system['manager'].execute('review_request', args)['data']['review']
    runtime.close()
    with sqlite3.connect(repo.path) as db:
        for table in ('result_approval_decisions', 'result_approval_challenges', 'result_operator_pins'):
            db.execute(f'DROP TABLE {table}')
        db.execute('PRAGMA user_version=3')
        db.execute("UPDATE meta SET value=? WHERE key='schema_hash'", (expected_schema_hash(3),))
    old_bytes = repo.path.read_bytes()
    target = tmp_path / 'migrated'
    target.mkdir(mode=0o700)
    copied = migrate_d3_copy(repo.path, target/'tasks.sqlite', source_root=repo.root, target_root=target,
                             protected_roots=(system['protected'],))
    assert repo.path.read_bytes() == old_bytes and copied.check_integrity()
    assert counts(copied)[:2] == (0, 0)
    reopened = Repository.open(copied.path, allowed_root=target, protected_roots=(system['protected'],))
    with TaskRuntime(reopened, clock=system['clock']) as current:
        task = current.manager(system['bindings'][0].binding_id).get(review['task_id'])['data']['task']
        assert task['state'] == 'PAUSED' and task['version'] == review['subject_version'] + 1
