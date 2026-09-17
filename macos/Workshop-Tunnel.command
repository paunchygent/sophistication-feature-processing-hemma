#!/bin/bash
# The shared Hemma LaunchAgent owns every persistent local forward. This
# shortcut only ensures that singleton is running, verifies the workstation,
# and opens it. It never creates another SSH connection.
set -euo pipefail

ACTION=${1:-start}
DOMAIN="gui/$(/usr/bin/id -u)"
LABEL=com.paunchygent.hemma-shared-tunnel
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

agent_loaded() { /bin/launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; }
listener_ready() { /usr/bin/nc -z -w 1 127.0.0.1 13000 >/dev/null 2>&1; }

ensure_listener() {
  if ! agent_loaded; then
    echo "The shared Hemma tunnel is not installed. Run macos/Install-Hemma-Shared-Tunnel.command once." >&2
    return 1
  fi
  if ! listener_ready; then
    /bin/launchctl kickstart -k "$DOMAIN/$LABEL"
    for _ in {1..100}; do
      listener_ready && return 0
      /bin/sleep 0.1
    done
    echo "The shared Hemma tunnel did not bind port 13000. Inspect $HOME/Library/Logs/hemma-shared-tunnel.log." >&2
    return 1
  fi
}

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
    ensure_listener
    probe
    /usr/bin/open http://127.0.0.1:13000/
    ;;
  status)
    ensure_listener
    echo 'The singleton shared Hemma tunnel is running.'
    probe
    ;;
  stop)
    echo 'This shortcut cannot stop the shared tunnel because other Hemma services use it.' >&2
    exit 64
    ;;
  *) echo "Usage: $0 {start|status|stop}" >&2; exit 64 ;;
esac
