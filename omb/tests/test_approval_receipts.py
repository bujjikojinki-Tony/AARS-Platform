from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
import pytest

from aars_task_manager.approval_receipts import (DOMAIN, PinnedKey, ReceiptChallenge, ResultSubject,
    result_subject_from_host, verify_result_receipt)
from aars_task_manager.domain import canonical, new_id, stamp
from aars_task_manager.errors import TaskError
from tests.test_review_gate import prepared


def fixture_signature(private_key, fields):
    # This test signer uses a transient software key. It is absent from the host runtime.
    statement = {name: value for name, value in fields.items() if name != 'signature_base64'}
    payload = (DOMAIN + '\n' + canonical(statement)).encode('utf-8')
    der = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    return canonical({**statement, 'signature_base64': base64.b64encode(der).decode('ascii')}).encode('utf-8')


def fixture_setup(subject=None, *, start=None, boot_id=None, decision='APPROVE_RESULT', reason='同意。含 Unicode 和斜杠 /。'):
    start = start or datetime(2026, 11, 27, 12, tzinfo=timezone.utc)
    boot_id = boot_id or new_id('boot')
    if subject is None:
        subject = ResultSubject(new_id('workspace'),new_id('db'),new_id('task'),new_id('review'),
            9,'sha256:'+'3'*64,'sha256:'+'a'*64,'LOCAL_SYNTHETIC_VALIDATION',4,5,'sha256:'+'c'*64,
            stamp(start + timedelta(seconds=120)))
    signing = ec.generate_private_key(ec.SECP256R1())
    public = signing.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    pin = PinnedKey('fixture-key',public,'sha256:'+hashlib.sha256(public).hexdigest())
    # Test-only placeholder, unrelated to any live challenge or operator account.
    nonce = bytes(range(32))
    challenge = ReceiptChallenge(subject,boot_id,'sha256:'+hashlib.sha256(nonce).hexdigest(),pin.key_id,
                                 decision,stamp(start),stamp(start+timedelta(seconds=90)),100.0)
    body = asdict(subject);body.pop('review_expires_at')
    body.update(domain=DOMAIN, decision=decision, control_action=None, reason=reason,
        nonce=nonce.hex(), issued_at=challenge.issued_at,expires_at=challenge.expires_at,
        key_id=pin.key_id,algorithm='ECDSA_P256_SHA256_DER')
    params = dict(current_subject=subject,challenge=challenge,pinned_key=pin,boot_id=boot_id,
                  now=start+timedelta(seconds=2),monotonic_now=102.0)
    return signing, body, params


@pytest.mark.parametrize('decision', ['APPROVE_RESULT','REJECT_RESULT','REQUEST_CHANGES'])
def test_accepts_signed_statement_shape_without_runtime_approval(decision):
    signing, body, params = fixture_setup(decision=decision)
    raw = fixture_signature(signing,body)
    verified = verify_result_receipt(raw,**params)
    assert verified.decision == decision and verified.review_id == body['review_id']
    assert verified.statement_sha256 != verified.receipt_sha256


@pytest.mark.parametrize('field,value', [
    ('workspace_id','workspace.'+'1'*32),('db_instance_id','db.'+'2'*32),('task_id','task.'+'3'*32),
    ('review_id','review.'+'4'*32),('subject_version',10),('definition_hash','sha256:'+'5'*64),
    ('evidence_set_hash','sha256:'+'6'*64),('policy_version',6),('binding_version',7),
    ('authorization_scope_hash','sha256:'+'7'*64)])
def test_even_correctly_signed_receipt_cannot_cross_snapshot_boundary(field,value):
    signing, body, params = fixture_setup()
    with pytest.raises(TaskError, match='^APPROVAL_CONTEXT_STALE$'):
        verify_result_receipt(fixture_signature(signing,{**body,field:value}),**params)


@pytest.mark.parametrize('field,value,code', [
    ('purpose','CATALOG_METADATA','PURPOSE_NOT_EXECUTABLE'),
    ('nonce','ff'*32,'APPROVAL_CHALLENGE_MISMATCH'),
    ('nonce',bytes(range(32)).hex()+'\n','APPROVAL_INVALID_RECEIPT'),
    ('decision','REQUEST_CHANGES','APPROVAL_CHALLENGE_MISMATCH'),
    ('decision','APPROVE_PLAN','APPROVAL_DECISION_UNSUPPORTED'),
    ('control_action','cancel','APPROVAL_DECISION_UNSUPPORTED'),
    ('key_id','other-key','APPROVAL_KEY_UNTRUSTED'),
    ('subject_version',9.0,'APPROVAL_INVALID_RECEIPT'),
    ('binding_version',True,'APPROVAL_INVALID_RECEIPT'),
    ('operator','user','APPROVAL_INVALID_RECEIPT'),
    ('domain','wrong-domain','APPROVAL_INVALID_RECEIPT'),
    ('algorithm','ECDSA_P384_SHA384','APPROVAL_INVALID_RECEIPT'),
])
def test_strict_fields(field,value,code):
    signing, body, params = fixture_setup()
    with pytest.raises(TaskError, match='^'+code+'$'):
        verify_result_receipt(fixture_signature(signing,{**body,field:value}),**params)


