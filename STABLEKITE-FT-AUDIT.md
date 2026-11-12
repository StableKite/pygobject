# Experimental free-threading integration

This branch integrates GNOME [MR !565](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/565)
into current main, retaining the original authors and commits. It is an
experiment, not the source selected by SingleBoardInstall.

Inputs tested on 12 November 2026:

- Current main: `3a52debeef4b34a655aab985d93a927be1dac803`.
- Our minimal reference-count test fix, [MR !577](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/577):
  `d6ab369f5779f3c5c343fe086adfa7729796959e`.
- Complete draft !565: `8eb64418b7d985ad36fbb7c8026997693064458f`.
- Our callable-cache critical-section scope correction, also submitted
  independently as [MR !578](https://gitlab.gnome.org/GNOME/pygobject/-/merge_requests/578).

## Native checks

Ubuntu Stonking amd64; CPython 3.15.2t; GLib 2.90; GTK 4.24.1 and GTK3;
native Pycairo; project Meson/pytest suite under Xvfb. No `PYTHON_GIL` override.
No test assertions, existing skips or selectors were weakened by our changes.
The upstream window-test `thread_unsafe` marker is retained as authored.

| Check | Result |
|---|---|
| Original draft compilation | Fails: unmatched critical-section lexical scopes, `_py_cs` undeclared |
| Scope correction | Native compilation succeeds; project pre-commit passes |
| GTK3 serial suite | 1736 passed, 28 skipped, 8 xfailed |
| GTK4 serial suite | 1685 passed, 79 skipped, 8 xfailed |
| GI and Cairo import | GIL remains disabled |
| GIL state after full GTK4 serial suite | Still disabled |
| GTK3, eight threads | Aborts while running `test_atoms.py` |
| GTK4, eight threads | Aborts while running `test_enum.py` |
| Main + !577 comparison, GTK4/eight threads | Times out after 300 seconds around `test_signal.py`; normal safety GIL fallback |

The comparison is inconclusive about the cause of the parallel aborts: the
baseline also fails to complete in this environment. Serial passes alone do
not establish thread safety. The draft additionally retains its own locking
TODOs. This branch must pass concurrency investigation and regression review
before it is considered for SBI; no production or ARM64 acceptance is claimed.

The minimal !578 fix was separately compiled on the exact draft head, without
the current-main merge or !577: original file fails, fixed file compiles.
Its source CI has 13 successful jobs, three failures and two skipped jobs.
Both GNOME-master jobs lack `xvfb-run`; the Python 3.15 job fails in Pycairo
preparation on CPython's `_Py_STDC_VERSION` header warning. These failures are
disclosed in !578; its CI workflow is unchanged.

SBI continues to select the rolling packaging branch
`codex/ubuntu-ft/3.57.1-1`, which retains CPython's normal safety GIL fallback.
Tested SHAs above are evidence, not installation pins.
