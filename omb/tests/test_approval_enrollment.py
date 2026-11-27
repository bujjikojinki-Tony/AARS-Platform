import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
import pytest

from aars_task_manager.approval_enrollment import EnrollmentAnchor, EnrollmentStore
from aars_task_manager.approval_transactions import ResultDecisionStore
from aars_task_manager.domain import new_id
from aars_task_manager.errors import TaskError
from tests.support import key
from tests.test_approval_transactions import counts, setup


def key_fixture():
    signer = ec.generate_private_key(ec.SECP256R1())
    point = signer.public_key().public_bytes(serialization.Encoding.X962,
                                             serialization.PublicFormat.UncompressedPoint)
    return signer, point


def make_store(system, *, operator=None):
    repo = system['repo']
    ws, instance = repo.read(lambda db: tuple(db.execute(
        'SELECT workspace_id,db_instance_id FROM workspaces').fetchone()))
    signer, point = key_fixture()
    anchor = EnrollmentAnchor(ws, instance, operator or new_id('principal'), 'candidate-key',
                              'sha256:' + sha256(point).hexdigest())
    current = system['clock']
    start = current.now()
    store = EnrollmentStore(repo, boot_id=system['runtime'].boot_id, anchor=anchor, now=current.now,
                            monotonic_now=lambda: 100 + (current.now() - start).total_seconds())
    return store, signer, point


def proof(signer, challenge):
    return base64.b64encode(signer.sign(challenge.signing_bytes(), ec.ECDSA(hashes.SHA256()))).decode('ascii')


def pins(repo):
    return repo.read(lambda db: [tuple(row) for row in db.execute('SELECT * FROM result_operator_pins')])


def test_verified_proof_stages_only_an_inactive_pin_and_does_not_change_task_history(system):
    store, signer, point = make_store(system)
    anchor = store.anchor
    repo = system['repo']
    initial = counts(repo)
    challenge = store.prepare()
    signature = proof(signer, challenge)
    staged = store.stage(point, signature)
    assert staged.x963 == point and staged.sha256 == anchor.pin_sha256
    assert pins(repo) == [(anchor.workspace_id, anchor.operator_id, anchor.key_id, point, anchor.pin_sha256, 0)]
    with pytest.raises(TaskError, match='^APPROVAL_ENROLLMENT_CHALLENGE_MISSING$'):
        store.stage(point, signature)
    with pytest.raises(TaskError, match='^APPROVAL_ENROLLMENT_EXISTS$'):
        store.prepare()
    approval = ResultDecisionStore(repo, boot_id=store.boot_id, anchor=anchor,
                                   now=store.now, monotonic_now=store.monotonic_now)
    with pytest.raises(TaskError, match='^APPROVAL_KEY_UNTRUSTED$'):
        approval.prepare(new_id('task'), expected_version=1, idempotency_key=key(), decision='APPROVE_RESULT')
    assert counts(repo) == initial and repo.check_integrity()


@pytest.mark.parametrize('alteration,expected', [
    ('changed-point', 'APPROVAL_KEY_UNTRUSTED'),
    ('wrong-signer', 'APPROVAL_INVALID_SIGNATURE'),
    ('malformed-signature', 'APPROVAL_INVALID_SIGNATURE'),
    ('wrong-operator', 'APPROVAL_INVALID_SIGNATURE'),
    ('wrong-database', 'APPROVAL_INVALID_SIGNATURE'),
    ('wrong-policy', 'APPROVAL_INVALID_SIGNATURE'),
    ('wrong-domain', 'APPROVAL_INVALID_SIGNATURE'),
    ('previous-nonce', 'APPROVAL_INVALID_SIGNATURE'),
])
def test_enrollment_rejects_substituted_proofs(system, alteration, expected):
    store, signer, point = make_store(system)
    challenge = store.prepare()
    signed = proof(signer, challenge)
    if alteration == 'changed-point':
        signer2, point = key_fixture()
        signed = proof(signer2, challenge)
    elif alteration == 'wrong-signer':
        signed = proof(key_fixture()[0], challenge)
    elif alteration == 'malformed-signature':
        signed += '!'
    elif alteration == 'wrong-operator':
        anchor = replace(challenge.anchor, operator_id=new_id('principal'))
        signed = proof(signer, replace(challenge, anchor=anchor))
    elif alteration == 'wrong-database':
        anchor = replace(challenge.anchor, db_instance_id=new_id('db'))
        signed = proof(signer, replace(challenge, anchor=anchor))
    elif alteration == 'wrong-policy':
        signed = proof(signer, replace(challenge, policy_version=challenge.policy_version+1))
    elif alteration == 'wrong-domain':
        message = b'AARS-OMB-TASK-APPROVAL-V1\n' + challenge.signing_bytes().split(b'\n', 1)[1]
        signed = base64.b64encode(signer.sign(message, ec.ECDSA(hashes.SHA256()))).decode('ascii')
    else:
        assert store.prepare().nonce != challenge.nonce
    with pytest.raises(TaskError, match='^'+expected+'$'):
        store.stage(point, signed)
    assert pins(system['repo']) == []


