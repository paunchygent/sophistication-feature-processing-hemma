# Source map and provenance

## Supplied repository authority

Uploaded files: `gothenburg-lexicon-offline-architect.json` and `gothenburg-lexicon-offline-architect.xml`.

- Governing task: `GOTHENBURG-LEXICON-WORKSHOP-ADVISORY`.
- Isolated advisory repository head: `f7788f6c8d8067c39835ab76549f3811856ecca3`, main, clean in the receipt. This is not an independently established current materials-repository or live-system revision.
- Specification revision: `8218a0f2b85590bb14c0a589002a165bb3462a2499033161eb966c7c18e9c589`.
- Selected input revision: `340a9770abbc83698e304366d4f015a9209f7939e5abebb1f5bee6a50c808e78`.
- Package revision: `02dbaeebb4b51e0bd8af2ecfaa8426d94949dd424fdb54c8f65f4e3fd71b33e6`.
- XML SHA-256, verified locally: `eabf438401d4ba03ad4fdb8b315266918d2c47ec697d2c06aa4dff3be3314803`.
- Runtime observation: `2026-09-15T11:31:31Z`, with some later same-day rereads. Stream geometry and CPU H.264 are supplied operating context in that observation, not an independently repeated measurement.

| Supplied file | Consequential source evidence | Candidate response |
|---|---|---|
| `evidence/tools/TAALED_1_4_1_Hemma.py` | `start_thread`, `MyApp`, `runprogram`, `main`; fixed geometry, shared output name, unrestricted starts, empty-picker handling, current spaCy loader | Separate GUI/one-run worker; preserve plain options; contained I/O patch; no numerical redesign |
| `evidence/tools/TAALED_1_4_1_original.py` | Original loading API and calculation functions | Comparison/provenance only; not the rollback target for the working patch |
| `evidence/launchers/container-desktop-entries.md` | Exact executable/interpreter paths and working directories; no editable TAALES source | Preserve tool locations, add wrappers/menu entries, do not invent binary flags |
| `evidence/runtime/live-snapshot.md` | Loopback mappings, two named mounts, 96 DPI, 30fps, empty Navigation, unidentified image/version | Add navigation and explicit controls; preserve baseline; version-sensitive live rereads |
| `evidence/workspace/START-HERE.txt` | Canonical deep input/smoke/output routes; obsolete claim that patch only changes model loading | Correct instructions and distinguish runtime data from distributable support |
| `evidence/metadata/data-inventory.md` | 500 text records, archive metadata, result inventory only | Compute current visible `.txt` count; do not package texts/results or treat aggregate inventory as exact live identities |
| `evidence/materials/README.md` | Materials checkout contains texts, results, readings and presentation | Treat materials as a separately provisioned runtime tree, not the support release |
| `evidence/macos/Mount-Hemma.redacted.command` | Keychain retrieval and interpolation of password into `mount_smbfs` argument; two fixed shares | Optional Finder-native Workshops-only route; do not distribute the redacted script as an executable template |
| `evidence/macos/mount-shortcuts-notes.md` | Actual tunnel launcher not captured; private SSH data intentionally absent | Local alias adaptation, no assumed missing tunnel and no exported SSH material |
| `PROVENANCE.md`, `PACKAGE-README.md`, commissioning request | Advisory-only authority and explicit exclusions | No live access/change or readiness verdict; explicit source allowlist |

`core-invariance.json` records the 15 nested calculation functions compared by Python AST and the candidate source hash. It is not a claim of numerical equivalence for the real model or historical reference results.

## External technical documentation, separate from repository facts

Public documentation was consulted on 15 September 2026. No connected user repository, host, Mac account or live service was inspected. The following describe documented APIs or current upstream behavior, not versions proven installed in the snapshot. Recheck against the actual image/interpreter/client before applying a setting.

- LinuxServer Webtop: https://docs.linuxserver.io/images/docker-webtop/ — port/persistence/security documentation and image-dependent configuration.
- LinuxServer Selkies configuration: https://docs.linuxserver.io/selkies/user-guide/configuration/ — frame rate, manual dimensions, scaling DPI and CSS scaling; fixed values may lock controls.
- LinuxServer Selkies web client: https://docs.linuxserver.io/selkies/user-guide/web-client/ — client resolution and scaling controls.
- LinuxServer Selkies: https://docs.linuxserver.io/selkies/ — platform context; current upstream documentation is not evidence that the observed XFCE/X11 installation should be migrated.
- XFCE Appearance: https://docs.xfce.org/xfce/xfce4-settings/appearance — font DPI and window scaling controls.
- OpenSSH `ssh_config`: https://man.openbsd.org/ssh_config — forwarding failure, server-alive probes, host verification, compression and dedicated control connections.
- Freedesktop Desktop Entry, Exec: https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html — execution/quoting rules; Exec is not a shell program.
- Python Tkinter: https://docs.python.org/3/library/tkinter.html#threading-model — event-loop/threading constraints; the candidate keeps all GUI work in the Tk process.
- Docker restart policies: https://docs.docker.com/engine/containers/start-containers-automatically/ — restart policy does not resume an interrupted application.
- Docker volumes: https://docs.docker.com/engine/storage/volumes/ — persistence independent of container lifetime, distinct from process recovery.

The design does not select or defend a new NLP model on research grounds. It keeps the already patched model call, records actual versions/resources at runtime and explicitly leaves historical equivalence unproven.
