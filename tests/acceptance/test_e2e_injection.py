import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

if sys.platform != "win32":
    pytest.skip("requires a real Windows GUI environment", allow_module_level=True)

from pywinauto import Application

from vetscribe.api_client import SoapNote
from vetscribe.avimark_injector import AvimarkInjector
from vetscribe.pipeline import Pipeline
from tests.acceptance.mock_avimark import WINDOW_TITLE

MOCK_AVIMARK_SCRIPT = Path(__file__).parent / "mock_avimark.py"


@pytest.fixture
def mock_avimark_window():
    app = Application(backend="win32").start(f"{sys.executable} {MOCK_AVIMARK_SCRIPT}")
    window = app.window(title=WINDOW_TITLE)
    window.wait("visible", timeout=10)
    window.set_focus()
    time.sleep(0.2)
    yield window
    app.kill()


def test_full_pipeline_injects_soap_note_into_focused_avimark_window(mock_avimark_window):
    recorder = MagicMock()
    recorder.save_wav.side_effect = lambda path: Path(path).write_bytes(b"fake-audio")
    api_client = MagicMock()
    api_client.generate_soap_note.return_value = SoapNote(
        subjective="Patient bright, alert, and responsive.",
        objective="Temp 101.5F, HR 120bpm.",
        assessment="Mild gastroenteritis.",
        plan="Bland diet for 3 days, recheck if not improved.",
    )
    on_flyout_needed = MagicMock()

    pipeline = Pipeline(
        recorder=recorder,
        api_client=api_client,
        injector=AvimarkInjector(),
        on_flyout_needed=on_flyout_needed,
    )

    pipeline.toggle_recording()
    pipeline.toggle_recording()

    on_flyout_needed.assert_not_called()
    injected_text = mock_avimark_window.child_window(control_type="Edit").get_value()
    assert "SUBJECTIVE" in injected_text
    assert "OBJECTIVE" in injected_text
    assert "ASSESSMENT" in injected_text
    assert "PLAN" in injected_text
