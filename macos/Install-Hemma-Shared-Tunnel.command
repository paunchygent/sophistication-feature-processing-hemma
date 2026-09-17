#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DOMAIN="gui/$(/usr/bin/id -u)"
LABEL=com.paunchygent.hemma-shared-tunnel
BIN="$HOME/.local/bin"
AGENTS="$HOME/Library/LaunchAgents"
DISABLED="$HOME/Library/LaunchAgents.disabled"
PLIST="$AGENTS/$LABEL.plist"
MANAGED_PORTS=(13000 13001 18085 19000 19100 28085)
LEGACY_LABELS=(com.hemma.huleedu-tunnel com.hemma.gpu-tunnel com.hemma.sir-convert-a-lot-tunnel)

/usr/bin/install -d -m 0755 "$BIN" "$AGENTS" "$DISABLED" "$HOME/Library/Logs"
/usr/bin/install -m 0755 "$ROOT/hemma-shared-tunnel.sh" "$BIN/hemma-shared-tunnel"
/usr/bin/sed "s|__HOME__|$HOME|g" "$ROOT/com.paunchygent.hemma-shared-tunnel.plist.in" > "$PLIST"
/usr/bin/plutil -lint "$PLIST" >/dev/null

# Retire only the three known previous tunnel agents. Their plists are kept in
# a disabled directory so rollback is explicit and recoverable.
for legacy_label in "${LEGACY_LABELS[@]}"; do
  /bin/launchctl bootout "$DOMAIN/$legacy_label" >/dev/null 2>&1 || true
  legacy_plist="$AGENTS/$legacy_label.plist"
  disabled_plist="$DISABLED/$legacy_label.plist.disabled"
  if [[ -f "$legacy_plist" ]]; then
    if [[ -e "$disabled_plist" ]]; then
      /usr/bin/cmp -s "$legacy_plist" "$disabled_plist" || {
        echo "Refusing to overwrite a different disabled plist: $disabled_plist" >&2
        exit 1
      }
      /bin/rm "$legacy_plist"
    else
      /bin/mv "$legacy_plist" "$disabled_plist"
    fi
  fi
done

/bin/launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true

ports_are_free=true
for _ in {1..50}; do
  ports_are_free=true
  for port in "${MANAGED_PORTS[@]}"; do
    if /usr/bin/nc -z -w 1 127.0.0.1 "$port" >/dev/null 2>&1; then
      ports_are_free=false
      break
    fi
  done
  $ports_are_free && break
  /bin/sleep 0.1
done
$ports_are_free || { echo 'A managed port is still owned by another process; the shared tunnel was not started.' >&2; exit 1; }

/bin/launchctl bootstrap "$DOMAIN" "$PLIST"
/bin/launchctl kickstart "$DOMAIN/$LABEL"

listener_ready=false
for _ in {1..100}; do
  if /usr/bin/nc -z -w 1 127.0.0.1 13000 >/dev/null 2>&1; then
    listener_ready=true
    break
  fi
  /bin/sleep 0.1
done
$listener_ready || {
  echo "The shared tunnel was installed but did not bind port 13000. Inspect $HOME/Library/Logs/hemma-shared-tunnel.log." >&2
  exit 1
}

echo 'One shared Hemma tunnel now owns ports 13000, 13001, 18085, 19000, 19100 and 28085.'
echo 'The retired GPU forward on 8082 is excluded because local Docker owns that port.'
echo 'launchd will restart it after sleep or network loss.'
