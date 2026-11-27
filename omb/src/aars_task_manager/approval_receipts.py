"""Verify a candidate receipt against host-owned state. No approval side effects."""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, fields
from datetime import datetime
from functools import lru_cache
import hashlib
import hmac
import json
import math
import re
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from jsonschema import Draft202012Validator

from . import reviews
from .domain import canonical, parse_time, require_id, stamp, text
from .errors import TaskError

DOMAIN = 'AARS-OMB-TASK-APPROVAL-V1'
MAX_RECEIPT_BYTES = 16 * 1024
MAX_CHALLENGE_SECONDS = 120
CLOCK_SKEW_SECONDS = 5
RESULT_DECISIONS = frozenset({'APPROVE_RESULT', 'REJECT_RESULT', 'REQUEST_CHANGES'})


def _sha256(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ResultSubject:
    workspace_id: str
    db_instance_id: str
    task_id: str
    review_id: str
    subject_version: int
    definition_hash: str
    evidence_set_hash: str
    purpose: str
    policy_version: int
    binding_version: int
    authorization_scope_hash: str
    review_expires_at: str


@dataclass(frozen=True)
class ReceiptChallenge:
    """Expectation supplied by the host. The nonce itself stays off the task interface."""

    subject: ResultSubject
    boot_id: str
    nonce_hash: str
    key_id: str
    decision: str
    issued_at: str
    expires_at: str
    issued_monotonic: float


@dataclass(frozen=True)
class PinnedKey:
    """P-256 X9.63 public point and pin from the trusted enrollment channel."""

    key_id: str
    x963: bytes
    sha256: str

    def load(self) -> ec.EllipticCurvePublicKey:
        if type(self.x963) is not bytes or len(self.x963) != 65 or self.x963[0] != 4:
            raise TaskError('APPROVAL_KEY_UNTRUSTED')
        if not isinstance(self.sha256, str) or not hmac.compare_digest(self.sha256.encode(), _sha256(self.x963).encode()):
            raise TaskError('APPROVAL_KEY_UNTRUSTED')
        try:
            return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), self.x963)
        except ValueError:
            raise TaskError('APPROVAL_KEY_UNTRUSTED') from None


@dataclass(frozen=True)
class VerifiedReceipt:
    review_id: str
    decision: str
    key_id: str
    statement_sha256: str
    receipt_sha256: str


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    path = Path(__file__).resolve().parents[2] / 'design/omb003a/TASK_MANAGER_SCHEMA.json'
    document = json.loads(path.read_text(encoding='utf-8'))
    return Draft202012Validator(document['$defs']['ApprovalReceipt'])


def _unique_fields(pairs):
    value = {}
    for name, item in pairs:
        if name in value:
            raise ValueError('Duplicate JSON field')
        value[name] = item
    return value


def _reject_constant(_):
    raise ValueError('Invalid JSON number')


def _parse(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_RECEIPT_BYTES:
        raise TaskError('APPROVAL_INVALID_RECEIPT')
    try:
        receipt = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
        if not _validator().is_valid(receipt):
            raise ValueError()
        for field in ('subject_version', 'policy_version', 'binding_version'):
            if type(receipt[field]) is not int:
                raise ValueError()
        if not re.fullmatch(r'[0-9a-f]{64}', receipt['nonce']):
            raise ValueError()
        text(receipt['key_id'], 128)
        text(receipt['reason'], 2000, empty=True)
        if receipt['decision'] in {'REJECT_RESULT', 'REQUEST_CHANGES'} and not receipt['reason'].strip():
            raise ValueError()
        return receipt
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise TaskError('APPROVAL_INVALID_RECEIPT') from None


def _signed_bytes(receipt: dict) -> bytes:
    body = {name: value for name, value in receipt.items() if name != 'signature_base64'}
    return DOMAIN.encode('ascii') + b'\n' + canonical(body).encode('utf-8')


def _verify_deadline(challenge: ReceiptChallenge, now: datetime, monotonic_now: float):
    try:
        start = parse_time(challenge.issued_at)
        expires = parse_time(challenge.expires_at)
        review_expires = parse_time(challenge.subject.review_expires_at)
        wall = parse_time(stamp(now))
    except TaskError:
        raise TaskError('APPROVAL_CLOCK_UNTRUSTED') from None
    duration = (expires - start).total_seconds()
    clock_values = (monotonic_now, challenge.issued_monotonic)
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in clock_values):
        raise TaskError('APPROVAL_CLOCK_UNTRUSTED')
    elapsed = monotonic_now - challenge.issued_monotonic
    wall_elapsed = (wall - start).total_seconds()
    if (not math.isfinite(elapsed) or not 0 < duration <= MAX_CHALLENGE_SECONDS or expires > review_expires
            or elapsed < 0 or wall_elapsed < 0 or abs(elapsed - wall_elapsed) > CLOCK_SKEW_SECONDS):
        raise TaskError('APPROVAL_CLOCK_UNTRUSTED')
    if wall >= expires or elapsed >= duration:
        raise TaskError('APPROVAL_CHALLENGE_EXPIRED')


