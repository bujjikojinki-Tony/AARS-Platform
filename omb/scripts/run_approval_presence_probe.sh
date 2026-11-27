#!/bin/sh
# Build and run only the fixed-message diagnosis in an isolated temporary folder.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
probe_tmp=$(mktemp -d "${TMPDIR:-/tmp}/aars-f02.XXXXXXXX")
trap 'rm -rf -- "$probe_tmp"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

swiftc -module-cache-path "$probe_tmp/module-cache" "$script_dir/check_approval_presence.swift" "$script_dir/check_approval_presence_cli.swift" -o "$probe_tmp/probe"
"$probe_tmp/probe" "$@"
