"""Development enrollment gate. Only a trusted host may supply the expected anchor."""
from dataclasses import asdict, dataclass
from datetime import timedelta
import math
import re
import secrets
from threading import Lock

from . import approval_receipts as receipts
from .domain import canonical, parse_time, require_id, stamp, text
from .errors import TaskError

DOMAIN = b'AARS-OMB-PIN-ENROLLMENT-V1\n'


@dataclass(frozen=True)
class EnrollmentAnchor:
    """Expected identity and fingerprint from the host's independent trust configuration."""

    workspace_id: str
    db_instance_id: str
    operator_id: str
    key_id: str
    pin_sha256: str

    def __post_init__(self):
        require_id(self.workspace_id, 'workspace')
        require_id(self.db_instance_id, 'db')
        require_id(self.operator_id, 'principal')
        text(self.key_id, 128)
        if not isinstance(self.pin_sha256, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', self.pin_sha256):
            raise TaskError('APPROVAL_KEY_UNTRUSTED')

    def check_context(self, repo, db, boot_id):
        if repo.meta(db, 'active_boot') != boot_id:
            raise TaskError('RUNTIME_INACTIVE')
        repo.assert_runtime(boot_id)
        if repo.meta(db, 'workspace_id') != self.workspace_id:
            raise TaskError('APPROVAL_CONTEXT_STALE')
        row = db.execute('SELECT db_instance_id,policy_version FROM workspaces WHERE workspace_id=?',
                         (self.workspace_id,)).fetchone()
        if row is None or row['db_instance_id'] != self.db_instance_id:
            raise TaskError('APPROVAL_CONTEXT_STALE')
        if db.execute('SELECT 1 FROM principals WHERE workspace_id=? AND principal_id=?',
                      (self.workspace_id, self.operator_id)).fetchone():
            raise TaskError('APPROVAL_KEY_UNTRUSTED')
        return row['policy_version']

    def check_pin(self, pin):
        if (pin.key_id, pin.sha256) != (self.key_id, self.pin_sha256):
            raise TaskError('APPROVAL_KEY_UNTRUSTED')
        return pin.load()


@dataclass(frozen=True)
class EnrollmentChallenge:
    anchor: EnrollmentAnchor
    boot_id: str
    policy_version: int
    nonce: str
    issued_at: str
    expires_at: str
    issued_monotonic: float

    def signing_bytes(self):
        context = asdict(self.anchor)
        context.update(boot_id=self.boot_id, policy_version=self.policy_version, nonce=self.nonce,
                       issued_at=self.issued_at, expires_at=self.expires_at)
        return DOMAIN + canonical(context).encode('utf-8')


class EnrollmentStore:
    """Issue one ephemeral challenge and stage a single inactive candidate per workspace."""

    def __init__(self, repository, *, anchor: EnrollmentAnchor, boot_id, now, monotonic_now):
        self.repository = repository
        self.anchor = anchor
        self.boot_id = require_id(boot_id, 'boot')
        self.now = now
        self.monotonic_now = monotonic_now
        self._lock = Lock()
        self._challenge: EnrollmentChallenge | None = None

    def _ensure_first_pin(self, db):
        if db.execute('SELECT 1 FROM result_operator_pins WHERE workspace_id=? LIMIT 1',
                      (self.anchor.workspace_id,)).fetchone():
            raise TaskError('APPROVAL_ENROLLMENT_EXISTS')

    def prepare(self):
        def read(db):
            policy = self.anchor.check_context(self.repository, db, self.boot_id)
            self._ensure_first_pin(db)
            now = stamp(self.now())
            ticks = self.monotonic_now()
            if type(ticks) not in (float, int) or ticks < 0 or not math.isfinite(ticks):
                raise TaskError('APPROVAL_CLOCK_UNTRUSTED')
            expiry = parse_time(now) + timedelta(seconds=receipts.MAX_CHALLENGE_SECONDS)
            return EnrollmentChallenge(self.anchor, self.boot_id, policy, secrets.token_hex(32),
                                       now, stamp(expiry), float(ticks))

        with self._lock:
            self._challenge = self.repository.read(read)
            return self._challenge

    def stage(self, public_point, signature_base64):
        """Verify proof of possession in the write transaction and retain an inactive pin."""
        with self._lock:
            challenge = self._challenge
            if challenge is None:
                raise TaskError('APPROVAL_ENROLLMENT_CHALLENGE_MISSING')

            def write(db):
                policy = self.anchor.check_context(self.repository, db, self.boot_id)
                if policy != challenge.policy_version:
                    raise TaskError('APPROVAL_CONTEXT_STALE')
                self._ensure_first_pin(db)
                key = receipts.PinnedKey(self.anchor.key_id, public_point, self.anchor.pin_sha256)
                public_key = self.anchor.check_pin(key)
                receipts._verify_p256_signature(signature_base64, challenge.signing_bytes(), public_key)
                receipts._verify_challenge_deadline(challenge.issued_at, challenge.expires_at,
                                                    challenge.issued_monotonic, self.now(), self.monotonic_now())
                db.execute('INSERT INTO result_operator_pins '
                           '(workspace_id,operator_id,key_id,public_point,pin_sha256,active) VALUES (?,?,?,?,?,0)',
                           (self.anchor.workspace_id, self.anchor.operator_id, key.key_id, key.x963, key.sha256))
                return key

            result = self.repository.write(write)
            self._challenge = None
            return result