def verify_result_receipt(raw: bytes, *, current_subject: ResultSubject,
                          challenge: ReceiptChallenge, pinned_key: PinnedKey,
                          boot_id: str, now: datetime, monotonic_now: float) -> VerifiedReceipt:
    """Verify format, live-context binding, expiry and signature.

    A successful result is input to a future transactional decision. The caller
    must supply live host state and a still-pending challenge, then consume that
    challenge with the decision in the same transaction. No receipt is accepted
    by a TaskManager or MCP endpoint in this implementation.
    """
    receipt = _parse(raw)
    if receipt['decision'] not in RESULT_DECISIONS or receipt['control_action'] is not None:
        raise TaskError('APPROVAL_DECISION_UNSUPPORTED')
    if receipt['purpose'] != 'LOCAL_SYNTHETIC_VALIDATION':
        raise TaskError('PURPOSE_NOT_EXECUTABLE')
    signed_subject_fields = (item.name for item in fields(ResultSubject) if item.name != 'review_expires_at')
    if (challenge.boot_id != boot_id or challenge.subject != current_subject
            or any(receipt[name] != getattr(current_subject, name) for name in signed_subject_fields)):
        raise TaskError('APPROVAL_CONTEXT_STALE')
    if receipt['key_id'] != pinned_key.key_id or challenge.key_id != pinned_key.key_id:
        raise TaskError('APPROVAL_KEY_UNTRUSTED')
    if (receipt['decision'] != challenge.decision or receipt['issued_at'] != challenge.issued_at
            or receipt['expires_at'] != challenge.expires_at
            or not hmac.compare_digest(_sha256(bytes.fromhex(receipt['nonce'])).encode(), challenge.nonce_hash.encode())):
        raise TaskError('APPROVAL_CHALLENGE_MISMATCH')
    _verify_deadline(challenge, now, monotonic_now)
    key = pinned_key.load()
    signed = _signed_bytes(receipt)
    try:
        encoded = receipt['signature_base64'].encode('ascii')
        signature = base64.b64decode(encoded, validate=True)
        if base64.b64encode(signature) != encoded or len(signature) > 72:
            raise ValueError()
        r, s = utils.decode_dss_signature(signature)
        if r <= 0 or s <= 0 or utils.encode_dss_signature(r, s) != signature:
            raise ValueError()
        key.verify(signature, signed, ec.ECDSA(hashes.SHA256()))
    except (UnicodeError, binascii.Error, ValueError, InvalidSignature):
        raise TaskError('APPROVAL_INVALID_SIGNATURE') from None
    return VerifiedReceipt(receipt['review_id'], receipt['decision'], pinned_key.key_id,
                           _sha256(signed), _sha256(canonical(receipt).encode('utf-8')))


def result_subject_from_host(repository, task_id, *, boot_id, now):
    """Read a pending verified result for receipt integration. No challenge is issued."""
    require_id(task_id, 'task')
    at = stamp(now)

    def read(db):
        if repository.meta(db, 'active_boot') != boot_id:
            raise TaskError('RUNTIME_INACTIVE')
        repository.assert_runtime(boot_id)
        workspace_id = repository.meta(db, 'workspace_id')
        row = db.execute('SELECT * FROM tm_tasks WHERE workspace_id=? AND task_id=?',
                         (workspace_id, task_id)).fetchone()
        if row is None:
            raise TaskError('REVIEW_STALE')
        task = repository.verify_task(db, row)
        if task.state.value != 'REVIEW_PENDING' or parse_time(at) < parse_time(task.updated_at):
            raise TaskError('REVIEW_STALE')
        review = reviews.current(db, task)
        if review is None or review['subject_version'] != task.version or reviews.invalidation_reason(db, task, at):
            raise TaskError('REVIEW_STALE')
        db_instance = db.execute('SELECT db_instance_id FROM workspaces WHERE workspace_id=?',
                                 (workspace_id,)).fetchone()[0]
        review_instance = db.execute('SELECT db_instance_id FROM result_review_requests WHERE review_id=?',
                                     (review['review_id'],)).fetchone()
        if review_instance is None or review_instance[0] != db_instance:
            raise TaskError('REVIEW_STALE')
        return ResultSubject(workspace_id=workspace_id, db_instance_id=db_instance, task_id=task_id,
            review_id=review['review_id'], subject_version=task.version,
            definition_hash=review['definition_hash'], evidence_set_hash=review['evidence_set_hash'],
            purpose=task.purpose, policy_version=review['policy_version'], binding_version=review['binding_version'],
            authorization_scope_hash=review['authorization_scope_hash'], review_expires_at=review['expires_at'])

    return repository.read(read)
