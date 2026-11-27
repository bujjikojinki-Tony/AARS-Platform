"""Exercise restart recovery on a disposable copy of an observed F-02 database."""

import argparse
import base64
from datetime import datetime, timezone
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import time
from uuid import uuid4
from zipfile import ZipFile

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from aars_task_manager import Repository, TaskRuntime
from aars_task_manager.approval_enrollment import DOMAIN, EnrollmentAnchor, EnrollmentStore
from aars_task_manager.approval_transactions import ResultDecisionStore
from aars_task_manager.domain import new_id
from aars_task_manager.errors import TaskError


ROOT = Path(__file__).resolve().parents[1]
CRASH_EXIT = 73


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def rejection(expected, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
    except TaskError as error:
        check(error.code == expected, f"Expected {expected}, got {error.code}")
        return error.code
    raise RuntimeError(f"Operation should have rejected with {expected}")


def load_session(session, archive_path):
    with ZipFile(archive_path) as archive:
        manifest_name, = [name for name in archive.namelist() if name.endswith("/MANIFEST.json")]
        manifest = json.loads(archive.read(manifest_name))["files"]
    documents = {}
    for name in ("session", "offer", "challenge", "proof", "result"):
        filename = f"{name}.json"
        raw = (session / filename).read_bytes()
        check(sha256(raw).hexdigest() == manifest[f"observed/{filename}"], f"Archived {name} hash mismatch")
        documents[name] = json.loads(raw)
    check(len({item["run_id"] for item in documents.values()}) == 1, "Session IDs do not agree")
    result = documents["result"]
    check(result["status"] == "INACTIVE_PIN_STAGED" and result["replay_rejected"], "Missing original staging result")
    check(documents["offer"]["source"] == result["proof_origin"] == "SECURE_ENCLAVE_DIAGNOSTIC",
          "Expected the physical diagnostic record")
    message = base64.b64decode(documents["challenge"]["payload_b64"], validate=True)
    check(message.startswith(DOMAIN), "Unexpected signature domain")
    challenge_hash = sha256(message).hexdigest()
    check(challenge_hash == documents["proof"]["payload_sha256"] == result["challenge_sha256"],
          "Challenge digest mismatch")
    point = base64.b64decode(documents["offer"]["public_point_b64"], validate=True)
    signature = documents["proof"]["signature_base64"]
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), point)
    key.verify(base64.b64decode(signature, validate=True), message, ec.ECDSA(hashes.SHA256()))
    fields = json.loads(message[len(DOMAIN):])
    anchor = EnrollmentAnchor(**{field: fields[field] for field in EnrollmentAnchor.__dataclass_fields__})
    check(anchor.pin_sha256 == result["pin_sha256"] == "sha256:" + sha256(point).hexdigest(),
          "Expected public key digest mismatch")
    return anchor, point, signature, challenge_hash


def open_copy(path):
    return Repository.open(path, allowed_root=path.parent,
                           protected_roots=(ROOT / "frozen_archive", ROOT / "frozen_payload"))


def snapshot(repo, anchor, point):
    def inspect(db):
        pins = [tuple(row) for row in db.execute("SELECT * FROM result_operator_pins")]
        check(pins == [(anchor.workspace_id, anchor.operator_id, anchor.key_id, point, anchor.pin_sha256, 0)],
              "Expected exactly one original inactive candidate")
        counts = {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in
                  ("tm_tasks", "task_events", "result_approval_challenges", "result_approval_decisions")}
        check(not any(counts.values()), "Unexpected task or approval data")
        return {"schema": db.execute("PRAGMA user_version").fetchone()[0],
                "inactive_candidates": 1, "active_candidates": 0,
                "counts": counts, "boot_marker": repo.meta(db, "active_boot")}

    result = repo.read(inspect)
    check(result["schema"] == 5 and repo.check_integrity(), "D5 integrity check failed")
    return result


