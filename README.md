# Hemma Research Workstation

General research work under `/home/paunchygent`, with TAALED, TAALES and JASP as peer tools. The Mac route remains the existing Tailscale/SSH tunnel to `http://127.0.0.1:13000/`. Neither published port is widened beyond host loopback.

The streamed desktop is fixed at `1920x1080` with 125% UI scaling for a 14-inch MacBook display. Browser-driven resolution changes are disabled so reconnects cannot silently change the canvas. The bottom panel uses the conventional application menu, running-applications taskbar, system tray, volume, clock, and show-desktop controls; the workspace switcher and empty quick-launch placeholder are removed.

The application is not tied to one workshop or dataset. File browsers start at the host's `/home/paunchygent`, mounted as `/hemma-home`. ELLIPSE, the private HuleEdu cohort, and Scott Crossley's workshop files appear as optional shortcuts when present.

## Runtime shape

- LXQt provides a lightweight but complete working desktop with an application menu, taskbar, desktop surface, PCManFM-Qt file management, terminal, text editor, image viewer, archive manager, process manager, clipboard manager, audio controls, and configuration tools. It uses Openbox for window management. XFCE is deliberately bypassed because its GTK/Glycin icon-loader repeatedly aborts in this container, leaking X clients until the stream fails.
- Scott Crossley's portrait is the desktop canary: if the image is absent, the desktop layer has not initialized correctly.
- TAALED has a responsive GUI and runs analysis in a detached single-run worker.
- TAALES uses the unmodified upstream binary with a route card for copying input and output paths.
- A suite launcher provides TAALED, TAALES, JASP, Hemma Home, dataset shortcuts, and a terminal.
- JASP runs as the official host-user Flatpak and displays on the same authenticated X11 desktop.

LXQt, Openbox, PCManFM-Qt, Selkies and the two lexical tools stay in the pinned Webtop image. The existing LXQt autostart ordering and targeted Openbox maximize correction remain. XFCE is not started. There is no watchdog or desktop-repair loop.

JASP uses the official **host-user Flatpak**, outside Docker, with its window displayed on the same X11 desktop. A private, fixed-request Unix socket activates one host process through the systemd user manager. It accepts only `JASP/1`, not shell commands, filenames or caller-supplied environment. The application does not depend on the launcher window or an SSH session remaining open. A container/X-server restart can still close JASP; save work first.

The host integration requires native host Flatpak namespace support. `scripts/setup-jasp-host.sh` checks this before installing the bridge. It does not try nested Flatpak, privileged Docker, namespace bypasses, or an alternative installation after failure.

## Durable paths

| Path | Meaning |
| --- | --- |
| `/home/paunchygent` | Ordinary browsing and arbitrary research inputs/results, on host and inside container |
| `/srv/hemma-workstation/workspace` | The existing `gothenburg-lexicon-workspace` volume exposed at the same path to all tools |
| `/hemma-home` | Retained container alias for the host home; no data migration |
| `/config/workspace` | Retained container mount of that same durable volume |
| `/config` outside the nested workspace | Disposable desktop preferences and TAALED active-run state |

ELLIPSE train/test, the private cohort and workshop texts remain optional shortcuts. No dataset is required for opening the desktop or navigating home. TAALED requires a flat folder of visible lowercase `.txt` files. Its input/output pickers and the TAALES route-card pickers start at Hemma Home. TAALES and JASP's own application dialogs remain controlled by those applications.

Completed results are durable, but unsaved application state is not. Never remove `/config` recursively while its nested durable workspace is mounted. Do not use `docker compose down -v` or prune the named research volume.

## Host preparation, then deployment

Before an authorized deployment, finish any TAALED run and save/close JASP documents. Use a separate staging instance for disruptive tests. Confirm the adaptation points in `docs/WORKSTATION-INTEGRATION.md` first.

On Hemma, as the intended desktop owner with a working systemd user session:

