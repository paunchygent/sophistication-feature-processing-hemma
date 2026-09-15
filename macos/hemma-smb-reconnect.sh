#!/bin/bash
set -euo pipefail

CONFIG="$HOME/.config/hemma-smb"
STATE="$HOME/Library/Caches/com.paunchygent.hemma-smb-reconnect"
SERVER_FILE="$CONFIG/server"
USER_FILE="$CONFIG/username"

[[ -r "$SERVER_FILE" && -r "$USER_FILE" ]] || exit 0
IFS= read -r SERVER < "$SERVER_FILE"
IFS= read -r REMOTE_USER < "$USER_FILE"
case "$SERVER" in ''|-*|*[!A-Za-z0-9.-]*) exit 64 ;; esac
case "$REMOTE_USER" in ''|-*|*[!A-Za-z0-9._-]*) exit 64 ;; esac

mkdir -p "$STATE"
chmod 700 "$STATE"

# Wait for the actual SMB route, not merely a generic network interface.
if ! /usr/bin/nc -z -w 3 "$SERVER" 445 >/dev/null 2>&1; then
  exit 0
fi

probe_mount() {
  /usr/bin/perl -e '
    $SIG{ALRM} = sub { exit 124 };
    alarm 5;
    opendir(my $directory, $ARGV[0]) or exit 1;
    readdir($directory);
    closedir($directory);
  ' "$1"
}

repair_share() {
  local share=$1
  local marker="$STATE/$share.failed-once"
  local mount_line=
  local mount_point=
  local mounted=false

  if mount_line=$(/sbin/mount | /usr/bin/grep -F "//$REMOTE_USER@$SERVER/$share on " | /usr/bin/head -n 1); then
    mounted=true
    mount_point=${mount_line#* on }
    mount_point=${mount_point% (smbfs,*}
  fi

  if [[ "$mounted" == true ]] && probe_mount "$mount_point"; then
    rm -f "$marker"
    return
  fi

  if [[ "$mounted" == true && ! -e "$marker" ]]; then
    /usr/bin/touch "$marker"
    return
  fi

  if [[ "$mounted" == true ]]; then
    if ! /usr/sbin/diskutil unmount "$mount_point" >/dev/null 2>&1; then
      /usr/bin/logger -t hemma-smb-reconnect "Could not unmount stale $share share; leaving it unchanged"
      return
    fi
  fi

  rm -f "$marker"
  /usr/bin/open -g "smb://$REMOTE_USER@$SERVER/$share"
}

repair_share Hemma
repair_share Workshops
