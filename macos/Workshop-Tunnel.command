#!/bin/bash
# The alias is resolved by LOCAL SSH configuration; no host/user/key is shipped.
# Keep this SSH alias free of LocalForward entries: this script owns these two forwards.
set -euo pipefail
umask 077
ACTION=${1:-start}
ALIAS=${WORKSHOP_SSH_ALIAS:-hemma}
case "$ALIAS" in ''|-*|*[!A-Za-z0-9._-]*) echo 'Use a simple local SSH alias.' >&2; exit 64;; esac
CACHE="$HOME/Library/Caches/gothenburg-workshop"
mkdir -p "$CACHE"
chmod 700 "$CACHE"
SOCKET="$CACHE/tunnel-%C"
check() { /usr/bin/ssh -S "$SOCKET" -O check "$ALIAS" >/dev/null 2>&1; }
probe() {
  local code
  code=$(/usr/bin/curl --max-time 8 --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:13000/) || {
    echo 'SSH may be running, but the forwarded HTTP route is not responding. Check the remote listener/container; do not kill an arbitrary local listener.' >&2
    return 1
  }
  case "$code" in
    2??|3??|401|403) echo "Forwarded HTTP response: $code. Verify the desktop, video and input in the browser." ;;
    *) echo "HTTP responded with $code; inspect the remote service." >&2; return 1 ;;
  esac
}
case "$ACTION" in
  start)
    if ! check; then
      /usr/bin/ssh -M -S "$SOCKET" -fnNT \
        -o ExitOnForwardFailure=yes -o ConnectTimeout=10 \
        -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
        -o Compression=no -o ForwardAgent=no -o ForwardX11=no \
        -o StrictHostKeyChecking=yes -o ControlPersist=no \
        -L 127.0.0.1:13000:127.0.0.1:13000 \
        -L 127.0.0.1:13001:127.0.0.1:13001 "$ALIAS"
    fi
    probe
    /usr/bin/open http://127.0.0.1:13000/
    ;;
  status)
    if check; then echo 'This shortcut owns a responding SSH control connection.'; probe
    else echo 'This shortcut has no responding tunnel. Existing unrelated tunnels are not changed.'; exit 1; fi
    ;;
  stop)
    if check; then /usr/bin/ssh -S "$SOCKET" -O exit "$ALIAS"
    else echo 'No responding tunnel owned by this shortcut.'; fi
    ;;
  *) echo "Usage: $0 {start|status|stop}" >&2; exit 64 ;;
esac
