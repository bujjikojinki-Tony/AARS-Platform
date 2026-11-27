"""Schema and integrity checks for result decisions in the isolated development store."""
import re

from .domain import State, hash_json, parse_time, require_id, require_key, text
from .errors import TaskError

OUTCOMES = {
    'APPROVE_RESULT': (State.COMPLETED, 'USABLE'),
    'REJECT_RESULT': (State.REJECTED, 'UNUSABLE'),
    'REQUEST_CHANGES': (State.READY, 'REVIEW_REQUIRED'),
}

SCHEMA = """
CREATE TABLE result_operator_pins (
 workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
 operator_id TEXT NOT NULL, key_id TEXT NOT NULL, public_point BLOB NOT NULL,
 pin_sha256 TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)),
 PRIMARY KEY(workspace_id,operator_id,key_id), UNIQUE(workspace_id,key_id)
);
CREATE UNIQUE INDEX one_active_result_pin ON result_operator_pins(workspace_id) WHERE active=1;
CREATE TABLE result_approval_challenges (
 nonce_hash TEXT PRIMARY KEY NOT NULL, workspace_id TEXT NOT NULL, task_id TEXT NOT NULL,
 review_id TEXT NOT NULL, operator_id TEXT NOT NULL, key_id TEXT NOT NULL,
 idempotency_key TEXT NOT NULL, boot_id TEXT NOT NULL, pin_sha256 TEXT NOT NULL,
 decision TEXT NOT NULL CHECK(decision IN ('APPROVE_RESULT','REJECT_RESULT','REQUEST_CHANGES')),
 issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, issued_monotonic REAL NOT NULL,
 UNIQUE(workspace_id,operator_id,idempotency_key), UNIQUE(nonce_hash,review_id),
 FOREIGN KEY(workspace_id,task_id,review_id) REFERENCES result_review_requests(workspace_id,task_id,review_id),
 FOREIGN KEY(workspace_id,operator_id,key_id) REFERENCES result_operator_pins(workspace_id,operator_id,key_id)
);
CREATE INDEX result_challenge_review ON result_approval_challenges(workspace_id,task_id,review_id);
CREATE TABLE result_approval_decisions (
 approval_id TEXT PRIMARY KEY NOT NULL, workspace_id TEXT NOT NULL, task_id TEXT NOT NULL,
 review_id TEXT NOT NULL UNIQUE, nonce_hash TEXT NOT NULL UNIQUE, task_version INTEGER NOT NULL,
 statement_sha256 TEXT NOT NULL, receipt_sha256 TEXT NOT NULL, reason TEXT NOT NULL, decided_at TEXT NOT NULL,
 UNIQUE(workspace_id,task_id,task_version),
 FOREIGN KEY(nonce_hash,review_id) REFERENCES result_approval_challenges(nonce_hash,review_id),
 FOREIGN KEY(workspace_id,task_id,review_id) REFERENCES result_review_requests(workspace_id,task_id,review_id),
 FOREIGN KEY(workspace_id,task_id,task_version) REFERENCES task_revisions(workspace_id,task_id,version)
);
"""

EVENT_TYPE = 'RESULT_DECIDED'


def commitment(decision, challenge):
    """Bind both records to the task audit chain without storing the raw receipt."""
    return hash_json({'decision': dict(decision), 'challenge': dict(challenge)})


def result_rejected(db, task):
    """Identify a signed rejection even if a legacy invalidation changed its usage state."""
    if task.state != State.REJECTED:
        return False
    if task.usage_state == 'UNUSABLE':
        return True
    return db.execute(
        "SELECT 1 FROM result_approval_decisions d JOIN result_approval_challenges c ON c.nonce_hash=d.nonce_hash "
        "WHERE d.workspace_id=? AND d.task_id=? AND c.decision='REJECT_RESULT'",
        (task.workspace_id, task.task_id)).fetchone() is not None


def verify_decisions(db, task, events, revisions, review_rows, closed):
    task_key = (task.workspace_id, task.task_id)
    rows = db.execute('SELECT * FROM result_approval_decisions WHERE workspace_id=? AND task_id=?',
                      task_key).fetchall()
    decision_events = {event['seq']: event for event in events if event['event_type'] == EVENT_TYPE}
    if len(rows) != len(decision_events):
        raise TaskError('INTEGRITY_FAILURE')
    decided = set()
    for row in rows:
        review_id = row['review_id']
        version = row['task_version']
        review = review_rows[review_id]
        event = decision_events[version]
        challenge = db.execute('SELECT * FROM result_approval_challenges WHERE nonce_hash=?',
                               (row['nonce_hash'],)).fetchone()
        if challenge is None:
            raise TaskError('INTEGRITY_FAILURE')
        dest, usage = OUTCOMES[challenge['decision']]
        require_id(row['approval_id'], 'approval')
        require_id(challenge['operator_id'], 'principal')
        require_id(challenge['boot_id'], 'boot')
        require_key(challenge['idempotency_key'])
        text(row['reason'], 2000, empty=dest == State.COMPLETED)
        digests = (row['statement_sha256'], row['receipt_sha256'], row['nonce_hash'], challenge['pin_sha256'])
        issued, expiry = map(parse_time, (challenge['issued_at'], challenge['expires_at']))
        if (review_id in closed or review_id in decided
            or (challenge['workspace_id'], challenge['task_id'], challenge['review_id']) != (*task_key, review_id)
            or version != review['subject_version'] + 1
            or event['from_state'] != State.REVIEW_PENDING or event['to_state'] != dest
            or revisions[version - 1].usage_state != usage
            or event['at'] != row['decided_at']
            or event['actor_principal_id'] != challenge['operator_id']
            or event['payload']['related_ids'] != [review_id, row['approval_id'], commitment(row, challenge)]
            or event['payload']['request_hash'] != row['statement_sha256']
            or not all(re.fullmatch(r'sha256:[0-9a-f]{64}', digest) for digest in digests)
            or not 0 < (expiry - issued).total_seconds() <= 120
            or not parse_time(events[version - 2]['at']) <= issued <= parse_time(row['decided_at']) < expiry):
            raise TaskError('INTEGRITY_FAILURE')
        decided.add(review_id)
    return len(decided)
