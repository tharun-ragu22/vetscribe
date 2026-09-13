import sys
import types

if sys.platform != "win32":
    for _name in ("win32api", "win32con", "win32gui", "win32clipboard", "pywintypes", "winreg"):
        if _name not in sys.modules:
            sys.modules[_name] = types.ModuleType(_name)
