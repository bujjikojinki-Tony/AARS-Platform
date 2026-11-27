"""Build the isolated F-02 probe with an explicitly selected local signing identity."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

from build_approval_xpc_fixture import create_layout


def report(status, **details):
    print(json.dumps({"status": status, "approval_gate": "BLOCKED_APPROVAL_PLATFORM", **details}))


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120).stdout


def signing_identities():
    inventory = run("/usr/bin/security", "find-identity", "-v", "-p", "codesigning")
    return set(re.findall(r"^\s*\d+\)\s+([0-9A-F]{40})\s+", inventory, re.MULTILINE))


def build(identity, team, destination):
    scripts = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix=".f02-build-", dir=destination.parent) as staging:
        staging = Path(staging)
        binary = staging / "PeerFixture"
        host = staging / destination.name
        run("/usr/bin/swiftc", "-module-cache-path", str(staging / "swift-cache"),
            str(scripts / "approval_peer_identity.swift"),
            str(scripts / "check_approval_signed_pair.swift"), "-o", str(binary))
        for bundle in create_layout(binary, host, expected_team=team):
            run("/usr/bin/codesign", "--force", "--sign", identity, "--options", "runtime", str(bundle))
        run("/usr/bin/codesign", "--verify", "--strict", "--deep", str(host))
        preflight = json.loads(run(str(host / "Contents/MacOS/PeerFixture"), "--preflight", team))
        if preflight.get("status") != "STATIC_IDENTITY_VERIFIED" or preflight.get("stage") != "bundle_pair":
            return False
        run("/bin/mv", "-n", str(host), str(destination.parent))
        return not host.exists() and destination.is_dir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--identity", help="Exact local identity fingerprint (40 hexadecimal characters)")
    parser.add_argument("--team-id", help="Expected Apple Team ID from the authorized signing configuration")
    parser.add_argument("--destination", type=Path, help="A new .app in an existing local directory")
    args = parser.parse_args()
    if args.inventory:
        if any((args.identity, args.team_id, args.destination)):
            parser.error("Use --inventory separately from the build options")
    else:
        if not re.fullmatch(r"[0-9A-Fa-f]{40}", args.identity or ""):
            parser.error("Specify an exact local signing identity fingerprint")
        if not re.fullmatch(r"[A-Z0-9]{10}", args.team_id or ""):
            parser.error("Specify the expected Apple Team ID")
        target = args.destination
        if (target is None or target.suffix != ".app" or not target.parent.is_dir()
                or target.exists() or target.is_symlink()):
            parser.error("Specify a new .app in an existing local directory")

    try:
        identities = signing_identities()
    except (OSError, subprocess.SubprocessError):
        report("SIGNING_INVENTORY_UNAVAILABLE")
        return 2
    if args.inventory:
        report("SIGNING_INVENTORY_CHECKED", valid_identity_count=len(identities))
        return 0
    identity = args.identity.upper()
    if identity not in identities:
        report("SIGNING_IDENTITY_UNAVAILABLE", valid_identity_count=len(identities))
        return 2

    destination = target.parent.resolve() / target.name
    try:
        if build(identity, args.team_id, destination):
            report("STATIC_IDENTITY_VERIFIED", stage="bundle_pair")
            return 0
    except subprocess.CalledProcessError as error:
        report("SIGNED_BUILD_BLOCKED", stage=Path(error.cmd[0]).name, exit_code=error.returncode)
        return 2
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    report("SIGNED_BUILD_BLOCKED")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