@pytest.mark.parametrize('alteration,expected', [
    ('new-instance', 'APPROVAL_CONTEXT_STALE'),
    ('policy-updated', 'APPROVAL_CONTEXT_STALE'),
    ('lease-ended', 'RUNTIME_INACTIVE'),
    ('expired', 'APPROVAL_CHALLENGE_EXPIRED'),
    ('clock-rollback', 'APPROVAL_CLOCK_UNTRUSTED'),
])
def test_enrollment_rechecks_live_context_and_expiration(system, alteration, expected):
    store, signer, point = make_store(system)
    request = store.prepare()
    signed = proof(signer, request)
    repo = system['repo']
    if alteration == 'new-instance':
        repo.write(lambda db: db.execute('UPDATE workspaces SET db_instance_id=?', (new_id('db'),)))
    elif alteration == 'policy-updated':
        repo.write(lambda db: db.execute('UPDATE workspaces SET policy_version=policy_version+1'))
    elif alteration == 'lease-ended':
        system['runtime'].close()
    elif alteration == 'expired':
        system['clock'].advance(120)
    else:
        system['clock'].advance(-1)
    with pytest.raises(TaskError, match='^'+expected+'$'):
        store.stage(point, signed)
    assert pins(repo) == []


def test_bot_identity_cannot_be_enrolled(system):
    operator = system['bindings'][0].principal_id
    store, _, _ = make_store(system, operator=operator)
    with pytest.raises(TaskError, match='^APPROVAL_KEY_UNTRUSTED$'):
        store.prepare()
    assert pins(system['repo']) == []


def test_concurrent_staging_cannot_register_a_second_candidate(system):
    candidates = []
    for _ in range(2):
        store, signer, point = make_store(system)
        candidates.append((store, point, proof(signer, store.prepare())))

    def stage(args):
        store, point, signature = args
        try:
            store.stage(point, signature)
        except TaskError as error:
            return error.code
        return 'STAGED'

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(stage, candidates))
    assert outcomes == ['APPROVAL_ENROLLMENT_EXISTS', 'STAGED']
    assert len(pins(system['repo'])) == 1 and pins(system['repo'])[0][-1] == 0


@pytest.mark.parametrize('update_digest', [False, True])
def test_substitution_of_database_pin_cannot_issue_an_approval_challenge(system, update_digest):
    store, review, _ = setup(system)
    _, substituted = key_fixture()
    fingerprint = 'sha256:' + sha256(substituted).hexdigest() if update_digest else store.anchor.pin_sha256
    repo = system['repo']
    repo.write(lambda db: db.execute('UPDATE result_operator_pins SET public_point=?,pin_sha256=?',
                                     (substituted, fingerprint)))
    before = counts(repo)
    with pytest.raises(TaskError, match='^APPROVAL_KEY_UNTRUSTED$'):
        store.prepare(review['task_id'], expected_version=review['subject_version'],
                      idempotency_key=key(), decision='APPROVE_RESULT')
    assert counts(repo) == before
