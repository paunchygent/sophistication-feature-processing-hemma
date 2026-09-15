# Integration notes: candidate, not a live acceptance result

## Scope and authority

Base: `53610a5af9f51f2792b898cf8016f7c37b9a8bb6`. The uploaded Repomix was reconstructed and all 37 selected file hashes matched its manifest. Runtime evidence is dated 15 September 2026. Only that package is repository authority; public documentation below is external evidence. No live repository write, host installation, deployment or readiness judgment is represented by this delivery.

Apply the whole patch set before building. The updated worker requires engine I/O revision 2; an old engine is deliberately rejected rather than handled through a compatibility implementation. Do not replace the pinned image, model or original TAALES binary while measuring this change.

## Target and why

Keep the proven streamed LXQt desktop. Move only JASP's execution across the Docker boundary to the host user, where the official Flatpak can use the host's normal namespace support. Share that application's display with the existing desktop, not another web desktop. This avoids a custom Qt/R/module build and avoids the established nested Bubblewrap failure. A user socket plus one fixed helper is the entire launch bridge; systemd owns process lifetime. No restart policy, retry loop, queue, scheduler, heartbeat, supervisor or arbitrary execution protocol is added.

The host/user manager and native host Flatpak are consequential assumptions. The setup script performs `flatpak run --user --command=true org.jaspstats.JASP` before the bridge is installed. That proves sandbox creation only. If it fails, this host-runtime assumption is false and must be resolved as a host fact; do not add the previously rejected Docker privilege experiments. The separate JASP proof must still exercise a window, data, an R-backed analysis and saving.

## Critical file groups

| Files | Change |
| --- | --- |
| `host/hemma-jasp.py`, socket/service units, `app/jasp_client.py` | Fixed launch request, UID check, one X11/authentication preflight, host process lifetime independent of client |
| `scripts/setup-jasp-host.sh`, `scripts/deploy-hemma.sh` | Native host Flatpak; recorded release/commits; systemd bind mount of existing volume; socket/linger provisioning; deployment prerequisite checks |
| `Dockerfile`, `compose.yaml`, `bin/require-xauth.py`, init script | Retain pinned desktop; authenticated shared Unix X11; same-path durable aliases; no unconfined seccomp; bounded NLP settings |
| `suite_launcher.py`, desktop entries, navigation, `workshop-launch` | Peer tools, explicit real home entry, no blocking JASP wait/unread pipe, retain LXQt autostart |
| `workshop_taales.py`, `launch-taales-window` | General route-card folder pickers, copy paths, manual actual application selections, fit width as well as height |
| TAALED engine, common/performance/worker modules | Ordered batch stream; set membership; explicit process policy; small status writes; measurements; existing publication unchanged |
| Focused tests | Synthetic calculation invariance, stream order/count, process policy, CSV order, status cost, bridge contract, actual local X authentication |

## Adaptation points to close on Hemma

**Host identity and service manager.** The supplied Compose uses PUID/PGID 1000/1000. Match these to the owner running the host user services and the actual home. `SO_PEERCRED` rejects another UID. The design assumes local, rootful Docker without UID remapping, a local volume driver, a Linux systemd user manager, native Flatpak and working user D-Bus. The setup explicitly enables lingering. Confirm that host choice and inspect the generated user units; no host D-Bus is mounted into Docker. The host helper assumes standard `/usr/bin` paths for Flatpak, mountpoint, Python and xdpyinfo. The preserved package does not establish host OS or these prerequisites.

**Host X display and inherited script.** Reserve `:1`; do not run this alongside an unrelated host X server on that display, and do not delete its socket or lock to force availability. Hemma's Docker is the Snap build, whose daemon resolves bind sources in a private `/tmp`; the shared X socket directory is therefore `~/.local/state/hemma-workstation/x11`, exposed by a setup-installed host bind mount at `/tmp/.X11-unix` and by Compose at the container's `/tmp/.X11-unix`. Reconcile the actual pinned image's `svc-xorg/run` and initialization dependencies. `bin/require-xauth.py` fails if the expected `-ac` seam has drifted. Verify that cookie initialization precedes Xvfb and that all desktop/stream clients inherit XAUTHORITY. TCP remains disabled. The shared X cookie is 0600 in an owner-only host directory; it is not a distributable artifact. It carries two entries for one secret: a FamilyLocal entry for the container hostname, which python-xlib clients such as Selkies input require, and a FamilyWild entry for host clients such as JASP. This is a trusted single-user desktop, not isolation between mutually untrusted tools. The original home read/write exposure already grants substantial host-user access.

**Existing volume and paths.** Inspect the exact volume name, driver and source before the setup's systemd bind mount. The script refuses a different or nonempty destination and never creates a replacement research volume. `/srv/hemma-workstation/workspace` becomes the same path in host and container; `/config/workspace` remains the original mount. `/home/paunchygent` becomes the common home path while `/hemma-home` remains available inside Docker. There is no copy, output merge or broad data chown. Existing receipts/preferences can still use original aliases inside the container. New navigation points at common paths, by replacing only installer-owned symlinks. Host reboots must restore the bind mount before JASP data access; its preflight refuses a missing mount.