@pytest.mark.parametrize('bad', ['tampered-text','other-signer','wrong-pin','der-trailing','invalid-base64','duplicate-field','too-large'])
def test_signature_pin_and_parser_fail_closed(bad):
    signing, body, params = fixture_setup()
    valid = fixture_signature(signing,body)
    data = json.loads(valid)
    code = 'APPROVAL_INVALID_SIGNATURE'
    if bad == 'tampered-text':
        data['reason'] = 'Modified after signing'
    elif bad == 'other-signer':
        data = json.loads(fixture_signature(ec.generate_private_key(ec.SECP256R1()),body))
    elif bad == 'wrong-pin':
        params['pinned_key'] = replace(params['pinned_key'],sha256='sha256:'+'0'*64)
        code = 'APPROVAL_KEY_UNTRUSTED'
    elif bad == 'der-trailing':
        data['signature_base64'] = base64.b64encode(base64.b64decode(data['signature_base64'])+b'\x00').decode()
    elif bad == 'invalid-base64':
        data['signature_base64'] = '*'*96
    raw = canonical(data).encode()
    if bad in {'duplicate-field','too-large'}:
        code = 'APPROVAL_INVALID_RECEIPT'
        raw = (b'{"decision":"APPROVE_RESULT",'+raw[1:] if bad=='duplicate-field' else b' '*16384+raw)
    with pytest.raises(TaskError, match='^'+code+'$'):
        verify_result_receipt(raw,**params)


@pytest.mark.parametrize('wall,monotonic,code', [(90,190,'APPROVAL_CHALLENGE_EXPIRED'),
    (87,190,'APPROVAL_CHALLENGE_EXPIRED'),(-1,101,'APPROVAL_CLOCK_UNTRUSTED'),
    (44,102,'APPROVAL_CLOCK_UNTRUSTED'),(2,99,'APPROVAL_CLOCK_UNTRUSTED')])
def test_both_clocks_enforce_expiry_and_reject_rollback(wall,monotonic,code):
    signing, body, params = fixture_setup()
    params.update(now=datetime(2026,11,27,12,tzinfo=timezone.utc)+timedelta(seconds=wall),monotonic_now=monotonic)
    with pytest.raises(TaskError,match='^'+code+'$'):
        verify_result_receipt(fixture_signature(signing,body),**params)


def test_new_boot_cannot_reuse_old_challenge():
    signing, body, params = fixture_setup()
    params['boot_id'] = new_id('boot')
    with pytest.raises(TaskError, match='APPROVAL_CONTEXT_STALE'):
        verify_result_receipt(fixture_signature(signing,body),**params)


def test_challenge_cannot_extend_past_review_expiry():
    signing, body, params = fixture_setup()
    short = replace(params['current_subject'],review_expires_at='2026-11-27T12:00:01.000000Z')
    params.update(current_subject=short,challenge=replace(params['challenge'],subject=short))
    with pytest.raises(TaskError,match='APPROVAL_CLOCK_UNTRUSTED'):
        verify_result_receipt(fixture_signature(signing,body),**params)


def test_reject_result_requires_human_reason():
    signing, body, params = fixture_setup(decision='REJECT_RESULT',reason='   ')
    with pytest.raises(TaskError,match='APPROVAL_INVALID_RECEIPT'):
        verify_result_receipt(fixture_signature(signing,body),**params)


def test_live_review_snapshot_and_revocation_never_operationally_approve(system):
    manager = system['manager'];runtime = system['runtime'];repository = system['repo']
    args = prepared(system)
    review = manager.execute('review_request',args)['data']['review']
    subject = result_subject_from_host(repository,args['task_id'],boot_id=runtime.boot_id,now=runtime.clock.now())
    assert subject.review_id == review['review_id'] and subject.evidence_set_hash == review['evidence_set_hash']
    signing, body, params = fixture_setup(subject,start=runtime.clock.now(),boot_id=runtime.boot_id)
    verified = verify_result_receipt(fixture_signature(signing,body),**params)
    assert verified.decision == 'APPROVE_RESULT'
    with pytest.raises(TaskError,match='APPROVAL_LOCKED'):
        manager.execute('submit_receipt',{'task_id':args['task_id'],'statement_sha256':verified.statement_sha256})
    assert manager.get(args['task_id'])['data']['task']['state']=='REVIEW_PENDING'
    assert runtime.revoke_frozen_fixture('fixture retired')==1
    with pytest.raises(TaskError,match='REVIEW_STALE'):
        result_subject_from_host(repository,args['task_id'],boot_id=runtime.boot_id,now=runtime.clock.now())


def test_cloned_database_instance_cannot_reuse_pending_subject(system):
    manager = system['manager']; runtime = system['runtime']; repository = system['repo']
    args = prepared(system)
    manager.execute('review_request', args)
    repository.write(lambda db: db.execute('UPDATE workspaces SET db_instance_id=?', (new_id('db'),)))
    with pytest.raises(TaskError, match='^REVIEW_STALE$'):
        result_subject_from_host(repository, args['task_id'], boot_id=runtime.boot_id, now=runtime.clock.now())


def test_identity_for_retries_uses_signed_statement_instead_of_der_bytes():
    signing, body, params = fixture_setup()
    first = verify_result_receipt(fixture_signature(signing, body), **params)
    second = verify_result_receipt(fixture_signature(signing, body), **params)
    assert first.statement_sha256 == second.statement_sha256
