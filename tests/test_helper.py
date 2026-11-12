from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from gi.repository import GLib
from .helper import capture_glib_warnings


@pytest.mark.thread_unsafe(reason="runs its own threads and checks the global mask")
def test_concurrent_glib_warning_capture():
    """Nested captures must restore the fatal mask despite competing threads."""
    original = GLib.log_set_always_fatal(GLib.LogLevelFlags(0))
    GLib.log_set_always_fatal(original)
    barrier = threading.Barrier(8)

    def get_mask():
        mask = GLib.log_set_always_fatal(GLib.LogLevelFlags(0))
        GLib.log_set_always_fatal(mask)
        return mask

    def capture():
        barrier.wait(timeout=10)
        for _ in range(30):
            with capture_glib_warnings(allow_criticals=True):
                time.sleep(0)
                mask = get_mask()
                assert not mask & GLib.LogLevelFlags.LEVEL_CRITICAL
                with capture_glib_warnings(allow_warnings=True):
                    assert not get_mask() & GLib.LogLevelFlags.LEVEL_WARNING
                assert get_mask() == mask

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: capture(), range(8)))
        assert get_mask() == original
    finally:
        GLib.log_set_always_fatal(original)
