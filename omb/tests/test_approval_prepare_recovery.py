from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest

from aars_task_manager.approval_transactions import ResultDecisionStore
from aars_task_manager.domain import new_id, stamp
from aars_task_manager.errors import TaskError
from aars_task_manager.runtime import TaskRuntime
from tests.support import key
from tests.test_approval_receipts import fixture_signature
from tests.test_approval_transactions import challenge_fields, counts, issue, setup


def prepare(store, review, idem, decision='APPROVE_RESULT'):
    return store.prepare(review['task_id'], expected_version=review['subject_version'],
                         idempotency_key=idem, decision=decision)


def test_retry_recovers_nonce_and_deadline_without_writing(system):
    store, review, _ = setup(system)
    idem = key()
    first = prepare(store, review, idem)
    repo = system['repo']
    original = repo.path.read_bytes()
    before = counts(repo)
    system['clock'].advance(5)
    assert prepare(store, review, idem) == first
    assert counts(repo) == before == (1, 0, review['subject_version'], review['subject_version'])
    assert repo.path.read_bytes() == original
    nonce = first[1]
    assert len(nonce) == 64
    assert bytes.fromhex(nonce) not in original and nonce.encode() not in original
    assert store._preparation_key not in original


def test_retry_after_response_loss_can_sign_and_commit(system, monkeypatch):
    store, review, signer = setup(system)
    repo = system['repo']
    write = repo.write
    lost = []

    def lose_response(fn):
        lost.append(write(fn))
        raise OSError('fixture transport interrupted after commit')

    idem = key()
    with monkeypatch.context() as patch:
        patch.setattr(repo, 'write', lose_response)
        with pytest.raises(OSError, match='interrupted after commit'):
            prepare(store, review, idem)
    challenge, nonce = prepare(store, review, idem)
    assert (challenge, nonce) == lost[0]
    raw = fixture_signature(signer, challenge_fields(challenge, nonce))
    assert not store.submit(raw, idempotency_key=idem)['replayed']
    assert counts(repo)[:2] == (1, 1)


def test_concurrent_prepare_with_same_key_returns_one_challenge(system):
    store, review, _ = setup(system)
    idem = key()
    barrier = Barrier(2)

    def concurrent_prepare():
        barrier.wait(timeout=5)
        return prepare(store, review, idem)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = [pool.submit(concurrent_prepare) for _ in range(2)]
        assert first.result(timeout=6) == second.result(timeout=6)
    assert counts(system['repo'])[:2] == (1, 0)


@pytest.mark.parametrize('field', ['task_id', 'subject_version', 'decision'])
def test_same_key_rejects_changed_request(system, field):
    store, review, _ = setup(system)
    idem = key()
    prepare(store, review, idem)
    other = dict(review)
    decision = 'APPROVE_RESULT'
    if field == 'decision':
        decision = 'REJECT_RESULT'
    elif field == 'task_id':
        other[field] = new_id('task')
    else:
        other[field] += 1
    with pytest.raises(TaskError, match='^IDEMPOTENCY_CONFLICT$'):
        prepare(store, other, idem, decision)
    assert counts(system['repo'])[:2] == (1, 0)


def test_distinct_idempotency_keys_produce_distinct_nonces(system):
    store, review, _ = setup(system)
    a, b = (prepare(store, review, key()) for _ in range(2))
    assert a[1] != b[1] and a[0].nonce_hash != b[0].nonce_hash
    assert counts(system['repo'])[:2] == (2, 0)


@pytest.mark.parametrize('clock,code', [
    ('wall-expired', 'APPROVAL_CHALLENGE_EXPIRED'),
    ('monotonic-expired', 'APPROVAL_CHALLENGE_EXPIRED'),
    ('monotonic-rollback', 'APPROVAL_CLOCK_UNTRUSTED'),
])
def test_retry_cannot_extend_deadline_or_roll_back_clock(system, monkeypatch, clock, code):
    store, review, _ = setup(system)
    idem = key()
    challenge, _ = prepare(store, review, idem)
    if clock == 'wall-expired':
        system['clock'].advance(120)
    elif clock == 'monotonic-expired':
        system['clock'].advance(117)
        monkeypatch.setattr(store, 'monotonic_now', lambda: challenge.issued_monotonic + 120)
    else:
        monkeypatch.setattr(store, 'monotonic_now', lambda: challenge.issued_monotonic - 1)
    with pytest.raises(TaskError, match='^' + code + '$'):
        prepare(store, review, idem)
    assert counts(system['repo'])[:2] == (1, 0)


def test_retry_cannot_recover_nonce_after_consumption(system):
    store, review, signer = setup(system)
    idem, _, raw = issue(store, review, signer)
    committed = store.submit(raw, idempotency_key=idem)
    with pytest.raises(TaskError, match='^APPROVAL_CHALLENGE_CONSUMED$'):
        prepare(store, review, idem)
    assert store.submit(raw, idempotency_key=idem) == {**committed, 'replayed': True}


@pytest.mark.parametrize('same_boot', [True, False])
def test_retry_requires_the_issuing_store_and_a_live_boot(system, same_boot):
    store, review, _ = setup(system)
    idem = key()
    prepare(store, review, idem)
    repo = system['repo']

    def assert_expired(boot):
        replacement = ResultDecisionStore(repo, boot_id=boot, operator_id=store.operator_id,
                                          now=store.now, monotonic_now=store.monotonic_now)
        with pytest.raises(TaskError, match='^APPROVAL_CHALLENGE_EXPIRED$'):
            prepare(replacement, review, idem)

    if same_boot:
        assert_expired(store.boot_id)
    else:
        system['runtime'].close()
        with TaskRuntime(repo, clock=system['clock']) as runtime:
            assert_expired(runtime.boot_id)
    assert counts(repo)[:2] == (1, 0)


@pytest.mark.parametrize('change,code', [
    ('revoke', 'REVIEW_STALE'),
    ('binding', 'REVIEW_STALE'),
    ('instance', 'REVIEW_STALE'),
    ('operator', 'APPROVAL_KEY_UNTRUSTED'),
    ('challenge-history', 'APPROVAL_CHALLENGE_EXPIRED'),
])
def test_retry_rechecks_trusted_context_and_committed_metadata(system, change, code):
    store, review, _ = setup(system)
    idem = key()
    prepare(store, review, idem)
    repo = system['repo']
    if change == 'revoke':
        system['runtime'].revoke_frozen_fixture('fixture retired')
    elif change == 'binding':
        repo.write(lambda db: db.execute("UPDATE principals SET binding_version=binding_version+1 WHERE kind='BOT'"))
    elif change == 'instance':
        repo.write(lambda db: db.execute('UPDATE workspaces SET db_instance_id=?', (new_id('db'),)))
    elif change == 'operator':
        repo.write(lambda db: db.execute('UPDATE result_operator_pins SET active=0'))
    else:
        changed_expiry = stamp(system['clock'].now() + timedelta(seconds=119))
        repo.write(lambda db: db.execute('UPDATE result_approval_challenges SET expires_at=?', (changed_expiry,)))
    with pytest.raises(TaskError, match='^' + code + '$'):
        prepare(store, review, idem)
    assert counts(repo)[:2] == (1, 0)