def worker(path, anchor, point, signature, abrupt, channel):
    repo = open_copy(path)
    before = snapshot(repo, anchor, point)
    prior_boot = before["boot_marker"]
    stale = rejection("RUNTIME_INACTIVE", repo.assert_runtime, prior_boot) if prior_boot else None
    with TaskRuntime(repo) as runtime:
        context = {"anchor": anchor, "boot_id": runtime.boot_id,
                   "now": lambda: datetime.now(timezone.utc), "monotonic_now": time.monotonic}
        enrolling = EnrollmentStore(repo, **context)
        approving = ResultDecisionStore(repo, **context)
        evidence = {"pid": os.getpid(), "old_boot_check": stale,
                    "replay": rejection("APPROVAL_ENROLLMENT_CHALLENGE_MISSING", enrolling.stage, point, signature),
                    "replacement": rejection("APPROVAL_ENROLLMENT_EXISTS", enrolling.prepare),
                    "approval": rejection("APPROVAL_KEY_UNTRUSTED", approving.prepare, new_id("task"),
                                          expected_version=1, idempotency_key=str(uuid4()), decision="APPROVE_RESULT"),
                    "during": snapshot(repo, anchor, point), "before": before}
        check(evidence["during"]["boot_marker"] == runtime.boot_id != prior_boot, "Boot marker did not rotate")
        if abrupt:
            channel.send(evidence)
            os._exit(CRASH_EXIT)
    evidence["after_shutdown"] = snapshot(repo, anchor, point)
    check(evidence["after_shutdown"]["boot_marker"] == "", "Shutdown left an active boot marker")
    channel.send(evidence)


def run_process(path, anchor, point, signature, *, abrupt):
    context = multiprocessing.get_context("spawn")
    incoming, outgoing = context.Pipe(duplex=False)
    process = context.Process(target=worker, args=(path, anchor, point, signature, abrupt, outgoing))
    process.start()
    outgoing.close()
    try:
        check(incoming.poll(20), "Worker timed out without a result")
        result = incoming.recv()
        process.join(timeout=10)
        check(process.exitcode == (CRASH_EXIT if abrupt else 0), "Unexpected worker exit")
        return {**result, "exit_code": process.exitcode}
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        incoming.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("observed_evidence_archive", type=Path)
    arguments = parser.parse_args()
    session = arguments.session.resolve(strict=True)
    anchor, point, signature, challenge_hash = load_session(session, arguments.observed_evidence_archive)
    original = session / "database/tasks.sqlite"
    check(original.is_file() and not original.is_symlink(), "Missing isolated diagnostic database")
    check(not any(original.with_name(original.name + suffix).exists() for suffix in ("-wal", "-shm", "-journal")),
          "Source database has a live SQLite sidecar")
    data = original.read_bytes()
    digest = sha256(data).hexdigest()
    with tempfile.TemporaryDirectory(prefix="f02-restart-") as directory:
        path = Path(directory).resolve() / "tasks.sqlite"
        path.touch(mode=0o600, exist_ok=False)
        path.write_bytes(data)
        abrupt = run_process(path, anchor, point, signature, abrupt=True)
        recovered = run_process(path, anchor, point, signature, abrupt=False)
        check(recovered["pid"] != abrupt["pid"], "Expected independent worker processes")
        check(recovered["before"] == abrupt["during"] and recovered["old_boot_check"] == "RUNTIME_INACTIVE",
              "Restart did not observe and reject the stale boot")
    check(sha256(original.read_bytes()).hexdigest() == digest, "Original database changed")
    print(json.dumps({"status": "ISOLATED_ENROLLMENT_RESTART_PASS", "approval_gate": "BLOCKED_APPROVAL_PLATFORM",
                      "archived_records_matched": 5, "historical_signature_verified": True,
                      "challenge_sha256": challenge_hash, "source_db_sha256_before": digest,
                      "source_db_sha256_after": digest, "abrupt_exit": abrupt, "recovery": recovered}, indent=2))


if __name__ == "__main__":
    main()
