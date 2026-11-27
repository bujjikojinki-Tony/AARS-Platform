"""Build the local XPC ping fixture. It contains zero approval or task methods."""
import argparse
from pathlib import Path
import plistlib
import shutil
import subprocess


def build(binary, host):
    service = host/'Contents/XPCServices/local.aars.f02.peer-test-service.xpc'
    for bundle, identifier, is_service in ((host, 'local.aars.omb.approval-broker', False),
                                          (service, 'local.aars.f02.peer-test-service', True)):
        executable = bundle/'Contents/MacOS/PeerFixture'
        executable.parent.mkdir(parents=True)
        shutil.copy2(binary, executable)
        metadata = {'CFBundleIdentifier':identifier, 'CFBundleName':'F02 Peer Fixture',
                    'CFBundleExecutable':'PeerFixture', 'CFBundleVersion':'1',
                    'CFBundlePackageType':'XPC!' if is_service else 'APPL'}
        if is_service:
            metadata['XPCService'] = {'ServiceType':'Application', 'RunLoopType':'NSRunLoop'}
        (bundle/'Contents/Info.plist').write_bytes(plistlib.dumps(metadata))
    for bundle, identifier in ((service, 'local.aars.omb.approval-service'),
                               (host, 'local.aars.omb.approval-broker')):
        subprocess.run(['codesign', '--force', '--sign', '-', '--identifier', identifier, str(bundle)], check=True)
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
