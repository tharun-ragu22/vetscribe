import gc
import sys
import types

import pytest

if sys.platform != "win32":
    for _name in ("win32api", "win32con", "win32gui", "win32clipboard", "pywintypes", "winreg"):
        if _name not in sys.modules:
            sys.modules[_name] = types.ModuleType(_name)


@pytest.fixture(autouse=True)
def _unregister_pystray_window_classes():
    # pystray's win32 backend registers a real Win32 window class per Icon
    # (named after id(self)) in __init__, and only unregisters it inside the
    # mainloop's finally block -- which only runs if something calls
    # icon.run()/run_detached() and lets it exit. Every test that builds a
    # TrayApp (directly, or via build_app()) without running that loop leaks
    # its class for the rest of the process. Once CPython reuses a
    # garbage-collected Icon's address for a later Icon, RegisterClassEx
    # collides on the same class name and raises "OSError: [WinError 1410]
    # Class already exists" -- nondeterministically, depending on GC timing.
    # Sweep every live Icon after each test (across all test files, since the
    # leak isn't confined to whichever test constructed it) and unregister
    # its class so no address reuse can collide with one still on file.
    yield
    if sys.platform != "win32":
        return
    import pystray

    gc.collect()
    for obj in gc.get_objects():
        if isinstance(obj, pystray.Icon):
            atom = getattr(obj, "_atom", None)
            unregister = getattr(obj, "_unregister_class", None)
            if atom and unregister:
                try:
                    unregister(atom)
                except OSError:
                    pass
