#!/bin/bash
set -euo pipefail

CONFIG="$HOME/.config/hemma-smb"
SERVER_FILE="$CONFIG/server"
USER_FILE="$CONFIG/username"

[[ -r "$SERVER_FILE" && -r "$USER_FILE" ]] || exit 0
IFS= read -r SERVER < "$SERVER_FILE"
IFS= read -r REMOTE_USER < "$USER_FILE"
case "$SERVER" in ''|-*|*[!A-Za-z0-9.-]*) exit 64 ;; esac
case "$REMOTE_USER" in ''|-*|*[!A-Za-z0-9._-]*) exit 64 ;; esac

# Wait for the actual SMB route, not merely a generic network interface.
if ! /usr/bin/nc -z -w 3 "$SERVER" 445 >/dev/null 2>&1; then
  exit 0
fi
MOUNT_TABLE=$(/sbin/mount)

repair_share() {
  local share=$1
  if [[ "$MOUNT_TABLE" == *"//$REMOTE_USER@$SERVER/$share on "* ]]; then
    return
  fi

  # Mount the missing share without asking Finder to open or navigate a window.
  /usr/bin/osascript -e "mount volume \"smb://$REMOTE_USER@$SERVER/$share\"" >/dev/null
}

repair_share Hemma
repair_share Workshops
