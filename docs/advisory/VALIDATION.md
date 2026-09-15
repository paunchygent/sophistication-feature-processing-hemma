# Validation record and focused follow-through

## What was actually exercised locally

Date: 15 September 2026. Environment: this response's isolated Linux sandbox, Python 3.13.5, pytest, Tk/ttk and Xvfb. This was not the Hemma image, Mac browser or live workshop runtime.

The uploaded XML's byte-level SHA-256 matched its manifest: `eabf438401d4ba03ad4fdb8b315266918d2c47ec697d2c06aa4dff3be3314803`. The extracted patched TAALED baseline was reconstructed with its terminal newline and matched `e268113aadfd7f2745fde4cf1717f3b9bcb774e07401d7a6824ded41549f565b`. XML text normalization is not a claim of byte identity for every other extracted file.

Command used, with the baseline pointing to a private extraction of the supplied source:

```sh
BASELINE_TAALED=/path/to/uploaded/TAALED_1_4_1_Hemma.py \
  xvfb-run -a -s '-screen 0 1920x1200x24' pytest -q
```

**28 tests passed.** The last full run reported six inherited invalid-escape warnings from `re.sub('\\s+', ...)` in source loaded by the tests. Earlier cold imports also reported the baseline's `is ""` warnings. These are recorded rather than called a warning-free run.

| Local coverage | Evidence and limits |
|---|---|
| Run ownership and failure containment | New output per run; second actual worker process refused; SIGKILL releases the kernel lock and leaves incomplete output; malformed CSV/input identity mismatch and metadata change do not publish; previous completed results remain unchanged |
| Publication boundary | Files are closed, checked and synchronized before rename; a failed auxiliary status update after rename can be recovered from the completed directory's receipt |
| GUI lifecycle | Actual Tk widgets under Xvfb; picker cancellation retains values; index/basic-only validation; Run remains accessible in a 760x500 window at 96/120/144/192 DPI; closing and reopening the GUI observes a separately running test worker |
| Navigation and launch routes | Non-destructive planning, conflicting-file refusal, idempotence and selective rollback; TAALES launch mock receives the exact executable with no invented arguments and its original working directory |
| TAALED I/O and calculation preservation | Resource-relative reads, quoted CSV filenames, exclusive result creation, diagnostic handles; AST comparison of all 15 nested calculation functions with the supplied patched baseline; before/after fields and values match using a synthetic NLP adapter |

The worker tests use a deliberately small fake engine. The calculation tests replace spaCy with synthetic token objects and use artificial strings, not supplied essays. These tests therefore establish neither actual model loading nor numerical agreement with ICNALE reference results. The source-structure comparison is not an empirical equivalence claim.

`git apply --check` and actual application in a temporary tree succeeded against the reconstructed baseline and reproduced the complete candidate byte-for-byte. Git reported 20 added trailing-whitespace lines inherited through output-loop reindentation; no broad formatting rewrite was made.

Shell syntax was checked with `bash -n` for the launch wrapper and both Mac command files. The Mac commands were not executed on a Mac. `desktop-file-validate`, shellcheck and zsh were unavailable; desktop trust, menu integration and macOS execution remain untested. No external dependency was installed to make a live system match this candidate.

## Local/staging proof still required for application

Use a distinct staging container and distinct ports/volume copies. Do not attach a staging session to the live `/config` or workspace volumes. Retain the live baseline before comparing it; parallel UI edits may supersede this package.

1. **Actual environment and core integration.** Reconcile the I/O patch against current source; run syntax/import checks using the installed interpreter, not just local Python 3.13. Confirm Python >=3.10, Tcl/Tk, spaCy, `en_core_web_sm`, resource files, model component configuration and filesystem permissions. Compare the pre-change patched core and candidate with the same model, resources, input copies and options. Compare CSV by filename/column, not directory enumeration order; compare diagnostics without assuming set iteration order. Do not introduce numeric tolerances without explaining why they are needed.
2. **Participant flow.** Exercise both desktop and menu launchers by keyboard and mouse; select Smoke, cancel both pickers, choose the actual inner input directory through Navigation, select options, run, locate CSV and reopen it through Finder. Exercise long paths and all controls on the actual laptop/projector. Confirm the source's lowercase/nonrecursive `.txt` rule against the real inventory. Where authorized, a full run should match the 500 current input identities and have 500 parsed CSV data rows, not merely 501 physical lines.
3. **TAALES binary.** Use its actual GUI to set input and the proposed new output filename. Verify accepted extensions, diagnostic/coverage side effects, write locations, overwrite prompts, window/dialog scaling and real completion behavior. Multiple analyses in one binary session require separate filenames. The route card alone proves none of this.
4. **Interruption behavior.** In staging, disconnect/reconnect the browser and tunnel while a run is active; close only the TAALED GUI and reopen it; kill only the test worker; log out of the X session; restart the container; recreate it from the recorded exact image with isolated copies of both named volumes. Distinguish which actions preserve a process from which preserve only files. Confirm incomplete output stays visibly incomplete. Test disk/permission failure and malformed private status without deleting the lock file or launching duplicate work.
5. **Display and transport experiment.** Keep the same Mac/browser/network and analysis load. Compare native geometry/30fps against 1920x1200/30fps, then 1600x1000/30fps only if needed. Record actual stream dimensions, text legibility, host/container CPU, memory/throttling, encode/decode/frame statistics where available, and observed input/scroll response. Compare cold model loading with a settled run and record concurrent SMB traffic. Pixel-count reductions are not substitutes for measured improvement. No latency or throughput target has been fabricated.
6. **Mac and distribution.** Confirm the effective SSH alias has no competing forwards, test an occupied local port and strict host verification, verify that stop affects only this helper's tunnel, and test real WebSocket/video/input beyond HTTP. Confirm Finder's account, share-to-runtime mapping and narrow permissions. Extract the source-only archive into a clean location, verify checksums and ensure no runtime trees, credentials, binary/model archives or data/results entered the release. Reconcile third-party notices before broader redistribution.

## Live operation is separate

Codex's next live work starts with fresh read-only observations of the target files, image/configuration, mounts, ports, process/run state and desktop session. Any accepted write, restart, source replacement, access change or disruptive test requires the existing appropriate owner authority. This document adds no new gate or approval procedure.

Apply changes only at a point that does not accidentally terminate or orphan a current analysis. Then use a deliberately separate smoke output and confirm the actual participant route. Do not run failure injection, recreate the live container, change image/dependency versions or perform a 500-file reanalysis merely because local tests passed.

## Residual technical risks

Input inventory validation records names, size and modification time, not immutable input bytes. A writer can alter bytes while preserving metadata; input immutability and deeper content provenance would require a separately chosen design. The output lock coordinates candidate workers sharing one local state path; old launchers and other users/state directories are outside it. Linux local-volume locking/fsync behavior and session-manager process lifetimes must be checked in the actual runtime.

Existing numerical edge cases remain, including zero-token/fully filtered selections and logarithm calculations. Failure containment is preferable to inventing scores. The current model may not reproduce historical tokenization, tagging or lemmatization. There is no per-file resume, partial-result acceptance, cancellation protocol, tool-independent completion detector or promised automatic recovery of TAALES.
