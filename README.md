# Node 24 Buffer GC patch

**Verified on Linux x64. Independent preview, not an official Node.js release.**

[![Compiled artifact verification](https://github.com/Neurovate-Agency/node24-buffer-gc-patch/actions/workflows/recheck.yml/badge.svg)](https://github.com/Neurovate-Agency/node24-buffer-gc-patch/actions/workflows/recheck.yml)

A reproducible Node 24 source patch and build/test harness for the short-lived
Buffer garbage-collection regression tracked in
[nodejs/node#61967](https://github.com/nodejs/node/issues/61967) and
[nodejs/node#63863](https://github.com/nodejs/node/issues/63863).

The candidate restores the earlier 8 MiB scavenger-capacity default on builds
without pointer compression and V8 older than 14. Explicit command-line flags
still override it. It is a scoped workaround, not a backport of V8's newer
external-memory-accounting implementation.

## Verified results

- Both unpatched and patched runtimes compiled from the same source revision.
- **4,751 parallel/sequential test cases, zero failures** (includes upstream
  skips for unsupported platform/features).
- Compiled-default, explicit-override, retained-buffer and worker-transfer checks passed.
- The Readable/Buffer reproducer measured **2.23× median throughput** in a
  15-sample-per-binary rerun; the first runner measured 2.11× across seven samples.

See the [green verification run](https://github.com/Neurovate-Agency/node24-buffer-gc-patch/actions/runs/39209351792),
[full validation record](VALIDATION.md), and [raw evidence](evidence/).
Performance gains are specific to the measured workloads and machines.

## Why this helps

V8 13.6 raised the capacity default from 8 to 32 MiB. Without pointer compression,
this pushes the young external-backing-store collection threshold above the
external-memory soft limit. Short-lived Buffers can then trigger major collections
before a young collection reclaims them. Restoring the older default addresses
that ordering, but can also affect workloads that benefit from a larger young heap.

## Reproduce

The workflow pins Node source commit
`0d10bfe3cb961ef997490f5c060bd1466b5affea` (v24.x).
It builds an unpatched binary, applies the patch, then rebuilds the changed code.
It runs a compiled-default/override regression test, the upstream parallel and
sequential suites, and interleaved benchmark samples against the unpatched binary.
Logs, raw benchmark samples, runtime metadata, and checksums are retained as Actions
artifacts. Timings are observations, not a promise of speedup for other applications.

Linux prerequisites: Git, GCC/G++ 12.2 or newer, Python 3, Make, and the other
[Node build prerequisites](https://github.com/nodejs/node/blob/v24.x/BUILDING.md).

```sh
bash scripts/build.sh
python3 scripts/verify.py node-source results
python3 scripts/compare.py node-source results --runs 7
results/node-patched scripts/stress.cjs
cd node-source
mkdir -p /tmp/n24-tests
NODE_TEST_DIR=/tmp/n24-tests python3 tools/test.py --mode=release -j 4 parallel sequential
```

To try the established workaround without building a custom runtime:

```sh
node --scavenger-max-new-space-capacity-mb=8 app.js
```

Benchmark your own workload first. Do not use this flag on runtimes that no longer
expose it. This repository does not change your installed Node or your application.

The custom build changes the default for the entire process. Applications that
benefit from larger young heaps may behave differently. Explicit
`--scavenger-max-new-space-capacity-mb=32` restores the baseline setting. Windows
measurements here use the official runtime with a flag; they do not validate a
custom Windows binary. macOS, ARM64 and Node's full multi-platform CI are outside
the validation performed here.

Windows workload comparison, using your own Node 24 executable:

```powershell
./scripts/windows-check.ps1 -NodePath C:\path\to\node.exe
```

To repeat tests on already compiled Linux artifacts, run the **Recheck compiled
artifacts** workflow with a build run ID. It verifies binary checksums before
executing tests. This avoids another full compilation while retaining the exact
same executables.

## Attribution and scope

Upstream issue reporters and contributors identified this regression and its
mechanism before this repository existed. The stream benchmark is attributed to
santigimeno's reproducer in #63863; eliau2005 documented the bisection and capacity
workaround in the upstream discussion. Node-derived code retains the upstream
license in `LICENSE.node`. Harness additions use `LICENSE`. Development assisted
by OpenAI Codex.

This is an independent patch repository. It is not affiliated with or endorsed by
Node.js, and no upstream acceptance or release is claimed. An upstream submission
requires human review and the Node project's contribution/DCO process.
