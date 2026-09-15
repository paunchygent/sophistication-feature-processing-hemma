#!/bin/bash
set -euo pipefail

docker volume inspect gothenburg-lexicon-config >/dev/null 2>&1 || \
  docker volume create gothenburg-lexicon-config >/dev/null
docker volume inspect gothenburg-lexicon-workspace >/dev/null
home=${HEMMA_HOME_PATH:-/home/paunchygent}
[[ -S "$home/.local/state/hemma-workstation/bridge/jasp.sock" ]] || {
  echo "Run setup-jasp-host.sh as the host owner and start its user socket first." >&2; exit 69;
}
mountpoint -q /srv/hemma-workstation/workspace || {
  echo "The host's durable workspace bind mount is missing." >&2; exit 69;
}
mountpoint -q /tmp/.X11-unix || {
  echo "The host's X11 socket directory bind mount is missing; rerun setup-jasp-host.sh." >&2; exit 69;
}

docker compose up -d --build --remove-orphans
docker compose ps
