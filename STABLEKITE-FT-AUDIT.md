# Free-threading integration and parallel validation

This integrates GNOME [MR565](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/565)
with current main, retaining its authors and commits. The matching 3.57.1
backport is selected by SBI through the rolling packaging branch
`codex/ubuntu-ft/3.57.1-1`; this main-based feature is its validation context.

Inputs tested on 12 November 2026:

- Main: `3a52debeef4b34a655aab985d93a927be1dac803`.
- Lifetime-test correction, [MR577](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/577).
- Complete draft565: `8eb64418b7d985ad36fbb7c8026997693064458f`.
- Callable-cache critical-section scope fix, [MR578](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/578).
- Parallel fixes through `e465c5cc9f31db44ac8c72c0e25b6cbb29fd5d6a`, submitted
  separately against the draft's source branch in
  [MR579](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/579).

## Causes and corrections

Automatic GType registration had a check/register race; pending generated
names are now reserved. Shared GIRepository caches are protected across
repository operations and GType resolution. Module wrapper creation now
rechecks and publishes its cache under the existing lock, including enums
without a GType. Before/after reproducers expose duplicate registrations,
repository cache double-free and distinct wrappers from concurrent lookup.

The tests also shared GLib's process-wide fatal mask, lazy C fixture types
and native ownership lists. These resources are protected and five new
concurrency regressions added. GTK operations stay on the main thread;
mutable static C fixtures and volume monitors stay serial. Assertions and
existing skips/xfails are retained; execution markers do not skip tests.

One DesktopAppInfo test launches external applications. Running it 32 times
simultaneously filled all 50 GIO workers with D-Bus flush tasks and starved
later async I/O, as confirmed by native debugger stacks. Only that launching
test is serialized; the other GIO tests continue to run concurrently.

## Final software checks

Ubuntu Stonking amd64, actual CPython 3.15.2t, GLib 2.90, native Pycairo,
GTK3 and GTK4.24.1, Meson/pytest under Xvfb, pytest-run-parallel 0.10.0:

| Complete suite | Passed | Existing skipped | Existing xfailed |
|---|---:|---:|---:|
| Main integration, GTK3, 32 threads | 1741 | 28 | 8 |
| Main integration, GTK4, 32 threads | 1690 | 79 | 8 |
| Actual 3.57.1 quilt backport, GTK3, 8 and 32 threads | 1737 | 26 | 8 |
| Actual 3.57.1 quilt backport, GTK4, serial and 32 threads | 1684 | 79 | 8 |

All runs asserted the GIL remained disabled after the full suite, with no
`PYTHON_GIL` override. Upstream pre-commit passed on all files. The 3.57.1
test-parallelization prerequisites are recorded with their upstream commit
identities in the packaging fork; quilt application and native compilation
were checked on a fresh archive, not inferred from the main-based tests.

The earlier 8020cfc1 experiment aborted or hung during parallel runs. Those
failures were not accepted as passes; the final results above follow the
runtime and test-fixture corrections. MR578 separately reproduces and fixes
the draft's original `_py_cs` compilation failure. Its hosted CI has known
missing-xvfb and Pycairo preparation failures; workflows were not weakened.
MR579's source-only branch needs the separately submitted MR578 to compile
on this interpreter, and the full integration results include MR577.

These are amd64 source/software checks, not a complete Debian binary-package
build, clean SBI/ARM64 installation, device or image/boot acceptance. The
upstream draft retains other TODOs; passing these suites does not prove all
native-library operations safe on arbitrary threads. Tested SHAs are
evidence, not installation pins.
