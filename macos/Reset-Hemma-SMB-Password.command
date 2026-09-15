#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SERVER=${1:-hemma.tail730aa2.ts.net}
ACCOUNT=${2:-paunchygent}
PASSWORD=$(/usr/bin/openssl rand -base64 36 | /usr/bin/tr -d '\n')
trap 'unset PASSWORD' EXIT

/usr/bin/printf '%s\n' "$PASSWORD" | /usr/bin/ssh hemma \
  /home/paunchygent/services/sophistication-feature-processing-hemma/scripts/reset-hemma-smb-password.sh

/usr/bin/security delete-internet-password -a "$ACCOUNT" -s "$SERVER" -r 'smb ' -P 445 >/dev/null 2>&1 || true
/usr/bin/security add-internet-password \
  -a "$ACCOUNT" -s "$SERVER" -r 'smb ' -P 445 -w "$PASSWORD" \
  -T /System/Library/CoreServices/Finder.app/Contents/MacOS/Finder \
  -T /System/Library/CoreServices/NetAuthAgent.app/Contents/MacOS/NetAuthAgent \
  -T /System/Library/CoreServices/NetAuthAgent.app/Contents/MacOS/NetAuthSysAgent \
  -T /usr/bin/security

"$ROOT/macos/Install-Hemma-SMB-Auto-Reconnect.command" "$SERVER" "$ACCOUNT"
echo "The new Samba password is stored in your login Keychain and Finder reconnect is active."
