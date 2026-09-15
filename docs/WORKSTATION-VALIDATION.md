# Four validation campaigns

These are proposed measurements, not invented performance thresholds or live results. Use the actual pinned image, unchanged NLP/model/resources and deliberately selected scientific options. Do not change model versions or preselect easier measures to manufacture speed.

## 1. One frozen correctness/parity slice

Create a read-only local slice of approximately 96 essays, selected across ELLIPSE train/test and the private cohort, including length tails and varied auxiliaries, pronouns, adverbs, punctuation and Unicode. Keep data private. Give files unique names within that slice and preserve the original dataset/name mapping in its private manifest. Add synthetic comma-containing filenames and separately test empty/fully filtered input behavior. An inherited calculation failure remains a failure; do not add substitute values.

Run the supplied baseline and candidate under the same interpreter, spaCy/model/resource hashes, explicit index options, diagnostics setting and `PYTHONHASHSEED=0`. Set OMP/OPENBLAS/MKL/BLIS thread counts to one for both runs. Compare the actual intended option selection, plus a slice pass exercising all implemented measures where their existing preconditions hold.

Compare baseline sequential calls with candidate batches 16, 64 and 128 at one process. Repeat only the best small-batch candidates with two and four processes. These are experiment points, not production-optimal settings. Use a fresh detached worker per run, the candidate CLI's explicit spawn policy, and the existing one-worker lock. Separate cold startup/model loading from sustained processing; repeat the bounded slice rather than assuming the first wall time is representative.

Require identical file identities/order and CSV headers, exact integer counts and initially exact numeric values. Compare diagnostics' token sequences in order and type sections as sets. The engine's HD-D floating-point summation and diagnostic type enumeration inherit set iteration. A changed hash seed can alter low-order digits/type order without changed annotations. First hold it fixed, inspect mismatches and compare annotations before considering a documented numeric tolerance. No tolerance is specified in advance. This is parity with the supplied runnable baseline, not proof against unprovided historical outputs.

Inspect invalid process/batch settings, deliberately wrong/truncated result streams and exceptions. Failed work must remain incomplete, with no final directory. No input may be silently skipped. Keep input bytes frozen: the existing inventory compares filename, size and mtime, not content hashes or immutable storage.

## 2. One full ELLIPSE throughput campaign

After parity, run the chosen configuration on train (5,468) and test (2,567) as two sequential, separately named runs using the existing worker. Combined total is 8,035, not 8,278. The additional 243 private essays are a separate run. Do not merge partitions or collide filenames simply to create one flat directory.

Use the real selected indices. Preserve each run's options and environment receipt. Measure elapsed time from worker start through return, e.g. shell `time -p` around the worker CLI; this includes validation, diagnostics fsync and final rename. `run.json` separately records engine-call wall time, model import/load time, parent calculation/output time, input bytes, files/second, parent plus reaped-child CPU and memory high-water observations. The engine timer excludes final publication. Do not add overlapping timers together.

Record aggregate completed ELLIPSE files/second as `8035 / (train_total_seconds + test_total_seconds)`. Record each partition separately as well. Inspect CSV names/order and parsed row counts, not physical line counts. Final receipts must show all expected files and selected columns.

Sample the live process tree's aggregate memory (prefer proportional set size where accessible) or use an appropriately isolated cgroup measurement. Record peak use, concurrent desktop/JASP use, swap and host memory availability. `largest_reaped_child_peak_rss_kib` is the largest child's peak, NOT aggregate multiprocessing memory. Spawn copies model state; prefetched documents, lexical sets and spaCy vocabulary also use memory. Texts/Docs are streamed rather than retained as one corpus-sized list, but vocabulary growth and long individual documents still matter.

Default remains batch 64 / one process until measurements justify a change. Two/four processes are bounded options, not a promise that they fit or help. The parent still computes TAALED's indices and writes results sequentially; MTLD work or I/O can dominate after annotation improves. If parent reduction dominates, do not add more NLP processes. A further algorithmic optimization would be a separate measured patch with its own parity evidence.

Report absolute throughput if no comparable full baseline timing exists. Compute a speedup only against a measured matching baseline. Select the smallest process count that actually improves throughput without degrading interactive use or causing memory pressure. There is no invented minimum speedup or minute budget.

## 3. One host JASP launch/data/calculation/save proof

Record host OS, user ID, Flatpak version, application/runtime refs and commits. Verify host namespace creation before installing the launch bridge. Confirm the actual inherited Xvfb script now requires the generated cookie, accepts the correct cookie, rejects a missing/wrong cookie, and has no TCP listener. Confirm no unrelated server owns display :1 and that startup ordering supplies the cookie before Xvfb.

Launch JASP by its peer button, without a second tunnel or web port. Verify an actual mapped window and that Flatpak/JASP run on the host as the intended user, not inside Webtop. Open an actual TAALED output CSV and a file in an arbitrary home folder. Verify row/column identities in JASP. Run Descriptives (or an equivalent required R-backed analysis) and verify rendered results. This catches missing modules/engine failures that merely opening the shell does not.

Save a `.jasp` project under an arbitrary home research folder, close/reopen it, and check the same saved file from PCManFM-Qt. Also exercise the shared service-workspace path. Do not mistake a process-created socket acknowledgement for this proof. Inspect the host service journal for post-acknowledgement failures. Missing acknowledgements are ambiguous; check for an existing JASP window before any manual relaunch.

## 4. One desktop/reconnect survival proof

Open the LXQt panel/menu, portrait canary, suite, PCManFM-Qt at Hemma Home, TAALED with a detached run, TAALES, and JASP with saved data. Record Xvfb/session/tool PIDs, mapped window geometries, a baseline X-client count, and recent logs.

Reconnect the actual Mac browser three times and separately stop/start only the supplied SSH tunnel, leaving the container untouched. Recheck video, keyboard, scroll, clipboard, file paths and existing applications after each reconnection. The TAALED worker PID and advancing result status should survive; do not start a duplicate run because the picture disappeared. Record X-client counts after transient clients settle and investigate sustained growth. Look for the specific previous XFCE/Glycin assertions and Xvfb client-exhaustion messages, not just HTTP 200.

As part of the same bounded interaction test, compare cursor mode, native versus 1920x1200 at 30 fps, and separately 30 versus 60 fps at the same dimensions. Record effective codec, dimensions, device scale, encoder/decoder load and observed input-to-frame behavior while analyses are active. Revert an ineffective tuning choice rather than adding a monitoring subsystem. Do not call a lower pixel count a measured latency result.

A distinct planned container recreation may test persistence using saved documents and finished results. It is not a reconnect test and is not expected to preserve unsaved GUI state or an active TAALED process. Retain 5,468/2,567/243 dataset inventories and previously completed results after disposable-config replacement; do not clear the nested workspace.

## Local evidence delivered with the patch bundle

The delivery's `LOCAL-VALIDATION.md` and JSON manifest record exactly which local tests/checks ran. The local tests use artificial lexical resources and synthetic NLP adapters; an actual local Xvfb cookie test is included. Docker image building, native host Flatpak, real JASP, actual model parity, full essays and Mac interaction were not executed in that sandbox.
