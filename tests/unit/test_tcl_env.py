import os
import sys

import pytest

from tests.tcl_env import ensure_tcl_tk_library_paths


def _make_fake_tcl_tree(tmp_path):
    # Mirror a real Windows Tcl install: a `tcl8` "Tcl Modules" directory with
    # no init.tcl (the decoy that also matches glob("tcl8*")), plus the real
    # tcl8.6 / tk8.6 script libraries.
    tcl_root = tmp_path / "tcl"
    (tcl_root / "tcl8").mkdir(parents=True)
    real_tcl = tcl_root / "tcl8.6"
    real_tcl.mkdir()
    (real_tcl / "init.tcl").write_text("# init")
    real_tk = tcl_root / "tk8.6"
    real_tk.mkdir()
    (real_tk / "tk.tcl").write_text("# tk")
    return real_tcl, real_tk


def test_selects_directory_that_actually_contains_init_tcl(tmp_path, monkeypatch):
    real_tcl, real_tk = _make_fake_tcl_tree(tmp_path)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("TCL_LIBRARY", raising=False)
    monkeypatch.delenv("TK_LIBRARY", raising=False)

    result = ensure_tcl_tk_library_paths(base_prefix=str(tmp_path))

    assert result is True
    assert os.environ["TCL_LIBRARY"] == str(real_tcl)
    assert os.environ["TK_LIBRARY"] == str(real_tk)


def test_replaces_env_pointing_at_a_dir_without_init_tcl(tmp_path, monkeypatch):
    real_tcl, real_tk = _make_fake_tcl_tree(tmp_path)
    monkeypatch.setattr(sys, "platform", "win32")
    # Reproduce the broken CI value: TCL_LIBRARY -> the modules dir (no init.tcl).
    monkeypatch.setenv("TCL_LIBRARY", str(tmp_path / "tcl" / "tcl8"))
    monkeypatch.setenv("TK_LIBRARY", str(real_tk))

    ensure_tcl_tk_library_paths(base_prefix=str(tmp_path))

    assert os.environ["TCL_LIBRARY"] == str(real_tcl)


def test_keeps_an_already_valid_env_untouched(tmp_path, monkeypatch):
    real_tcl, real_tk = _make_fake_tcl_tree(tmp_path)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("TCL_LIBRARY", str(real_tcl))
    monkeypatch.setenv("TK_LIBRARY", str(real_tk))

    ensure_tcl_tk_library_paths(base_prefix=str(tmp_path))

    assert os.environ["TCL_LIBRARY"] == str(real_tcl)
    assert os.environ["TK_LIBRARY"] == str(real_tk)


def test_reports_failure_and_does_not_set_a_bad_value_when_library_missing(
    tmp_path, monkeypatch
):
    # A prefix with no usable Tcl/Tk libraries at all.
    (tmp_path / "tcl" / "tcl8").mkdir(parents=True)  # decoy only, no init.tcl
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("TCL_LIBRARY", raising=False)
    monkeypatch.delenv("TK_LIBRARY", raising=False)

    result = ensure_tcl_tk_library_paths(base_prefix=str(tmp_path))

    assert result is False
    # Never point Tk at a directory we know is wrong.
    assert "TCL_LIBRARY" not in os.environ


def test_no_op_on_non_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("TCL_LIBRARY", raising=False)
    monkeypatch.delenv("TK_LIBRARY", raising=False)

    assert ensure_tcl_tk_library_paths(base_prefix=str(tmp_path)) is True
    assert "TCL_LIBRARY" not in os.environ
