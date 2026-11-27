"""Internal result approval transaction. A verified operator channel must call it.

The application does not construct this store. Enrollment and human-presence
verification belong to the native broker, which is still gated.
"""
from dataclasses import asdict, replace
from datetime import timedelta
import hmac
import math
import secrets

from . import approval_history as history, approval_receipts as receipts
from .approval_enrollment import EnrollmentAnchor
from .domain import canonical, new_id, parse_time, require_id, require_key, require_version, stamp
from .errors import TaskError


class ResultDecisionStore:
    def __init__(self, repository, *, boot_id, anchor: EnrollmentAnchor, now, monotonic_now):
        self.repository = repository
        self.boot_id = require_id(boot_id, 'boot')
        self.anchor = anchor
        self.operator_id = anchor.operator_id
        self.now = now
        self.monotonic_now = monotonic_now
        # One store per trusted host session. Neither this key nor the derived
        # challenge values are written to SQLite or exposed to Bot callers.
        self._preparation_key = secrets.token_bytes(32)

    def _context(self, db):
        self.anchor.check_context(self.repository, db, self.boot_id)
        workspace = self.anchor.workspace_id
        row = db.execute(
            'SELECT key_id,public_point,pin_sha256 FROM result_operator_pins '
            'WHERE workspace_id=? AND operator_id=? AND active=1',
            (workspace, self.operator_id)).fetchone()
        if row is None:
            raise TaskError('APPROVAL_KEY_UNTRUSTED')
        pin = receipts.PinnedKey(*row)
        self.anchor.check_pin(pin)
        return workspace, pin

    def _challenge(self, db, workspace, key):
        return db.execute(
            'SELECT * FROM result_approval_challenges WHERE workspace_id=? AND operator_id=? AND idempotency_key=?',
            (workspace, self.operator_id, key)).fetchone()

    def _nonce(self, challenge, idempotency_key, pin):
        fields = asdict(challenge)
        fields.pop('nonce_hash')
        fields.update(operator_id=self.operator_id, idempotency_key=idempotency_key, pin_sha256=pin.sha256)
        material = b'AARS-OMB-RESULT-CHALLENGE-V1\n' + canonical(fields).encode('utf-8')
        return hmac.digest(self._preparation_key, material, 'sha256')

    @staticmethod
    def _stored_challenge(row, subject):
        return receipts.ReceiptChallenge(subject, row['boot_id'], row['nonce_hash'], row['key_id'],
                                         row['decision'], row['issued_at'], row['expires_at'],
                                         row['issued_monotonic'])

    def _recover_preparation(self, db, row, *, task_id, expected_version, decision, pin, now):
        review = db.execute('SELECT subject_version FROM result_review_requests WHERE review_id=?',
                            (row['review_id'],)).fetchone()
        if review is None:
            raise TaskError('INTEGRITY_FAILURE')
        if (row['task_id'], review['subject_version'], row['decision']) != (task_id, expected_version, decision):
            raise TaskError('IDEMPOTENCY_CONFLICT')
        if (row['key_id'], row['pin_sha256']) != (pin.key_id, pin.sha256):
            raise TaskError('APPROVAL_KEY_UNTRUSTED')
        if db.execute('SELECT 1 FROM result_approval_decisions WHERE nonce_hash=?', (row['nonce_hash'],)).fetchone():
            raise TaskError('APPROVAL_CHALLENGE_CONSUMED')
        if row['boot_id'] != self.boot_id or parse_time(stamp(now)) >= parse_time(row['expires_at']):
            raise TaskError('APPROVAL_CHALLENGE_EXPIRED')
        _, subject = receipts._result_in_transaction(
            self.repository, db, task_id, boot_id=self.boot_id, now=now)
        if (row['review_id'], expected_version) != (subject.review_id, subject.subject_version):
            raise TaskError('APPROVAL_CONTEXT_STALE')
        challenge = self._stored_challenge(row, subject)
        receipts._verify_deadline(challenge, now, self.monotonic_now())
        nonce = self._nonce(challenge, row['idempotency_key'], pin)
        if not hmac.compare_digest(receipts._sha256(nonce), challenge.nonce_hash):
            # The issuing session no longer holds the key, or the row has changed.
            raise TaskError('APPROVAL_CHALLENGE_EXPIRED')
        return challenge, nonce.hex()

    def prepare(self, task_id, *, expected_version, idempotency_key, decision):
        """Prepare or recover the same live challenge for the trusted caller."""
        require_id(task_id, 'task')
        require_version(expected_version)
        require_key(idempotency_key)
        if not isinstance(decision, str) or decision not in history.OUTCOMES:
            raise TaskError('APPROVAL_DECISION_UNSUPPORTED')
        repo = self.repository

        def write(db):
            workspace, pin = self._context(db)
            now = self.now()
            existing = self._challenge(db, workspace, idempotency_key)
            if existing is not None:
                return self._recover_preparation(db, existing, task_id=task_id, expected_version=expected_version,
                                                 decision=decision, pin=pin, now=now)
            _, subject = receipts._result_in_transaction(repo, db, task_id, boot_id=self.boot_id, now=now)
            if subject.subject_version != expected_version:
                raise TaskError('VERSION_CONFLICT')
            ticks = self.monotonic_now()
            if type(ticks) not in (float, int) or not math.isfinite(ticks) or ticks < 0:
                raise TaskError('APPROVAL_CLOCK_UNTRUSTED')
            expiry = min(parse_time(subject.review_expires_at), now + timedelta(seconds=receipts.MAX_CHALLENGE_SECONDS))
            challenge = receipts.ReceiptChallenge(subject, self.boot_id, '', pin.key_id, decision,
                                                  stamp(now), stamp(expiry), float(ticks))
            nonce = self._nonce(challenge, idempotency_key, pin)
            challenge = replace(challenge, nonce_hash=receipts._sha256(nonce))
            db.execute(
                'INSERT INTO result_approval_challenges VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (challenge.nonce_hash, workspace, task_id, subject.review_id, self.operator_id, pin.key_id,
                 idempotency_key, self.boot_id, pin.sha256, decision, challenge.issued_at, challenge.expires_at,
                 challenge.issued_monotonic))
            return challenge, nonce.hex()

        return repo.write(write)

    def submit(self, raw, *, idempotency_key):
        """Serialize context verification, nonce consumption, the task update and its event."""
        require_key(idempotency_key)
        receipt = receipts._parse(raw)
        repo = self.repository

        def write(db):
            workspace, pin = self._context(db)
            row = self._challenge(db, workspace, idempotency_key)
            if row is None:
                raise TaskError('APPROVAL_CHALLENGE_MISMATCH')
            if (row['key_id'], row['pin_sha256']) != (pin.key_id, pin.sha256):
                raise TaskError('APPROVAL_KEY_UNTRUSTED')
            stored = db.execute('SELECT * FROM result_approval_decisions WHERE nonce_hash=?',
                                (row['nonce_hash'],)).fetchone()
            if stored is not None:
                return self._replay(db, stored, row, receipt, pin)
            if row['boot_id'] != self.boot_id:
                raise TaskError('APPROVAL_CONTEXT_STALE')
            now = self.now()
            task, subject = receipts._result_in_transaction(repo, db, row['task_id'], boot_id=self.boot_id, now=now)
            if row['review_id'] != subject.review_id:
                raise TaskError('APPROVAL_CONTEXT_STALE')
            challenge = self._stored_challenge(row, subject)
            verified = receipts._verify_parsed_result(
                receipt, current_subject=subject, challenge=challenge, pinned_key=pin, boot_id=self.boot_id,
                now=now, monotonic_now=self.monotonic_now())
            commit_time = self.now()
            receipts._verify_deadline(challenge, commit_time, self.monotonic_now())
            if commit_time < now:
                raise TaskError('APPROVAL_CLOCK_UNTRUSTED')
            decided_at = stamp(commit_time)
            destination, usage = history.OUTCOMES[verified.decision]
            updated = replace(task, state=destination, usage_state=usage, version=task.version + 1,
                              updated_at=decided_at)
            approval = {'approval_id': new_id('approval'), 'workspace_id': workspace, 'task_id': task.task_id,
                        'review_id': subject.review_id, 'nonce_hash': row['nonce_hash'], 'task_version': updated.version,
                        'statement_sha256': verified.statement_sha256, 'receipt_sha256': verified.receipt_sha256,
                        'reason': receipt['reason'], 'decided_at': decided_at}
            repo.save(db, task, updated, actor=self.operator_id, event_type=history.EVENT_TYPE,
                      now=decided_at, request_hash=verified.statement_sha256,
                      related_ids=(subject.review_id, approval['approval_id'], history.commitment(approval, row)))
            # Its UNIQUE nonce_hash is the consumption marker. The challenge remains auditable.
            db.execute('INSERT INTO result_approval_decisions VALUES (?,?,?,?,?,?,?,?,?,?)',
                       tuple(approval.values()))
            return self._response(approval, verified.decision, replayed=False)

        return repo.write(write)

    def _replay(self, db, stored, challenge, receipt, pin):
        repo = self.repository
        verified = receipts._verify_signature(receipt, pin)
        if verified.statement_sha256 != stored['statement_sha256']:
            raise TaskError('IDEMPOTENCY_CONFLICT')
        row = db.execute(
            'SELECT t.* FROM tm_tasks t JOIN result_review_requests r ON r.workspace_id=t.workspace_id '
            'AND r.task_id=t.task_id JOIN workspaces w ON w.workspace_id=r.workspace_id '
            'AND w.db_instance_id=r.db_instance_id WHERE r.review_id=?', (challenge['review_id'],)).fetchone()
        if row is None:
            raise TaskError('APPROVAL_CONTEXT_STALE')
        repo.verify_task(db, row)
        return self._response(stored, challenge['decision'], replayed=True)

    @staticmethod
    def _response(approval, decision, *, replayed):
        return {**{key: approval[key] for key in ('approval_id', 'review_id', 'task_id', 'task_version',
                                                  'decided_at', 'statement_sha256', 'receipt_sha256')},
                'decision': decision, 'replayed': replayed}
