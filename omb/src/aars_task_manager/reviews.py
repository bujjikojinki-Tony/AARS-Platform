"""Result review requests and closure history. The operator signing gate is locked."""
from datetime import timedelta
import json
from hashlib import sha256
import secrets

from . import evidence
from .domain import canonical, hash_json, new_id, parse_time, require_id, stamp
from .errors import TaskError

SCHEMA = '''
CREATE TABLE result_review_requests (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, review_id TEXT NOT NULL UNIQUE,
 subject_version INTEGER NOT NULL, attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
 db_instance_id TEXT NOT NULL, record_json TEXT NOT NULL CHECK(json_valid(record_json)),
 record_hash TEXT NOT NULL,
 PRIMARY KEY(workspace_id,task_id,review_id),
 UNIQUE(workspace_id,task_id,subject_version),
 FOREIGN KEY(workspace_id,task_id,subject_version)
  REFERENCES task_revisions(workspace_id,task_id,version) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE result_review_closures (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, review_id TEXT NOT NULL,
 task_version INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('STALE','EXPIRED')),
 PRIMARY KEY(workspace_id,task_id,review_id), UNIQUE(workspace_id,task_id,task_version),
 FOREIGN KEY(workspace_id,task_id,review_id) REFERENCES result_review_requests(workspace_id,task_id,review_id),
 FOREIGN KEY(workspace_id,task_id,task_version)
  REFERENCES task_revisions(workspace_id,task_id,version) DEFERRABLE INITIALLY DEFERRED
);
'''


def scope_hash(db, task, policy_version):
    principals = db.execute('SELECT principal_id,binding_version,capabilities_json FROM principals '
        'WHERE workspace_id=? AND active=1 ORDER BY principal_id', (task.workspace_id,)).fetchall()
    acl = db.execute('SELECT principal_id,permission FROM task_acl WHERE workspace_id=? AND task_id=? '
        'AND active=1 ORDER BY principal_id,permission', (task.workspace_id, task.task_id)).fetchall()
    return hash_json({'workspace_id': task.workspace_id, 'policy_version': policy_version,
                      'principals': list(map(tuple, principals)), 'acl': list(map(tuple, acl))})


def request(db, task, principal, attempt, now):
    graph = evidence.verified_graph(db, task.workspace_id)
    links = evidence.latest_links(evidence.link_versions(db, task))
    if not evidence.grant_usable(db, graph, now) or not any(
        row['use_state'] == 'USABLE_FIXTURE' and row['scope_hash'] == hash_json(evidence.scope_for(task)) for row in links):
        raise TaskError('EVIDENCE_UNUSABLE')
    if current(db, task):
        raise TaskError('REVIEW_LOCKED')
    ws = db.execute('SELECT policy_version,db_instance_id FROM workspaces WHERE workspace_id=?',
                    (task.workspace_id,)).fetchone()
    cutoff = parse_time(now) + timedelta(seconds=120)
    if graph['expires_at']:
        cutoff = min(cutoff, parse_time(graph['expires_at']))
    # The record shape reserves nonce_hash; the preimage is discarded. Only an approved
    # native broker may later create an actual, separate, consumable challenge.
    view = {'review_id': new_id('review'), 'task_id': task.task_id, 'kind': 'RESULT',
        'subject_version': task.version + 1, 'definition_hash': task.definition_hash,
        'evidence_set_hash': evidence.evidence_digest(links), 'policy_version': ws['policy_version'],
        'binding_version': principal['binding_version'], 'action': 'approve_result', 'status': 'PENDING',
        'nonce_hash': 'sha256:' + sha256(secrets.token_bytes(32)).hexdigest(), 'expires_at': stamp(cutoff),
        'authorization_scope_hash': scope_hash(db, task, ws['policy_version'])}
    commitment = hash_json({'review': view, 'attempt_id': attempt['attempt_id'], 'db_instance_id': ws['db_instance_id']})
    db.execute('INSERT INTO result_review_requests VALUES (?,?,?,?,?,?,?,?)', (task.workspace_id,
        task.task_id, view['review_id'], view['subject_version'], attempt['attempt_id'], ws['db_instance_id'],
        canonical(view), commitment))
    return view, commitment