```bash
./scripts/setup-jasp-host.sh
./scripts/deploy-hemma.sh
```

Host prerequisites are listed in the setup script. Setup installs the official user Flatpak, verifies the selected release (reference: 0.98.1), tests native host sandbox creation, records application/runtime commits, exposes the **existing** local Docker volume through a systemd bind mount, installs the fixed launcher, and enables the user launch socket. It explicitly enables user lingering so a last SSH logout does not remove that socket or its user manager. It does not enable automatic JASP launching, restarting or updating.

Reserve host X display `:1` for this workstation. Snap Docker's daemon has a private `/tmp`, so the X socket directory is `~/.local/state/hemma-workstation/x11`: setup bind-mounts it at the host's `/tmp/.X11-unix` and Compose mounts the same directory at the container's `/tmp/.X11-unix`. The container exports only the local X11 socket and a private cookie; its inherited `-ac` option is removed at build time. No host Docker socket, D-Bus socket, SSH identity or TCP X11 listener is needed. A build-time mismatch in the inherited Xvfb script stops the build for reconciliation.

PUID/PGID must match the host owner. The candidate retains baseline values 1000/1000. See the integration note before using another account or rootless Docker.

On the Mac, keep using:

```bash
./macos/Workshop-Tunnel.command
```

The existing command filename and two forwards are unchanged. The separate Finder helper still opens the optional `Workshops` SMB share; it is not the general home-navigation contract.

To reconnect the `Hemma` and `Workshops` Finder volumes automatically after a network drop, run once on the Mac:

```bash
./macos/Install-Hemma-SMB-Auto-Reconnect.command
```

The per-user LaunchAgent checks the SMB route once a minute. A missing mount is reopened in the background. A mounted but unresponsive share must fail two consecutive bounded probes before the helper performs a normal unmount and reconnect. It recognizes both the existing home-directory mountpoints and Finder's standard `/Volumes` locations. Finder and Keychain retain control of authentication; the helper stores only the server name and SMB username.

To rotate the dedicated Samba password and save it directly in the macOS login Keychain for Finder, run:

```bash
./macos/Reset-Hemma-SMB-Password.command
```

The generated plaintext password is held only in process memory. Hemma retains Samba's password hash in the disposable SMB container configuration.

## Tool behavior

TAALED uses the existing detached, locked worker and fresh run-directory publication. The engine now streams `nlp.pipe` with explicit batching and filename context. Defaults are `TAALED_BATCH_SIZE=64` and `TAALED_N_PROCESS=1`. Two/four-process experiments are explicit choices, not automatic scaling. The worker CLI also accepts `--batch-size` and `--n-process`.

The spaCy version, model, selected indices, token classification and mathematical calculations remain unchanged. Dependency-list membership uses sets. Runtime measurements and execution settings are recorded in `run.json`. Full input metadata remains there, but is omitted from frequent UI status writes. A failed run stays `.incomplete`; there is no per-essay resume or partial-result acceptance.

TAALES remains the original opaque executable in its original working directory. The route card offers arbitrary input/output browsing, copyable paths and optional presets. It **does not set the binary's pickers**, invent command-line flags, or assert completion. Set its real pickers manually and inspect its resulting CSV.

JASP's launch acknowledgement means the host created a process, not that a window or R analysis has succeeded. Inspect the desktop and, for post-launch failures, `journalctl --user -u 'hemma-jasp@*'`. A missing acknowledgement is ambiguous: check for an existing window before trying again.

## Validation

```bash
docker compose -f compose.yaml -f compose.test.yaml build workstation
```

This command still requires the full repository's omitted lexical resources and wallpaper asset. `docs/WORKSTATION-VALIDATION.md` specifies the parity slice, 8,035-essay ELLIPSE run, JASP data-open/calculation proof and desktop/reconnect proof. Local synthetic tests do not establish any of those live outcomes.

Historical workshop-focused advice under `docs/advisory/` is retained only as history, not the current product boundary.
