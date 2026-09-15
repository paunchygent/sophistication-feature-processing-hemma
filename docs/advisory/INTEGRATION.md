# Integration, owner choices and rollback

## Working boundary

The provided observation is dated **2026-09-15 11:31:31 UTC**, with some later same-day file rereads. The source package is an isolated advisory staging repository. Codex must reread the actual target files and effective runtime configuration immediately before an authorized change. Parallel UI work is not represented after that observation.

Recommended next use is additive integration into the existing image, not an image upgrade. The new GUI is an inspectable candidate implementation. Where current live work already supplies better navigation or layout, reuse it and bring across the path, run-state and output-safety behavior instead of replacing that work.

## Compact integration map

| Target surface | Responsibility | Input/output route | Verification |
|---|---|---|---|
| `/config/workshop-support` | Versioned code and guidance only | No runtime output inside this tree | Source-only inventory; no symlink traversal; checksums |
| `/config/Navigation` | Four stable, readable aliases | Inner input, smoke input, output, materials | Resolve all four as the actual desktop user; exercise Tk and TAALES pickers separately |
| Desktop and per-user application menu | A single discoverable entry per action | Wrapper to GUI, binary route card, navigation/output and appearance settings | Launch by mouse and keyboard; check executable/trust metadata and working directories |
| Existing TAALED source | Computational owner, contained I/O patch | Frozen filename list + plain integer options -> caller-owned new CSV/diagnostics | Apply against fresh source; AST/math comparison and before/after current-environment run |
| New TAALED GUI/worker | Defaults, ergonomics, one-worker coordination, incomplete/complete distinction | Input folder -> `output/taaled/<run-id>[.incomplete]/` | Invalid paths, cancellation, duplicate launch, worker exit/kill and reconnect |
| `/config/.local/state/gothenburg-workshop` | Private settings, active-run pointer and OS lock | No essay bodies; metadata/logs are still runtime-only | Reopen, corrupt/missing settings, write failure; never use the presence of a lock file as proof |
| TAALES wrapper | Unmodified executable plus accurate route guidance | Same input -> proposed `output/taales/<launch-id>/taales.csv` | Set actual pickers manually, inspect the produced file, test program exit/interruption |
| XFCE/Tk/Selkies controls | Independent, understandable display controls | Stream dimensions; XFCE font DPI; Tk point-to-pixel scaling | Actual browser, screen work area and both tools' dialogs at each selected profile |
| Mac tunnel | Dedicated start/status/stop for two loopback forwards | Mac 13000/13001 -> Hemma loopback 13000/13001 -> existing container mappings | SSH control check, HTTP response, WebSocket/video and user-input test; port-collision test |
| Finder shortcut | Optional native authentication and Workshops access | Tailscale-only SMB, independently mapped to runtime by the operator | Finder login/Keychain, actual share path, group/UID permissions, copy and reopen |
| Existing container definition | Preserve working deployment and both named volumes | Same image and private bindings | Restart and isolated recreation with exact image; test volumes independently |

## File application details

Keep the application/resources where observed. Install support under `/config/workshop-support` as the desktop user or with the appropriate ownership; do not broadly chown `/config`, `/hemma-home` or the workspace. The existing virtual environment stays at `/config/taaled-venv`.

`patches/taaled-io.patch` is relative to `/config/workspace`. Its baseline source SHA-256 is `e268113aadfd7f2745fde4cf1717f3b9bcb774e07401d7a6824ded41549f565b`. Recheck actual current source, preserve a private rollback copy, and use `git apply --check` in a staging checkout before applying/reconciling hunks. Most output-loop diff size is indentation under explicit file contexts. The complete candidate file is provided for comparison, not as permission to erase live edits. The old GUI code is retained in that engine file; the new public launcher calls `workshop_gui.py`, not the old `__main__` block.

Provision `output/taaled` and `output/taales` under the runtime workspace with suitable local ownership. Input, materials and smoke input must already be present; the navigation installer refuses missing destinations. It does not download or unpack any data.

After staging the support tree, run `bin/install-navigation.py` for its read-only plan. `--apply` creates only absent, owned entries. Conflicting entries cause an error before creation. Identical pre-existing items are not claimed for rollback. `--rollback` removes only unchanged additions recorded by this installer and preserves subsequently modified items. No installer can safely promise a cross-file transaction after power loss: inspect its short owned-file manifest after an interrupted install.

