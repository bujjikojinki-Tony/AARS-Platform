"""Build the local XPC ping fixture. It contains zero approval or task methods."""
import argparse
from pathlib import Path
import plistlib
import shutil
import subprocess


def create_layout(binary, host, *, expected_team=None):
    service_id = 'local.aars.omb.approval-service'
    service = host/'Contents/XPCServices'/f'{service_id}.xpc'
    for bundle, identifier, is_service in ((host, 'local.aars.omb.approval-broker', False),
                                          (service, service_id, True)):
        executable = bundle/'Contents/MacOS/PeerFixture'
        executable.parent.mkdir(parents=True)
        shutil.copy2(binary, executable)
        metadata = {'CFBundleIdentifier':identifier, 'CFBundleName':'F02 Peer Fixture',
                    'CFBundleExecutable':'PeerFixture', 'CFBundleVersion':'1',
                    'CFBundlePackageType':'XPC!' if is_service else 'APPL'}
        if expected_team is not None:
            metadata['AARSExpectedAppleTeamID'] = expected_team
        if is_service:
            metadata['XPCService'] = {'ServiceType':'Application', 'RunLoopType':'NSRunLoop'}
        (bundle/'Contents/Info.plist').write_bytes(plistlib.dumps(metadata))
    return service, host


def build(binary, host):
    for bundle in create_layout(binary, host):
        subprocess.run(['codesign', '--force', '--sign', '-', str(bundle)], check=True)
    subprocess.run(['codesign', '--verify', '--strict', '--deep', str(host)], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.destination.suffix != '.app' or args.destination.exists():
        parser.error('Destination must be a new .app bundle')
    build(args.binary.resolve(strict=True), args.destination.resolve())


if __name__ == '__main__':
    main()
