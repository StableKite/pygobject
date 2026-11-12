# Free-threaded packaging validation

This rolling packaging branch retains upstream 3.57.1-1 and carries the
dependency corrections here, outside SingleBoardInstall. SBI resolves the
branch at build time; these SHAs record test inputs, not installation pins.

Quilt inputs, in order:

1. Ten upstream test-parallelization commits, listed in the DEP-3 header.
   The test_builder.py hunk is omitted because 3.57.1 has no such file.
2. The three lifetime-test corrections submitted in GNOME MR577.
3. Upstream draft MR565 at 8eb64418b7d985ad36fbb7c8026997693064458f.
4. The callable-cache scope correction submitted in MR578.
5. Registration, repository, wrapper-cache and test-fixture corrections
   submitted in [MR579](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/579).

The exact source archive at 53fbf8340ef557f95c091eba4c13324d06772d1c was
extracted afresh; `dpkg-source --before-build .` applied all five patches,
and native Meson configuration and compilation succeeded. The later DEP-3
Forwarded URL and this document do not change the tested source payload.

Ubuntu Stonking amd64, CPython 3.15.2t, GLib 2.90, native Pycairo, Xvfb:

| Complete suite | Passed | Existing skipped | Existing xfailed |
|---|---:|---:|---:|
| GTK3, 8 threads | 1737 | 26 | 8 |
| GTK3, 32 threads | 1737 | 26 | 8 |
| GTK4, 32 threads | 1684 | 79 | 8 |
| GTK4, serial | 1684 | 79 | 8 |

No `PYTHON_GIL` override was used; every run asserted the GIL remained
disabled after the full suite. Native GIR generation uses a separate
scanner process with CPython's normal safety GIL fallback; this does not
describe that scanner as GIL-free. GTK and shared-fixture serial markers
still execute those tests with their assertions. Five new concurrency
regressions exercise actual worker threads and GLib fatal-mask capture.

Runtime sources match the separately tested main-based integration at
e465c5cc9f31db44ac8c72c0e25b6cbb29fd5d6a, except existing release/main
differences. That integration passed GTK3 1741/28/8 and GTK4 1690/79/8 at
32 threads, with the GIL disabled, and upstream pre-commit on all files.

These are source build and software checks. A complete Debian binary
package build, clean SBI transaction and ARM64/Orange Pi acceptance remain
separate gates; this document does not report them as passed. The upstream
free-threading proposal still contains TODOs and is not a blanket claim of
thread safety for all third-party GLib/GTK libraries.
