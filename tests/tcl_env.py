import os
import sys
from pathlib import Path

# Windows-only Tk bootstrap guard.
#
# tkinter randomly fails on the Windows CI runner with "Can't find a usable
# init.tcl" when Python runs inside a venv (sys.prefix != sys.base_prefix) from
# a non-interactive shell -- Tk's console-window init spawns a second Tcl
# interpreter that doesn't inherit the tcl_library Python computed, so it falls
# back to a nondeterministic auto-search for its script library. Pointing
# TCL_LIBRARY / TK_LIBRARY at the real directories fixes it (upstream:
# actions/setup-python#1102, astral-sh/python-build-standalone#939).
#
# The subtlety that made the earlier CI workaround itself flaky: a Tcl install
# ships BOTH a `tcl8` directory (the "Tcl Modules" dir, which has no init.tcl)
# and a `tcl8.6` directory (the real script library). Both match glob("tcl8*"),
# and glob order is filesystem order, so blindly taking the first hit can point
# TCL_LIBRARY at `tcl8` -- a dir with no init.tcl -- which silently defeats the
# workaround and leaves Tk on its flaky fallback. We select by the presence of
# the script file (init.tcl / tk.tcl), which is correct and deterministic, and
# do it in-process (see tests/conftest.py) before any test constructs a Tk root
# so it never depends on a CI shell step getting the glob right.

_LIBRARIES = (
    ("TCL_LIBRARY", ("tcl9*", "tcl8*"), "init.tcl"),
    ("TK_LIBRARY", ("tk9*", "tk8*"), "tk.tcl"),
)


def _find_library_dir(base_prefix, patterns, required_file):
    # Search the roots real Windows Python layouts place the Tcl/Tk libraries
    # under, and only accept a directory that actually contains the script file.
    roots = []
    for base in (base_prefix, sys.prefix):
        roots.append(Path(base) / "tcl")
        roots.append(Path(base) / "lib")
    for root in roots:
        if not root.is_dir():
            continue
        for pattern in patterns:
            for candidate in sorted(root.glob(pattern)):
                if (candidate / required_file).is_file():
                    return candidate
    return None


def ensure_tcl_tk_library_paths(base_prefix=None):
    """Point TCL_LIBRARY / TK_LIBRARY at the Tcl/Tk script directories that
    actually contain init.tcl / tk.tcl, so tkinter can bootstrap on Windows.

    No-op on non-Windows platforms and when the variables already point at
    valid directories. Never overwrites a variable with a directory that lacks
    the required script file. Returns True when both libraries are known-good
    (or the platform doesn't need this), False if a directory couldn't be
    located.
    """
    if sys.platform != "win32":
        return True

    base_prefix = base_prefix or sys.base_prefix
    ok = True
    for env_var, patterns, required_file in _LIBRARIES:
        current = os.environ.get(env_var)
        if current and (Path(current) / required_file).is_file():
            continue
        found = _find_library_dir(base_prefix, patterns, required_file)
        if found is None:
            ok = False
        else:
            os.environ[env_var] = str(found)
    return ok