The installer does not move old launchers, rewrite the XFCE panel, or export/import an XFCE profile. Locate the actual old desktop/menu filenames, take targeted backups, then reconcile them so users are not offered both legacy and candidate TAALED execution paths. Launcher executability does not establish XFCE trust metadata: test that behavior in the installed version. Pin Start Here, both tools and Workshop Files in the existing panel manually, rather than overwriting panel XML. Optional Thunar bookmarks should be merged into the existing bookmarks file, not substituted wholesale. Tk's picker does not depend on those GTK bookmarks; real directory aliases are the common path.

## Display profile options

Keep the existing 30 fps baseline. Compare one setting at a time on the actual Mac/projector.

| Profile to evaluate | Remote pixel dimensions | Intended tradeoff |
|---|---|---|
| Native reference | Observed 2616 x 1640, 30 fps | Retains detail; highest nominal pixel workload among these choices |
| Balanced first experiment | 1920 x 1200, 30 fps | About 54% of the reference pixel count; test legibility before retaining |
| Lower-load fallback | 1600 x 1000, 30 fps | About 37% of the reference pixel count; less room and possible scaling softness |

Those percentages are arithmetic, not measured bitrate, CPU or latency gains. The reference stream geometry was supplied context rather than independently measured in the uploaded observation. Read the actual remote dimensions, browser viewport, device-pixel ratio, client scale and effective encoder before attributing small text or slowness to a cause.

Start with one desktop-font adjustment, such as XFCE 120 DPI, if needed. TAALED's Text DPI explicitly uses Tk scaling = DPI/72, with a System reset. Do not stack 2x GTK scaling, browser zoom, CSS stretching and explicit Tk DPI without checking the combined result. A fullscreen browser and a maximized application are different operations. A larger TAALED window alone does not make its text larger.

Current public LinuxServer documentation lists manual dimensions, `SELKIES_SCALING_DPI` and CSS scaling, and explains that setting manual dimensions locks them. These are version-sensitive adaptation points, not evidence of installed support. Prefer client settings for the experiment. Only move a chosen profile into the owner's real deployment definition after matching its supported settings/schema. Do not paste a guessed persistent environment overlay into an unidentified service or recreate the container just to try font sizing.

Do not assume `GDK_SCALE` changes the opaque TAALES application. Test its actual toolkit/dialog behavior. If it ignores desktop DPI, a whole-stream scaling or lower-resolution profile may help without binary modification. Confirm the blur/space tradeoff on the real display.

## Tunnel and Finder specifics

The tunnel shortcut resolves the local alias `hemma-workshop`, or `WORKSHOP_SSH_ALIAS`, through the Mac's private SSH configuration. Confirm the actual host identity normally before using its strict host-key check. No keys, identities, usernames or known-host files belong in support. Reconcile inherited SSH `LocalForward` settings so this shortcut is the sole owner of its two forwards; do not duplicate a working launcher or kill an unrelated listener. Its stop action addresses only its own SSH control socket.

Both endpoints bind explicitly to 127.0.0.1. Remote targets are host ports 13000 and 13001, not container ports 3000 and 3001. Forwarding creation is distinct from backend availability: the shortcut also checks HTTP, but neither check proves streaming/input works. Keep compression off as an experiment appropriate to the already encoded stream, not as a promised latency cure. It does not automatically reconnect: run start again after loss. Automatic launchd supervision is an optional later operator choice, not another required daemon.

Retain the supplied HTTP loopback route unless an actual browser capability failure warrants a separate HTTPS test through 13001. Current upstream HTTPS guidance does not establish failure of this observed loopback route. Check the actual browser's secure-context/video/clipboard behavior; do not broaden network bindings or disable SSH host verification as a workaround.

The Finder shortcut is a safer **distribution alternative**, not a behavior-identical replacement of the existing two-share fixed-mount script. It asks Finder to open Workshops; Finder manages authentication/Keychain. Set its server DNS name in local configuration outside support. It does not mount Hemma home or guarantee the existing `/Users/...` mount names. Workflows depending on those mounts require an explicit adaptation. A TCP/445 check is not proof of share access or workspace mapping.

## Recovery and rollback by surface

