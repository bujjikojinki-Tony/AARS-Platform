"""Verified OMB-002 synthetic fixture snapshots and append-only task links."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from hashlib import sha256
import json
import re

from aars_core.certification.serialization import object_from_dict
from aars_omb.store import plain
from aars_sdk import AARSClient

from .domain import canonical, hash_json, new_id, parse_time, require_id, ZERO_HASH
from .errors import TaskError

FIXTURE_ARCHIVE_ENTRY = 'BOT_TASK_OBJECT_SNAPSHOT.json'
FIXTURE_ARTIFACT_HASH = 'sha256:0c8f2bdc5d92a7e7453bf6b6fee73635c490ac2d487407b6f51a57a3cbce9b86'
LICENSE_BASIS = 'OMB-002-FIX internal synthetic fixture validation only'

SCHEMA = '''
CREATE TABLE fixture_graphs (
 workspace_id TEXT PRIMARY KEY REFERENCES workspaces(workspace_id),
 artifact BLOB NOT NULL, artifact_hash TEXT NOT NULL, graph_digest TEXT NOT NULL,
 registered_at TEXT NOT NULL, expires_at TEXT, grant_hash TEXT NOT NULL
);
CREATE TABLE object_snapshots (
 workspace_id TEXT NOT NULL REFERENCES fixture_graphs(workspace_id),
 snapshot_id TEXT NOT NULL, object_id TEXT NOT NULL, object_type TEXT NOT NULL,
 canonical_json TEXT NOT NULL CHECK(json_valid(canonical_json)), graph_digest TEXT NOT NULL,
 PRIMARY KEY(workspace_id,snapshot_id), UNIQUE(workspace_id,object_id)
);
CREATE TABLE evidence_link_versions (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, link_id TEXT NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>=1), snapshot_id TEXT NOT NULL,
 task_version INTEGER NOT NULL CHECK(task_version>=2),
 use_state TEXT NOT NULL CHECK(use_state IN ('USABLE_FIXTURE','REVOKED','REVIEW_REQUIRED')),
 scope_hash TEXT NOT NULL, verification_hash TEXT NOT NULL,
 PRIMARY KEY(workspace_id,task_id,link_id,revision),
 UNIQUE(workspace_id,task_id,task_version), UNIQUE(workspace_id,task_id,snapshot_id,revision),
 FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),
 FOREIGN KEY(workspace_id,snapshot_id) REFERENCES object_snapshots(workspace_id,snapshot_id),
 FOREIGN KEY(workspace_id,task_id,task_version) REFERENCES task_revisions(workspace_id,task_id,version) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE fixture_expirations (
 workspace_id TEXT PRIMARY KEY REFERENCES fixture_graphs(workspace_id),
 detected_at TEXT NOT NULL, expiration_hash TEXT NOT NULL
);
CREATE TABLE fixture_revocations (
 workspace_id TEXT PRIMARY KEY REFERENCES fixture_graphs(workspace_id),
 revoked_at TEXT NOT NULL, reason TEXT NOT NULL, revocation_hash TEXT NOT NULL
);
'''


def require_snapshot_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value):
        raise TaskError('INVALID_ARGUMENT')
    return value


@lru_cache(maxsize=4)
def certify_fixture(raw: bytes):
    """Trust only the reviewed archive artifact, then verify the full Core graph."""
    if 'sha256:' + sha256(raw).hexdigest() != FIXTURE_ARTIFACT_HASH:
        raise TaskError('SOURCE_UNVERIFIED')
    try:
        rows = json.loads(raw)
        if len(rows) != 9:
            raise ValueError()
        objects, snapshots = [], []
        for row in rows:
            record = row['record']
            obj = object_from_dict(record)
            fingerprint = hash_json(record)
            if (fingerprint != 'sha256:' + row['sha256'] or obj.id != row['object_id']
                or obj.type.value != row['type'] or obj.provenance.source_type != 'test_fixture'
                or canonical(plain(obj)) != canonical(record)):
                raise ValueError()
            objects.append(obj)
            snapshots.append((fingerprint, obj.id, obj.type.value, canonical(record)))
        if not AARSClient().certify(objects).valid:
            raise ValueError()
        if sum(obj.type.value == 'evidence' for obj in objects) != 1:
            raise ValueError()
        graph_digest = hash_json(sorted((row[1], row[0]) for row in snapshots))
        return graph_digest, tuple(sorted(snapshots))
    except (ValueError, TypeError, KeyError, AttributeError):
        raise TaskError('SOURCE_UNVERIFIED') from None


def grant_fingerprint(workspace, graph_digest, registered_at, expires_at):
    return hash_json({'workspace_id': workspace, 'artifact_hash': FIXTURE_ARTIFACT_HASH,
        'graph_digest': graph_digest, 'registered_at': registered_at, 'expires_at': expires_at,
        'license_basis': LICENSE_BASIS, 'source_verification': 'FIXTURE_VERIFIED'})


def verified_graph(db, workspace):
    row = db.execute('SELECT * FROM fixture_graphs WHERE workspace_id=?', (workspace,)).fetchone()
    stored = db.execute('SELECT snapshot_id,object_id,object_type,canonical_json,graph_digest FROM object_snapshots WHERE workspace_id=? ORDER BY snapshot_id', (workspace,)).fetchall()
    if row is None:
        if stored:
            raise TaskError('INTEGRITY_FAILURE')
        return None
    try:
        digest, snapshots = certify_fixture(row['artifact'])
        registered = parse_time(row['registered_at'])
        if row['expires_at'] and parse_time(row['expires_at']) <= registered:
            raise TaskError('INTEGRITY_FAILURE')
        if (row['artifact_hash'] != FIXTURE_ARTIFACT_HASH or row['graph_digest'] != digest
            or row['grant_hash'] != grant_fingerprint(workspace, digest, row['registered_at'], row['expires_at'])
            or tuple(map(tuple, stored)) != tuple((*snapshot, digest) for snapshot in snapshots)):
            raise TaskError('INTEGRITY_FAILURE')
        return row
    except (TaskError, TypeError):
        raise TaskError('INTEGRITY_FAILURE') from None


def register_fixture(db, workspace, artifact, now, expires_at):
    digest, snapshots = certify_fixture(artifact)
    if expires_at is not None and parse_time(expires_at) <= parse_time(now):
        raise TaskError('INVALID_ARGUMENT')
    registered = parse_time(now)
    latest_object_time = max(datetime.fromisoformat(json.loads(row[3])['created_at']) for row in snapshots)
    if registered < latest_object_time:
        raise TaskError('CLOCK_UNTRUSTED')
    existing = verified_graph(db, workspace)
    if existing is None:
        db.execute('INSERT INTO fixture_graphs VALUES (?,?,?,?,?,?,?)', (workspace, artifact,
            FIXTURE_ARTIFACT_HASH, digest, now, expires_at, grant_fingerprint(workspace, digest, now, expires_at)))
        db.executemany('INSERT INTO object_snapshots VALUES (?,?,?,?,?,?)',
                       [(workspace, *row, digest) for row in snapshots])
    elif existing['expires_at'] != expires_at:
        raise TaskError('SOURCE_ALREADY_REGISTERED')
    return {'artifact_sha256': FIXTURE_ARTIFACT_HASH, 'graph_digest': digest,
        'object_count': len(snapshots), 'evidence_snapshot_id': next(row[0] for row in snapshots if row[2] == 'evidence'),
        'source_verification': 'FIXTURE_VERIFIED', 'execution_authorized': False}


def revocation(db, workspace):
    row = db.execute('SELECT * FROM fixture_revocations WHERE workspace_id=?', (workspace,)).fetchone()
    if row and row['revocation_hash'] != hash_json({'workspace_id': workspace, 'at': row['revoked_at'], 'reason': row['reason']}):
        raise TaskError('INTEGRITY_FAILURE')
    return row


def expiration(db, graph):
    row = db.execute('SELECT * FROM fixture_expirations WHERE workspace_id=?', (graph['workspace_id'],)).fetchone()
    if row:
        if (not graph['expires_at'] or parse_time(row['detected_at']) < parse_time(graph['expires_at'])
            or row['expiration_hash'] != hash_json({'grant_hash': graph['grant_hash'], 'at': row['detected_at']})):
            raise TaskError('INTEGRITY_FAILURE')
    return row


def grant_usable(db, graph, now):
    return bool(graph and revocation(db, graph['workspace_id']) is None and expiration(db, graph) is None
                and parse_time(now) >= parse_time(graph['registered_at']) and
                (graph['expires_at'] is None or parse_time(now) < parse_time(graph['expires_at'])))


def scope_for(task):
    return {'workspace_id': task.workspace_id, 'task_definition_hash': task.definition_hash}


def append_link(db, task, *, snapshot_id, now):
    if task.purpose != 'LOCAL_SYNTHETIC_VALIDATION':
        raise TaskError('PURPOSE_NOT_EXECUTABLE')
    graph = verified_graph(db, task.workspace_id)
    obj = db.execute('SELECT object_type FROM object_snapshots WHERE workspace_id=? AND snapshot_id=?',
                     (task.workspace_id, snapshot_id)).fetchone()
    if obj is None or obj[0] != 'evidence' or not grant_usable(db, graph, now):
        raise TaskError('EVIDENCE_UNUSABLE')
    if db.execute('SELECT 1 FROM evidence_link_versions WHERE workspace_id=? AND task_id=? AND snapshot_id=?',
                  (task.workspace_id, task.task_id, snapshot_id)).fetchone():
        raise TaskError('NO_CHANGE')
    link = {'link_id': new_id('link'), 'revision': 1, 'task_id': task.task_id, 'snapshot_id': snapshot_id,
        'purpose': task.purpose, 'scope': scope_for(task), 'source_verification': 'FIXTURE_VERIFIED',
        'license_basis': LICENSE_BASIS, 'use_state': 'USABLE_FIXTURE'}
    db.execute('INSERT INTO evidence_link_versions VALUES (?,?,?,?,?,?,?,?,?)', (task.workspace_id,
        task.task_id, link['link_id'], 1, snapshot_id, task.version + 1, link['use_state'],
        hash_json(link['scope']), graph['grant_hash']))
    return link


def link_versions(db, task):
    return db.execute('SELECT * FROM evidence_link_versions WHERE workspace_id=? AND task_id=? ORDER BY task_version',
                      (task.workspace_id, task.task_id)).fetchall()


def evidence_digest(rows):
    return hash_json(sorted((row['link_id'], row['revision'], row['snapshot_id'], row['use_state'],
        'LOCAL_SYNTHETIC_VALIDATION', row['scope_hash'], row['verification_hash']) for row in rows)) if rows else ZERO_HASH


def latest_links(rows):
    return list({row['link_id']: row for row in rows}.values())


def verify_history(db, task, events, revisions):
    rows = link_versions(db, task)
    if not rows and all(event['payload']['evidence_set_hash'] == ZERO_HASH and event['event_type'] not in {'EVIDENCE_LINKED', 'EVIDENCE_INVALIDATED'} for event in events):
        return
    graph = verified_graph(db, task.workspace_id)
    if graph is None or task.purpose != 'LOCAL_SYNTHETIC_VALIDATION':
        raise TaskError('INTEGRITY_FAILURE')
    revoked = revocation(db, task.workspace_id)
    expired = expiration(db, graph)
    evidence_ids = {row[0] for row in db.execute('SELECT snapshot_id FROM object_snapshots WHERE workspace_id=? AND object_type=?',
                                               (task.workspace_id, 'evidence'))}
    by_version = {row['task_version']: row for row in rows}
    if any(version < 2 or version > len(events) for version in by_version):
        raise TaskError('INTEGRITY_FAILURE')
    current = {}
    for event, revision in zip(events, revisions):
        link = by_version.get(event['seq'])
        if link:
            prior = current.get(link['link_id'])
            require_id(link['link_id'], 'link')
            if link['snapshot_id'] not in evidence_ids or link['verification_hash'] != graph['grant_hash']:
                raise TaskError('INTEGRITY_FAILURE')
            if link['revision'] == 1:
                if (prior or event['event_type'] != 'EVIDENCE_LINKED' or link['use_state'] != 'USABLE_FIXTURE'
                    or event['from_state'] != 'RUNNING' or event['to_state'] != 'RUNNING'
                    or link['scope_hash'] != hash_json(scope_for(revision))):
                    raise TaskError('INTEGRITY_FAILURE')
            elif (prior is None or link['revision'] != prior['revision'] + 1 or prior['use_state'] == 'REVOKED' or prior['use_state'] == link['use_state'] or prior['snapshot_id'] != link['snapshot_id']
                  or prior['scope_hash'] != link['scope_hash'] or event['event_type'] != 'EVIDENCE_INVALIDATED'
                  or (link['use_state'] == 'REVOKED' and not revoked)
                  or (link['use_state'] == 'REVIEW_REQUIRED' and not expired)):
                raise TaskError('INTEGRITY_FAILURE')
            if event['payload']['related_ids'][:2] != [link['link_id'], link['snapshot_id']]:
                raise TaskError('INTEGRITY_FAILURE')
            current[link['link_id']] = link
        elif event['event_type'] in {'EVIDENCE_LINKED', 'EVIDENCE_INVALIDATED'}:
            raise TaskError('INTEGRITY_FAILURE')
        if event['payload']['evidence_set_hash'] != evidence_digest(current.values()):
            raise TaskError('INTEGRITY_FAILURE')


def trace(db, task, now):
    graph = verified_graph(db, task.workspace_id)
    result = []
    for row in link_versions(db, task):
        event = db.execute('SELECT event_id,event_hash FROM task_events WHERE workspace_id=? AND task_id=? AND seq=?',
                           (task.workspace_id, task.task_id, row['task_version'])).fetchone()
        result.append({**dict(row), **dict(event)})
    provenance = None
    if graph is not None and result:
        object_row = db.execute(
            'SELECT object_id,canonical_json FROM object_snapshots WHERE workspace_id=? AND snapshot_id=?',
            (task.workspace_id, result[0]['snapshot_id'])).fetchone()
        record = json.loads(object_row['canonical_json'])
        provenance = {'evidence_object_id': object_row['object_id'], 'observation_ids': record['observation_ids'],
            'core_provenance': record['provenance'], 'archive_entry': FIXTURE_ARCHIVE_ENTRY}
    current = []
    revoked = revocation(db, task.workspace_id)
    for row in latest_links(result):
        effective = row['use_state']
        if effective == 'USABLE_FIXTURE' and not grant_usable(db, graph, now):
            effective = 'REVOKED' if revoked else 'REVIEW_REQUIRED'
        current.append({'link_id': row['link_id'], 'snapshot_id': row['snapshot_id'], 'effective_use_state': effective})
    return {'task_id': task.task_id, 'version': task.version, 'history': result, 'current': current,
            'source': None if not graph or not result else {'artifact_sha256': graph['artifact_hash'],
                'graph_digest': graph['graph_digest'], 'grant_hash': graph['grant_hash'], 'expires_at': graph['expires_at'],
                'source_verification': 'FIXTURE_VERIFIED', 'license_basis': LICENSE_BASIS},
            'evidence_set_hash': evidence_digest(latest_links(result)), 'provenance': provenance, 'execution_authorized': False}
