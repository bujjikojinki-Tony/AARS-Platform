"""Isolated, one-shot test of the native enrollment proof. Never opens an existing task DB."""
import argparse
import base64
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import time
from uuid import uuid4

from aars_task_manager import Binding, Repository, TaskRuntime
from aars_task_manager.approval_enrollment import EnrollmentAnchor, EnrollmentStore
from aars_task_manager.domain import new_id, stamp
from aars_task_manager.errors import TaskError

SCOPE = 'F02_ISOLATED_HARDWARE_PIN'
KEY_ID = 'f02-hardware-fixture'
LIMIT = 4096
REPO_ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc)


def publish(path, value):
    data = (json.dumps(value, ensure_ascii=True, sort_keys=True) + '\n').encode()
    part = path.with_name(f'.{path.name}.{uuid4().hex}')
    fd = os.open(part, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as fd_file:
            fd_file.write(data)
        os.link(part, path)
    finally:
        part.unlink(missing_ok=True)


def wait_json(path, timeout, fields, *, declined=None, run_id=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if declined is not None and declined.exists():
            outcome = wait_json(declined, 1, {'run_id','action'})
            if outcome != {'run_id':run_id,'action':'CANCELLED'}:
                raise TaskError('DIAGNOSTIC_BAD_CANCEL')
            raise TaskError('DIAGNOSTIC_OPERATOR_CANCELLED')
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            time.sleep(0.2)
            continue
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise TaskError('DIAGNOSTIC_UNSAFE_FILE')
            raw = stream.read(LIMIT+1)
        if not 0 < len(raw) <= LIMIT:
            raise TaskError('DIAGNOSTIC_INVALID_INPUT')
        try:
            result = json.loads(raw)
        except (UnicodeError, ValueError):
            raise TaskError('DIAGNOSTIC_INVALID_INPUT') from None
        if type(result) is not dict or result.keys() != fields:
            raise TaskError('DIAGNOSTIC_INVALID_INPUT')
        return result
    raise TaskError('DIAGNOSTIC_TIMEOUT')


def run(root, run_id, timeout):
    storage = root/'database'
    storage.mkdir(mode=0o700)
    protected = (REPO_ROOT/'frozen_archive', REPO_ROOT/'frozen_payload')
    repo = Repository.create(storage/'tasks.sqlite', allowed_root=storage, protected_roots=protected,
                             workspace_id=new_id('workspace'), bindings=[Binding(new_id('binding'),
                             new_id('principal'), ('task.read',))], created_at=stamp(now()))
    with TaskRuntime(repo) as runtime:
        offer = wait_json(root/'offer.json', timeout, {'run_id', 'public_point_b64', 'source'})
        if offer['run_id'] != run_id or offer['source'] not in {'SECURE_ENCLAVE_DIAGNOSTIC', 'SOFTWARE_FIXTURE'}:
            raise TaskError('DIAGNOSTIC_INVALID_INPUT')
        try:
            point = base64.b64decode(offer['public_point_b64'], validate=True)
        except (ValueError, TypeError):
            raise TaskError('DIAGNOSTIC_INVALID_INPUT') from None
        if len(point) != 65 or point[0] != 4:
            raise TaskError('DIAGNOSTIC_INVALID_INPUT')
        workspace, db_instance = repo.read(lambda db: tuple(db.execute(
            'SELECT workspace_id,db_instance_id FROM workspaces').fetchone()))
        anchor = EnrollmentAnchor(workspace, db_instance, new_id('principal'), KEY_ID,
                                  'sha256:' + sha256(point).hexdigest())
        store = EnrollmentStore(repo, anchor=anchor, boot_id=runtime.boot_id, now=now, monotonic_now=time.monotonic)
        challenge = store.prepare()
        message = challenge.signing_bytes()
        message_sha = sha256(message).hexdigest()
        publish(root/'challenge.json', {'scope': SCOPE, 'run_id': run_id,
                                        'payload_b64': base64.b64encode(message).decode('ascii')})
        response = wait_json(root/'proof.json', 119, {'run_id', 'payload_sha256', 'signature_base64'},
                             declined=root/'cancel.json', run_id=run_id)
        if response['run_id'] != run_id or response['payload_sha256'] != message_sha:
            raise TaskError('DIAGNOSTIC_WRONG_CHALLENGE')
        store.stage(point, response['signature_base64'])
        try:
            store.stage(point, response['signature_base64'])
        except TaskError as error:
            if error.code != 'APPROVAL_ENROLLMENT_CHALLENGE_MISSING':
                raise
        else:
            raise TaskError('DIAGNOSTIC_REPLAY_ACCEPTED')
        pins, tasks, approvals = repo.read(lambda db: (
            [tuple(r) for r in db.execute('SELECT operator_id,key_id,pin_sha256,active FROM result_operator_pins')],
            db.execute('SELECT count(*) FROM tm_tasks').fetchone()[0],
            db.execute('SELECT count(*) FROM result_approval_decisions').fetchone()[0],
        ))
        if pins != [(anchor.operator_id, anchor.key_id, anchor.pin_sha256, 0)] or tasks or approvals:
            raise TaskError('DIAGNOSTIC_UNEXPECTED_PERSISTENCE')
        repo.check_integrity()
        return {'status':'INACTIVE_PIN_STAGED','proof_origin':offer['source'],
                'pin_sha256':anchor.pin_sha256, 'active':0,'tasks':0,'approval_decisions':0,
                'replay_rejected':True,'challenge_sha256':message_sha}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path, help='New private diagnostic session directory')
    parser.add_argument('--wait', type=int, default=300)
    args = parser.parse_args()
    root = args.directory.absolute()
    if root.resolve() != root or not root.is_dir() or not 1 <= args.wait <= 600:
        parser.error('Expected a real local directory and a bounded wait')
    info = root.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        parser.error('Expected a private directory owned by the current user')
    if any(not x.name.endswith('.app') for x in root.iterdir()):
        parser.error('Expected a new session directory')
    token = uuid4().hex
    assert re.fullmatch(r'[0-9a-f]{32}',token)
    publish(root/'session.json', {'scope':SCOPE,'run_id':token})
    try:
        evidence = run(root, token, args.wait)
    except TaskError as error:
        evidence = {'status':'CANCELLED' if error.code=='DIAGNOSTIC_OPERATOR_CANCELLED' else 'BLOCKED',
                    'code':error.code}
    evidence.update(scope=SCOPE,run_id=token,recorded_at=stamp(now()),approval_gate='BLOCKED_APPROVAL_PLATFORM')
    publish(root/'result.json', evidence)
    print(json.dumps(evidence, ensure_ascii=True, sort_keys=True),flush=True)
    return 0 if evidence['status']=='INACTIVE_PIN_STAGED' else 2


if __name__=='__main__':
    raise SystemExit(main())
