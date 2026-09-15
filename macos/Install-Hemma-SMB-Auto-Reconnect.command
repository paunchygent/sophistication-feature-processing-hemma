#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SERVER=${1:-hemma.tail730aa2.ts.net}
REMOTE_USER=${2:-paunchygent}
case "$SERVER" in ''|-*|*[!A-Za-z0-9.-]*) echo "Invalid SMB server name." >&2; exit 64 ;; esac
case "$REMOTE_USER" in ''|-*|*[!A-Za-z0-9._-]*) echo "Invalid SMB username." >&2; exit 64 ;; esac

CONFIG="$HOME/.config/hemma-smb"
BIN="$HOME/.local/bin"
AGENTS="$HOME/Library/LaunchAgents"
PLIST="$AGENTS/com.paunchygent.hemma-smb-reconnect.plist"
DOMAIN="gui/$(/usr/bin/id -u)"
LABEL=com.paunchygent.hemma-smb-reconnect

/usr/bin/install -d -m 0700 "$CONFIG"
/usr/bin/install -d -m 0755 "$BIN" "$AGENTS" "$HOME/Library/Logs"
/usr/bin/printf '%s\n' "$SERVER" > "$CONFIG/server"
/usr/bin/printf '%s\n' "$REMOTE_USER" > "$CONFIG/username"
/bin/chmod 0600 "$CONFIG/server" "$CONFIG/username"
/usr/bin/install -m 0755 "$ROOT/hemma-smb-reconnect.sh" "$BIN/hemma-smb-reconnect"
/usr/bin/sed "s|__HOME__|$HOME|g" "$ROOT/com.paunchygent.hemma-smb-reconnect.plist.in" > "$PLIST"
/usr/bin/plutil -lint "$PLIST" >/dev/null

/bin/launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
/bin/launchctl bootstrap "$DOMAIN" "$PLIST"
/bin/launchctl kickstart "$DOMAIN/$LABEL"

echo "Automatic Hemma SMB reconnect is active."
echo "Finder/Keychain owns the password; this helper stores only server and username."
