#!/bin/bash
# Finder handles account/password/Keychain. Never put a password into a URL or argv.
# Set WORKSHOP_SMB_SERVER locally, or keep its single DNS name in the private file below.
set -euo pipefail
SERVER=${WORKSHOP_SMB_SERVER:-}
CONFIG="$HOME/.config/gothenburg-workshop/smb-server"
if [ -z "$SERVER" ] && [ -f "$CONFIG" ]; then IFS= read -r SERVER < "$CONFIG" || true; fi
case "$SERVER" in ''|-*|*[!A-Za-z0-9.-]*)
  echo "Set the Tailscale-only SMB DNS name locally in $CONFIG (one line). No account or password belongs here." >&2
  exit 64 ;;
esac
if ! /usr/bin/nc -z -w 5 "$SERVER" 445; then
  /usr/bin/osascript -e 'display alert "Workshop files are not reachable" message "Check Tailscale and the SMB service, then try again."'
  exit 1
fi
exec /usr/bin/open "smb://$SERVER/Workshops"