| Change or interruption | Recovery or rollback |
|---|---|
| New desktop/menu/navigation entries | Installer `--rollback`, then restore only separately backed-up legacy entries. Never delete the whole Desktop/Navigation directory. |
| TAALED GUI and I/O patch | Let any worker finish, or deliberately stop it knowing the run will be incomplete. Restore the fresh pre-change **patched** source and old launcher. Keep all output folders and private receipts. Do not revert to the incompatible original spaCy-loading source. |
| Display/font changes | Record preceding values/screenshots; return to them or TAALED System DPI. Remove only newly introduced manual-resolution overrides. Do not delete the user's entire XFCE/browser profile. |
| Browser tab or SSH loss | Restore the tunnel/browser first and observe the existing run. Do not launch another analysis just because the picture disappeared. |
| TAALED GUI close | Reopen to observe the independent worker. Reopening does not resume work from CSV rows. |
| Worker/container/session loss | Reconnect/reopen; a stale nonterminal receipt without the OS lock is interrupted. Preserve the incomplete folder and start a new whole run. Validate the independent-worker behavior against the actual session manager. |
| New tunnel helper | Stop only its own control connection; restore/use the previously working local launcher. No `pkill ssh`, listener-killing or SSH-directory replacement. |
| New Finder helper | Return to the original private mount shortcut. Unmount only the specifically mounted share after open files are closed. No Keychain export or password-in-argv template. |
| Container tuning/recreation | Restore prior image digest and exact container definition while retaining both original named volumes. Test a recreation with isolated volume copies first. Never use `down -v`, volume prune, or a volume-content reset as rollback. |
| Output folder convention | Keep new folders where they are. Old launchers may use a new explicitly named CSV under the existing output root. Do not merge/overwrite earlier CSVs merely to restore a naming convention. |

The observed `unless-stopped` restart policy concerns container restart, not application or analysis resumption. A manually stopped container is not made active merely by that policy. Persistent files and a live GUI/worker are separate recovery concerns.

## Owner decisions and consequential missing evidence

Obtain the relevant owner choice before switching the GUI/run-output convention, preselecting pedagogical indices, modifying display/container settings, changing fixed Finder mount behavior, changing sharing/access, or changing image/dependency versions. These are not already authorized by this advisory commission.

Re-read the exact image digest/tag/build, Docker definition, PUID/PGID, effective supported Selkies settings, restart/volume mounts, actual desktop user and font/scaling state. Image identifiers and dependency versions are absent from the package: no complete reproducible container build can be inferred. A persisted venv alone may still depend on the image's Python/shared libraries. Treat same-container restart and clean recreation as different tests.

Read the current TAALED source, interpreter/Tk/spaCy/model versions and component configuration, resource availability/checksums, the actual `.txt` inventory and chosen pedagogical options. The omitted dependency lists are operational inputs, not replaceable filler. Preserve algorithms; do not repair zero-token/logarithm or short-text conventions by inventing values. Whitespace-only or fully filtered texts can still encounter inherited mathematical edge cases. The wrapper contains failures rather than assigning new scientific meanings.

Read the TAALES binary's local help/version and real input/output/diagnostic behavior. No screenshot, command-line contract, minimum-size evidence or editable source was supplied for it. No custom flags, resource relocation or automatic completion signal are assumed.

Read the actual Mac tunnel launcher and a targeted effective SSH configuration locally, without exporting private files. Read browser build, secure context, WebSocket behavior, frame/encode/decode statistics, CPU throttling and concurrent SMB/load conditions; do not infer a network bottleneck from one geometry observation.

Read the SMB share-to-host-to-volume mapping, account-to-UID/group mapping and permissions. New run folders are 0700 and receipts 0600 by default; a different SMB identity may need a deliberate narrow group/ACL adjustment. Do not solve this with world-writable runtime trees.

Finally, decide the distribution audience and `/hemma-home` exposure. Omitting a Home shortcut is discoverability, not isolation. The delivered support creates no host-home shortcut or mount, but it does not remove the existing live mount. No broad participant access, shared-session isolation or tool/resource redistribution permission is established by the package. Do not copy either mounted volume, `docker commit` a personalized environment, or archive the public materials checkout into the support release: that checkout itself contains excluded data/result/archive material.
