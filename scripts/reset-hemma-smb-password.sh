#!/bin/bash
set -euo pipefail

CONTAINER=hemma-smb
PREVIOUS=hemma-smb-previous
ACCOUNT=paunchygent
IMAGE='ghcr.io/servercontainers/samba@sha256:31b90ea7fe3258d30fccd971c85743b92694605f4b43dc8a4df23a202fced06a'

IFS= read -r PASSWORD
[[ ${#PASSWORD} -ge 20 ]] || { echo "Password input is missing or too short." >&2; exit 64; }
[[ $(docker inspect "$CONTAINER" --format '{{.Config.Image}}') == "$IMAGE" ]] || {
  echo "The running SMB image differs from the expected pinned image." >&2
  exit 64
}

printf '%s\n%s\n' "$PASSWORD" "$PASSWORD" | docker exec -i "$CONTAINER" smbpasswd -s "$ACCOUNT" >/dev/null
ACCOUNT_HASH=$(docker exec "$CONTAINER" awk -F: -v account="$ACCOUNT" '$1 == account { print; found=1 } END { exit !found }' /var/lib/samba/private/smbpasswd)
unset PASSWORD

docker stop "$CONTAINER" >/dev/null
docker rename "$CONTAINER" "$PREVIOUS"

rollback() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker rename "$PREVIOUS" "$CONTAINER" >/dev/null 2>&1 || true
  docker start "$CONTAINER" >/dev/null 2>&1 || true
}
trap rollback ERR

docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  --publish 100.104.109.2:445:445/tcp \
  --env 'SAMBA_CONF_SERVER_STRING=Hemma over Tailscale' \
  --env 'SAMBA_VOLUME_CONFIG_workshops=[Workshops]; path=/shares/workshops; valid users = paunchygent; guest ok = no; read only = no; browseable = yes' \
  --env 'UID_paunchygent=1000' \
  --env 'AVAHI_DISABLE=true' \
  --env 'WSDD2_DISABLE=true' \
  --env 'NETBIOS_DISABLE=true' \
  --env 'FAIL_FAST=true' \
  --env 'SAMBA_VOLUME_CONFIG_home=[Hemma]; path=/shares/home; valid users = paunchygent; guest ok = no; read only = no; browseable = yes' \
  --env "ACCOUNT_paunchygent=$ACCOUNT_HASH" \
  --volume gothenburg-lexicon-workspace:/shares/workshops:rw \
  --volume /home/paunchygent:/shares/home:rw \
  "$IMAGE" >/dev/null
unset ACCOUNT_HASH

for _ in $(seq 1 30); do
  [[ $(docker inspect "$CONTAINER" --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}') == healthy ]] && break
  sleep 1
done
[[ $(docker inspect "$CONTAINER" --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}') == healthy ]]

trap - ERR
docker rm -v "$PREVIOUS" >/dev/null
echo "Samba password updated; the SMB service is healthy."
