# Validation record

## Scope

Source: Node v24.x commit `0d10bfe3cb961ef997490f5c060bd1466b5affea`,
reporting `v24.22.1-pre`, V8 13.6. Both Linux x64 binaries were built from this
same commit, with the same configuration. The patched build adds the source
patch in this repository. No system Node installation was replaced.

Patch SHA-256:
`cc81dcf13867e7afbe3cb790e6b013027129cabb37cbeb6b43c02abda3522fce`.

## Initial Linux build, 19 October 2026 (India time)

[Build and test run](https://github.com/Neurovate-Agency/node24-buffer-gc-patch/actions/runs/39164801172).

- Unpatched and patched source builds succeeded.
- The new regression test failed on the unpatched binary as expected (32 vs 8).
- It passed on the patched binary. Explicit 32 and 4 MiB overrides passed.
- The parallel/sequential run recorded 4,749 successful/skip outcomes and two
  socket-test failures. This run was **not green**.
- The failing socket paths were 110 bytes, exceeding the Unix-domain socket path
  capacity. The subsequent verification run tests that explanation against both
  executables instead of suppressing or deleting the tests.

Seven samples per binary per workload, with alternating execution order:

| Workload | Baseline median ops/s | Patched median ops/s | Change |
| --- | ---: | ---: | ---: |
| Short-lived Readable/Buffer reproducer | 17,353 | 36,661 | +111.3% |
| Buffer churn | 205,800 | 343,371 | +66.8% |
| Retained buffers | 207,156 | 344,978 | +66.5% |
| JavaScript object churn | 41,913,780 | 46,673,316 | +11.4% |

These are workload-specific observations on a shared GitHub runner, not a claim
of universal application speedup. Raw samples are in
[`evidence/linux-first-build/`](evidence/linux-first-build/).

One separate traced reproducer run recorded 22 Mark-Compact collections before
the patch and 3 after it. Scavenges changed from 9 to 78. This is the expected
shift toward reclaiming short-lived backing stores through young collections.

Median peak RSS for the allocation workloads (KiB):

| Workload | Baseline | Patched |
| --- | ---: | ---: |
| Buffer churn | 157,648 | 94,532 |
| Retained buffers | 159,592 | 95,008 |
| JavaScript object churn | 126,672 | 93,456 |

## Linux verification rerun, 19 October 2026

[Green verification run](https://github.com/Neurovate-Agency/node24-buffer-gc-patch/actions/runs/39209351792).
This run reused the exact binaries from the original build after verifying their
SHA-256 checksums; no recompilation or runtime-source change was needed.

- Both binaries failed the two socket tests with deliberately oversized socket
  paths and passed with short paths. This isolated the original environmental failure.
- Setting the upstream-supported `NODE_TEST_DIR=/tmp/n24-tests` fixed the test
  setup. No upstream test was changed, removed, or newly excluded.
- **All 4,751 parallel/sequential test cases completed with zero failures.** This
  count includes normal upstream skips for platform/features not in the build.
- Compiled default and explicit override tests passed again.
- Retained backing-store content, varying allocation sizes and transferred
  ArrayBuffers between workers passed on both compiled binaries.

Fifteen interleaved samples per binary on the second runner:

| Workload | Baseline median ops/s | Patched median ops/s | Change |
| --- | ---: | ---: | ---: |
| Short-lived Readable/Buffer reproducer | 18,150 | 40,481 | +123.0% |
| Buffer churn | 223,859 | 393,059 | +75.6% |
| Retained buffers | 219,431 | 388,087 | +76.9% |
| JavaScript object churn | 43,687,209 | 47,944,276 | +9.7% |

Raw measurements, GC traces, socket controls and the complete suite log are
preserved in [`evidence/linux-recheck/`](evidence/linux-recheck/).

## Windows flag checks

Official Node 24.22.0 x64 was checked against the download's SHA-256 manifest.
Nine interleaved samples per variant used the default setting and the equivalent
`--scavenger-max-new-space-capacity-mb=8` command-line setting. Median changes were
+6.73% for buffer churn, +8.83% for retained buffers, and +2.18% for object churn.
Small differences can be noise; raw samples and environment metadata are kept in
`evidence/windows-*`. These are **not tests of a custom Windows build**.

Both settings passed the retained-data, allocation-size and worker-transfer
correctness stress script. Official Node 24 rejected the new compiled-default
assertion as expected.

## Limits

This restores a prior default; it is not the newer upstream V8 accounting change.
It affects the process's young-generation capacity, so applications benefiting
from larger young heaps may behave differently. Test the application's own load
before adopting it. An explicit 32 MiB flag restores the baseline setting.

The work does not establish correctness across all supported architectures,
operating systems, embedders, custom V8 builds, or Node's full CI matrix. It does
not make this independent preview an official or upstream-approved Node release.
