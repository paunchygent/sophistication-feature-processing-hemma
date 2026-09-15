# Sophistication Feature Processing on Hemma

A disposable, Tailscale-only graphical workspace for the TAALED and TAALES tools used in Scott Crossley's Gothenburg lexical-analysis workshop.

The service runs an Ubuntu XFCE desktop on Hemma and is viewed from a Mac through an SSH tunnel. Webtop listens only on Hemma loopback ports `13000` and `13001`; it is not published directly to the LAN or internet.

## What this repository contains

- A patched TAALED 1.4.1 UI with readable sizing, workshop input/output defaults, visible progress, guarded background processing, and an error log.
- A Webtop image and Compose service pinned to the tested upstream image digest.
- Desktop navigation shortcuts for the workshop workspace and Hemma home directory.
- A TAALES launcher that makes the complete legacy UI visible at a usable size.
- A Mac SSH-tunnel helper.

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
./scripts/open-tunnel-macos.sh
```

Then use `http://127.0.0.1:13000/`. Keep the terminal running while using the desktop.

## Using the tools

TAALED opens with the 500-text workshop folder and `/config/workspace/output/results.csv` preselected. Its status progresses from model loading through each processed file. Exceptions appear in the status area and are written to `output/taaled-error.log`.

TAALES is distributed upstream as a packaged binary rather than editable Linux source. Its launcher enlarges and centers the legacy interface. Choose `/workshop-input` as the input and `/workshop-output/taales-` as the output prefix; TAALES appends output names such as `results`.

## Verified live behavior, 2026-09-15

- TAALED processed all 500 workshop essays and produced a 501-line CSV including the header.
- A separate one-file smoke run produced a two-line CSV.
- No TAALED error log was produced.
- The Webtop stream runs at 30 fps to reduce remote-desktop lag.
- TAALES opens with all controls visible in a `900x1300` window.

The generated results are deliberately outside Git.

## Upstream material

- [Workshop repository](https://github.com/scrosseye/goth_lexicon_workshop)
- [TAALES official page](https://www.linguisticanalysistools.org/taales.html)