**Flatpak release and graphics.** The selected reference is JASP 0.98.1. Setup refuses another application version and records exact application and runtime commits. This is an installed-version check and receipt, not a claim that a future Flathub resolution is immutable. Freeze the actual chosen refs locally for reproducible redeployment and keep their receipts with private run-environment records. Do not invent release/runtime hashes. The host launcher uses documented `--safeGraphics`, X11 rather than Wayland, and Qt's `QT_XCB_NO_MITSHM` to avoid depending on cross-namespace SysV shared memory. It adds no `--no-sandbox` or WebEngine sandbox disabling. Confirm software rendering, module availability and filesystem access in the actual launch proof. Analysis code and data remain local unless the user explicitly chooses an online JASP feature; no such feature is enabled by these patches.

**Full-repository artifacts.** The Repomix deliberately omits the two lexical payloads and supplied portrait binary. They are required by the actual build. Preserve them and record their hashes. TAALES stays at `tools/taales_2.2/TAALES_2.2` in the same durable volume, with its original working directory and no new flags. The snapshot's shell executable modes are not encoded in XML; reconcile existing repository modes while applying the text patches.

## Minimal latency work

Keep 30 fps as the reference; Compose exposes it as `WORKSTATION_FRAMERATE` rather than silently choosing a new value. Try the documented browser CSS cursor setting, separating pointer feel from actual application input-to-frame latency. Verify this setting exists in the pinned Selkies build. Leave encoder choice and resolution unchanged initially. In one controlled Mac test compare native dimensions with 1920x1200 at 30 fps; separately compare 30 and 60 fps at the same dimensions. Record effective dimensions, codec, browser/device scale, encode/decode/load and input response. The old resolution experiments did not cure the GTK crash, and are not proposed as a cure now. A lower pixel workload or local cursor is not itself a measured latency improvement. Do not stack stream scaling, browser zoom and Tk DPI without checking legibility.

The candidate removes the unconfined seccomp entry because the failing nested runtime is gone. Verify ordinary Docker seccomp with all retained applications; a failure should identify a specific remaining syscall/runtime need, not trigger blanket privilege restoration. Keep SSH compression off and both loopback forwards exactly as supplied. No GPU device is added without evidence of a useful host GPU/encoder.

## Routine reconciliation, not another subsystem

Update any existing user pin/menu alias to the installed suite entry, and verify keyboard access and desktop launch trust in PCManFM-Qt. There must not be a second entry calling the legacy TAALED GUI. Keep the existing canary asset and Openbox policy correction. Test the new suite status label and all buttons at the actual browser work area and chosen DPI.

For the route card, verify cancelling both new pickers preserves paths; arbitrary home folders work; and the binary's real input/output, extension, overwrite and diagnostic behavior remains as observed. The retained bounded initial window-location wait is placement only, not a watchdog. Copying a proposed prefix is not proof that TAALES accepted it.

The historical Finder helper opens the `Workshops` share. Document it as optional or rename only its visible caption. General Mac file access can use the already available home-share route if configured, but this design neither grants a new SMB share nor assumes its account mapping. Confirm narrow ACL/UID access for 0700 run folders rather than world-writable permissions.

Deploy between runs. Save JASP before any X-server recreation. A browser or SSH disconnect should preserve running applications; restarting the X server is not promised to preserve them. Reset only disposable config, with the nested workspace unmounted/protected. Never reset host home, results, Flatpak data or either data alias to repair a desktop issue.

## External primary sources (consulted 15 September 2026)

- JASP download: https://jasp-stats.org/download/ — 0.98.1 release and official Linux Flatpak route.
- JASP source at v0.98.1: https://github.com/jasp-stats/jasp-desktop/blob/v0.98.1/Docs/development/jasp-build-guide-linux.md — native build dependencies/module bundle maintenance and `--safeGraphics`.
- spaCy API: https://spacy.io/api/language — ordered `pipe`, context tuples and explicit batching/processes.
- spaCy pipelines: https://spacy.io/usage/processing-pipelines — multiprocessing startup and model-copy costs.
- LinuxServer configuration: https://docs.linuxserver.io/selkies/user-guide/configuration/ — frame-rate controls, CSS cursors/scaling, fixed-resolution semantics and seccomp caveat.
- Comparable upstream Xvfb launcher, not proof of the exact pinned image contents: https://github.com/linuxserver/docker-baseimage-selkies/blob/0bd500a32b29e0b234361ce0977b97fea54e7c83/root/etc/s6-overlay/s6-rc.d/svc-xorg/run
- Flatpak supported arguments: https://docs.flatpak.org/en/latest/flatpak-command-reference.html
- Qt XCB implementation: https://github.com/qt/qtbase/blob/dev/src/plugins/platforms/xcb/qxcbconnection_basic.cpp — `QT_XCB_NO_MITSHM`; retrieved blob `314ffcbf2202655917cece9d38e42ebb92be868a`. Match the installed runtime implementation during validation.
