#!/bin/bash
# Run once as the Hemma workstation owner, on the HOST, before desktop integration.
# Prerequisites: rootful local Docker; systemd user session; Flatpak, Python, xauth,
# xdpyinfo and the host distribution's D-Bus user-session support. No root JASP.
set -euo pipefail
umask 077
[[ $EUID -ne 0 ]] || { echo "Run as the workstation owner, not root." >&2; exit 64; }
for command in docker flatpak systemctl systemd-escape python3 xauth xdpyinfo sudo mountpoint loginctl; do
  command -v "$command" >/dev/null || { echo "Install the host prerequisite: $command" >&2; exit 69; }
done
systemctl --user show-environment >/dev/null
SUPPORT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
STATE="$HOME/.local/state/hemma-workstation"
WORKSPACE=/srv/hemma-workstation/workspace
VOLUME=gothenburg-lexicon-workspace
# Never create an empty replacement for the existing durable research volume.
source=$(docker volume inspect "$VOLUME" --format '{{.Mountpoint}}')
[[ $(docker volume inspect "$VOLUME" --format '{{.Driver}}') == local ]] || {
  echo "Reconcile the non-local Docker volume driver before creating a host bind mount." >&2; exit 64;
}
[[ "$source" == /* && "$source" != *[[:space:]]* ]] || {
  echo "Reconcile the Docker volume mountpoint for a systemd mount unit." >&2; exit 64;
}
sudo test -d "$source"

flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user --noninteractive -y flathub org.jaspstats.JASP
version=$(flatpak list --user --app --columns=application,version | awk '$1 == "org.jaspstats.JASP" { print $2 }')
[[ "$version" == "${JASP_EXPECTED_VERSION:-0.98.1}" ]] || {
  echo "Installed JASP version is $version; explicitly reconcile the selected release." >&2; exit 64;
}
# Prove host namespace creation before adding desktop integration. A failure stops here.
flatpak run --user --command=true org.jaspstats.JASP
mkdir -p "$STATE/bridge" "$STATE/xauth" "$HOME/.config/systemd/user"
chmod 700 "$STATE" "$STATE/bridge" "$STATE/xauth"
{
  flatpak info --user org.jaspstats.JASP
  printf '\nApplication commit: '
  flatpak info --user --show-commit org.jaspstats.JASP
  runtime=$(flatpak info --user --show-runtime org.jaspstats.JASP)
  printf '\nRuntime ref: %s\nRuntime commit: ' "$runtime"
  flatpak info --user --show-commit "$runtime"
} > "$STATE/jasp-install.txt"

# Create only absent mountpoint directories; never chmod/chown mounted data.
for directory in /srv/hemma-workstation "$WORKSPACE"; do
  if ! sudo test -d "$directory"; then sudo install -d -m 0755 "$directory"; fi
done
if mountpoint -q "$WORKSPACE"; then
  [[ $(sudo stat -c '%d:%i' "$source") == $(stat -c '%d:%i' "$WORKSPACE") ]] || {
    echo "A different filesystem already occupies $WORKSPACE" >&2; exit 64;
  }
elif [[ -n $(sudo find "$WORKSPACE" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Refusing to hide pre-existing contents at $WORKSPACE" >&2; exit 64
fi
install_bind_mount() {  # what where description after
  local unit temporary
  unit=$(systemd-escape --path --suffix=mount "$2")
  temporary=$(mktemp)
  cat > "$temporary" <<EOF
[Unit]
Description=$3
After=$4
RequiresMountsFor=$1

[Mount]
What=$1
Where=$2
Type=none
Options=bind

[Install]
WantedBy=multi-user.target
EOF
  sudo install -m 0644 "$temporary" "/etc/systemd/system/$unit"
  rm -f "$temporary"
  sudo systemctl daemon-reload
  sudo systemctl enable --now "$unit"
}
install_bind_mount "$source" "$WORKSPACE" \
  "Durable Hemma research workspace (existing Docker volume, no copy)" docker.service
sudo install -d -m 0755 /usr/local/libexec
sudo install -m 0755 "$SUPPORT/host/hemma-jasp.py" /usr/local/libexec/hemma-jasp.py
install -m 0644 "$SUPPORT/host/hemma-jasp.socket" "$SUPPORT/host/hemma-jasp@.service" "$HOME/.config/systemd/user/"
# Snap Docker's daemon runs with a private /tmp, so the host's /tmp/.X11-unix is not a
# usable Compose bind source. The X socket directory lives in owner state instead:
# Compose mounts it at the container's /tmp/.X11-unix, and this host bind mount exposes
# the same directory at the host path that Flatpak and xdpyinfo use for display :1.
X11=/tmp/.X11-unix
if [[ ! -d "$STATE/x11" ]]; then sudo install -d -m 1777 -o root -g root "$STATE/x11"; fi
if mountpoint -q "$X11"; then
  [[ $(stat -c '%d:%i' "$STATE/x11") == $(stat -c '%d:%i' "$X11") ]] || {
    echo "A different filesystem already occupies $X11" >&2; exit 64;
  }
elif [[ -n $(find "$X11" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Refusing to hide an existing host X server socket in $X11" >&2; exit 64
fi
install_bind_mount "$STATE/x11" "$X11" \
  "Hemma workstation X11 socket directory (shared with Snap Docker)" systemd-tmpfiles-setup.service
systemctl --user daemon-reload
# Keep the user manager available when the last SSH session disconnects.
# This does not auto-start or restart JASP; only the launch socket is enabled.
sudo loginctl enable-linger "$(id -un)"
systemctl --user enable --now hemma-jasp.socket
printf 'Host runtime installed. Review %s/jasp-install.txt (design reference: JASP 0.98.1).\n' "$STATE"
printf 'Before deployment, reserve X display :1 exclusively for this workstation.\n'
