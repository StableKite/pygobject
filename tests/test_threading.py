from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
import testhelper

from gi.repository import GObject


@pytest.mark.thread_unsafe(reason="starts its own synchronized worker threads")
def test_concurrent_type_registration():
    """Same-named Python classes must receive distinct registered GTypes."""
    barrier = threading.Barrier(8)

    def register(_):
        classes = []
        for _ in range(16):
            barrier.wait(timeout=10)

            class ConcurrentObject(GObject.Object):
                pass

            class ConcurrentEnum(GObject.GEnum):
                FIRST = 1

            class ConcurrentFlags(GObject.GFlags):
                FIRST = 1

            classes.extend((ConcurrentObject, ConcurrentEnum, ConcurrentFlags))
        return classes

    with ThreadPoolExecutor(max_workers=8) as pool:
        classes = [cls for group in pool.map(register, range(8)) for cls in group]

    assert len(classes) == 384
    assert len({cls.__gtype__ for cls in classes}) == len(classes)
    for cls in classes:
        assert cls.__gtype__.pytype is cls
        assert GObject.GType.from_name(cls.__gtype__.name) == cls.__gtype__


@pytest.mark.thread_unsafe(reason="starts its own synchronized worker threads")
def test_concurrent_property_construction():
    """Metadata cache misses from independent objects must not corrupt the repo."""
    classes = [
        type(
            f"ConcurrentProperty{i}",
            (GObject.Object,),
            {"text": GObject.Property(type=str, default="")},
        )
        for i in range(32)
    ]
    barrier = threading.Barrier(8)

    def construct(index):
        barrier.wait(timeout=10)
        for i in range(128):
            expected = f"{index}:{i}"
            obj = classes[(i + index) % len(classes)](text=expected)
            assert obj.props.text == expected

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(construct, range(8)))


@pytest.mark.thread_unsafe(reason="starts its own threads and reads fixture lists")
def test_concurrent_native_fixture_ownership():
    """Concurrent C-side ownership changes must leave both fixture lists empty."""
    barrier = threading.Barrier(8)

    def own_and_release(_):
        for _ in range(16):
            barrier.wait(timeout=10)
            objects = [testhelper.OwnedByLibrary(), testhelper.FloatingAndSunk()]
            barrier.wait(timeout=10)
            for obj in objects:
                obj.release()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(own_and_release, range(8)))
    assert testhelper.owned_by_library_get_instance_list() == []
    assert testhelper.floating_and_sunk_get_instance_list() == []
