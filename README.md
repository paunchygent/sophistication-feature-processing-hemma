# Sophistication Feature Processing on Hemma

A general-purpose, Tailscale-only graphical research workstation for TAALED, TAALES, and JASP. It runs on Hemma and is viewed from a Mac through an SSH tunnel at `http://127.0.0.1:13000/`.

The streamed desktop is fixed at `1920x1080` with 125% UI scaling for a 14-inch MacBook display. Browser-driven resolution changes are disabled so reconnects cannot silently change the canvas. The bottom panel uses the conventional application menu, running-applications taskbar, system tray, volume, clock, and show-desktop controls; the workspace switcher and empty quick-launch placeholder are removed.

The application is not tied to one workshop or dataset. File browsers start at the host's `/home/paunchygent`, mounted as `/hemma-home`. ELLIPSE, the private HuleEdu cohort, and Scott Crossley's workshop files appear as optional shortcuts when present.

## Current runnable baseline

- LXQt provides a lightweight but complete working desktop with an application menu, taskbar, desktop surface, PCManFM-Qt file management, terminal, text editor, image viewer, archive manager, process manager, clipboard manager, audio controls, and configuration tools. It uses Openbox for window management. XFCE is deliberately bypassed because its GTK/Glycin icon-loader repeatedly aborts in this container, leaking X clients until the stream fails.
- Scott Crossley's portrait is the desktop canary: if the image is absent, the desktop layer has not initialized correctly.
- TAALED has a responsive GUI and runs analysis in a detached single-run worker.
- TAALES uses the unmodified upstream binary with a route card for copying input and output paths.
- A suite launcher provides TAALED, TAALES, JASP, Hemma Home, dataset shortcuts, and a terminal.
- JASP is represented, but is the remaining runtime gap: its official Linux Flatpak cannot create the required Bubblewrap namespaces inside this Webtop container. The launcher reports that failure plainly.

No watchdog or automatic desktop recovery layer is installed. The current correction replaces the crashing XFCE layer itself.

## Data and results

The service reuses these legacy-named durable Docker volumes:

- `gothenburg-lexicon-workspace` at `/config/workspace` for datasets, tools, and service output
- `gothenburg-lexicon-config` at `/config` for disposable UI configuration and runtime state

The names remain for continuity; they do not define application scope. The host home is mounted read/write at `/hemma-home`.

Known dataset shortcuts:

```text
/config/workspace/materials/data/ELLIPSE_promoted_scorer_input_v1/texts/train
/config/workspace/materials/data/ELLIPSE_promoted_scorer_input_v1/texts/test
/config/workspace/materials/data/HuleEdu_private_catalog_active_students_v1/essays
/config/workspace/materials/data/ICNALE_500_merged_clean_texts/ICNALE_500_merged_clean
```

The ELLIPSE export contains 5,468 training and 2,567 test essays. The private cohort contains 243 essays. Keep input and results under `/hemma-home` or `/config/workspace`; both survive disposable UI resets.

## Deploy and connect

On Hemma:

```bash
git clone https://github.com/paunchygent/sophistication-feature-processing-hemma.git
cd sophistication-feature-processing-hemma
./scripts/deploy-hemma.sh
```

On the Mac:

```bash
./macos/Workshop-Tunnel.command
```

The existing script name is retained for local compatibility. It opens the service only after its loopback tunnel responds.

## TAALED result contract

Choose a flat directory containing lowercase `.txt` files, select indices, and run. Each run writes to a new timestamped folder. A completed folder contains `taaled.csv`, `run.json`, and a worker log. Failed or interrupted work stays in a `.incomplete` folder and is never presented as complete.

The engine currently loads spaCy once per process but calls it sequentially for every essay. Large-run throughput optimization and parity measurement are intentionally left for the architecture pass rather than guessed into this baseline.

## Verification

Build and run the container test target:

```bash
docker build --target test -t sophistication-feature-processing:test .
```

The suite currently has 26 passing tests and two optional historical-reference comparisons that skip when their archive is absent.

The original workshop-focused architect package remains under `docs/advisory/` as historical evidence, not current product authority.

## Upstream tools

- [Scott Crossley's workshop repository](https://github.com/scrosseye/goth_lexicon_workshop)
- [TAALES](https://www.linguisticanalysistools.org/taales.html)
- [JASP](https://jasp-stats.org/download/)