def current(db, task):
    row = db.execute('SELECT r.* FROM result_review_requests r LEFT JOIN result_review_closures c '
        'ON c.review_id=r.review_id WHERE r.workspace_id=? AND r.task_id=? AND c.review_id IS NULL',
        (task.workspace_id, task.task_id)).fetchall()
    if len(row) > 1:
        raise TaskError('INTEGRITY_FAILURE')
    return json.loads(row[0]['record_json']) if row else None


def close(db, task, status):
    review = current(db, task)
    if review is None:
        return None
    db.execute('INSERT INTO result_review_closures VALUES (?,?,?,?,?)', (task.workspace_id, task.task_id,
                review['review_id'], task.version + 1, status))
    return review['review_id']


def invalidation_reason(db, task, now):
    review = current(db, task)
    if review is None:
        return None
    if not evidence.grant_usable(db, evidence.verified_graph(db, task.workspace_id), now):
        return 'STALE'
    policy = db.execute('SELECT policy_version FROM workspaces WHERE workspace_id=?', (task.workspace_id,)).fetchone()[0]
    if policy != review['policy_version'] or scope_hash(db, task, policy) != review['authorization_scope_hash']:
        return 'STALE'
    if parse_time(now) >= parse_time(review['expires_at']):
        return 'EXPIRED'
    return None


def verify_history(db, task, events):
    records = db.execute('SELECT * FROM result_review_requests WHERE workspace_id=? AND task_id=?',
                         (task.workspace_id, task.task_id)).fetchall()
    requests = {event['seq']: event for event in events if event['event_type'] == 'REVIEW_REQUESTED'}
    if len(records) != len(requests):
        raise TaskError('INTEGRITY_FAILURE')
    for row in records:
        record = json.loads(row['record_json']); require_id(record['review_id'], 'review')
        event = requests[row['subject_version']]
        payload = event['payload']
        commitment = hash_json({'review': record, 'attempt_id': row['attempt_id'], 'db_instance_id': row['db_instance_id']})
        attempt = db.execute('SELECT * FROM attempts WHERE attempt_id=?', (row['attempt_id'],)).fetchone()
        if (record['review_id'] != row['review_id'] or record['task_id'] != task.task_id
            or record['subject_version'] != row['subject_version'] or record['status'] != 'PENDING'
            or record['kind'] != 'RESULT' or record['action'] != 'approve_result'
            or record['evidence_set_hash'] != payload['evidence_set_hash']
            or record['definition_hash'] != payload['definition_hash'] or commitment != row['record_hash']
            or payload['related_ids'] != [row['review_id'], row['attempt_id'], commitment]
            or not 0 < (parse_time(record['expires_at']) - parse_time(event['at'])).total_seconds() <= 120
            or event['from_state'] != 'RUNNING' or event['to_state'] != 'REVIEW_PENDING'
            or tuple(attempt[key] for key in ('workspace_id','task_id','status','finished_at'))
               != (task.workspace_id, task.task_id, 'SUBMITTED', event['at'])):
            raise TaskError('INTEGRITY_FAILURE')
    closures = db.execute('SELECT * FROM result_review_closures WHERE workspace_id=? AND task_id=?',
                          (task.workspace_id, task.task_id)).fetchall()
    by_id = {row['review_id']: row for row in records}
    for row in closures:
        if not by_id[row['review_id']]['subject_version'] < row['task_version'] <= len(events):
            raise TaskError('INTEGRITY_FAILURE')
        event = events[row['task_version'] - 1]
        if (event['to_state'] != 'PAUSED' or event['from_state'] != 'REVIEW_PENDING'
            or event['event_type'] not in {'REVIEW_INVALIDATED','EVIDENCE_INVALIDATED'}
            or event['payload']['related_ids'][-2:] != [row['review_id'], row['status']]):
            raise TaskError('INTEGRITY_FAILURE')
    pending = len(records) - len(closures)
    if pending != (1 if task.state.value == 'REVIEW_PENDING' else 0):
        raise TaskError('INTEGRITY_FAILURE')
