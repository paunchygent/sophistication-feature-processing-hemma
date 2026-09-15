# Sophistication Feature Processing on Hemma

A disposable, Tailscale-only graphical workspace for the TAALED and TAALES tools used in Scott Crossley's Gothenburg lexical-analysis workshop.

The service runs an Ubuntu XFCE desktop on Hemma and is viewed from a Mac through an SSH tunnel. Webtop listens only on Hemma loopback ports `13000` and `13001`; it is not published directly to the LAN or internet.

## What this repository contains

- A responsive TAALED 1.4.1 UI with workshop routes, adjustable text DPI, a persistent status receipt, and an independent single-run worker.
- A Webtop image and Compose service pinned to the tested upstream image digest.
- Desktop navigation shortcuts for the workshop workspace and Hemma home directory.
- A TAALES route card plus a resize-only launcher for the unmodified upstream binary.
- Mac SSH-tunnel and Finder-share helpers that keep host names and credentials in local configuration.

It intentionally excludes workshop essay bodies, generated CSV results, credentials, SSH material, the TAALES executable, and private Hemma files.

## Hemma layout

The Compose service reuses these named volumes:

- `gothenburg-lexicon-config` mounted at `/config`
- `gothenburg-lexicon-workspace` mounted at `/config/workspace`

The host home directory is mounted at `/hemma-home`. Set `HEMMA_HOME_PATH` if it is not `/home/paunchygent`.

Expected workshop paths inside the container:

```text
/config/workspace/materials/data/ICNALE_500_merged_clean_texts/ICNALE_500_merged_clean
/config/workspace/output
/config/workspace/tools/taales_2.2/TAALES_2.2
```

## Deploy on Hemma

```bash
git clone https://github.com/paunchygent/sophistication-feature-processing-hemma.git
cd sophistication-feature-processing-hemma
./scripts/deploy-hemma.sh
```

Place the upstream workshop materials in the workspace volume before analysis. Download TAALES 2.2 for Linux from the official tool site, put its executable at the expected path above, and make it executable.

## Connect from macOS

```bash
./macos/Workshop-Tunnel.command
```

Then use `http://127.0.0.1:13000/`. Keep the terminal running while using the desktop.

The tunnel helper uses the existing SSH alias `hemma` by default; set `WORKSHOP_SSH_ALIAS` to override it. The alias owns the user, host, and key selection. Keep `LocalForward` out of that alias because the helper owns the two loopback forwards. The script opens `http://127.0.0.1:13000/` only after the forwarded service responds.

## Using the tools

The desktop provides `00 Start Here`, TAALED, TAALES, Workshop Files, Workshop Output, and Display and Fonts launchers. File pickers start at `/config/Navigation`, whose numbered links lead directly to workshop texts, smoke input, output, and materials. `90 Hemma Home` is the separate route to the server home mounted at `/hemma-home`.

TAALED opens with the 500-text workshop folder and `/config/workspace/output/taaled` selected. Each run executes in an independent worker and publishes a new timestamped directory only after validation succeeds. A completed run contains `taaled.csv`, `run.json`, and a local worker log. A directory ending in `.incomplete` is deliberately retained evidence of an interrupted or failed run.

TAALES is distributed upstream as a packaged binary rather than editable Linux source. Its route card shows copyable input and output paths, then its resize-only launcher enlarges and centers the legacy interface. The binary's own pickers must still be set manually. TAALES appends output names such as `results` to the proposed `taales-` prefix.

## Verified live behavior, 2026-09-15

- TAALED processed all 500 workshop essays and produced a 501-line CSV including the header.
- The integrated independent worker processed a one-file smoke input and published a valid two-row, ten-column CSV plus a complete receipt.
- No TAALED error log was produced.
- The Webtop stream runs at 30 fps to reduce remote-desktop lag.
- TAALED opens at `944x658` inside the ordinary `1024x768` Webtop desktop; its run/status footer remains outside the scroll area.
- TAALES opens with all controls visible in a window capped at `900x1300` and bounded by the available screen.
- The containerized Linux/X11 suite passes 26 tests; two optional historical-baseline comparisons are skipped when their archive is absent.

The generated results are deliberately outside Git.

The original offline architect package is preserved under `docs/advisory/` as design evidence. Runtime paths in that snapshot describe the candidate layout; this README and `docs/START-HERE.txt` describe the integrated `/opt/workshop` image.

## Upstream material

- [Workshop repository](https://github.com/scrosseye/goth_lexicon_workshop)
- [TAALES official page](https://www.linguisticanalysistools.org/taales.html)
