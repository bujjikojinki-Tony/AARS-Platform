#!/bin/sh
set -eu
if [ "$#" -ne 1 ] || [ "$1" = "${1%.app}" ] || [ -e "$1" ]; then
    printf '%s\n' '请指定尚不存在的 .app 路径。' >&2
    exit 2
fi
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
parent=$(CDPATH= cd -- "$(dirname -- "$1")" && pwd)
destination="$parent/$(basename -- "$1")"
scratch=$(mktemp -d "$parent/.aars-enrollment-build.XXXXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
bundle="$scratch/登记诊断.app"
mkdir -p "$bundle/Contents/MacOS"
cat > "$bundle/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key><string>local.aars.omb.f02-hardware-enrollment</string>
    <key>CFBundleExecutable</key><string>F02HardwareEnrollment</string>
    <key>CFBundleName</key><string>F-02 公钥登记诊断</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleVersion</key><string>1</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
</dict>
</plist>
PLIST
swiftc -module-cache-path "$scratch/module-cache" "$script_dir/check_approval_presence.swift" \
    "$script_dir/hardware_enrollment_app.swift" -o "$bundle/Contents/MacOS/F02HardwareEnrollment"
/usr/bin/plutil -lint "$bundle/Contents/Info.plist"
/usr/bin/codesign --sign - "$bundle"
/usr/bin/codesign --verify --strict "$bundle"
mv -n -- "$bundle" "$destination"
test ! -e "$bundle"
