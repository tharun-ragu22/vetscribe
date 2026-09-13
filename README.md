# VetScribe Assistant

A Windows system-tray app for veterinary exam rooms. Press a hotkey to record
the conversation, get an AI-generated SOAP note, and have it typed directly
into AVImark — with a safety net when AVImark isn't in focus.

## How it works

1. Press **`Ctrl+Shift+R`** to start recording exam-room audio.
2. Press it again to stop. The audio is sent to a configurable AI backend,
   which returns a structured SOAP note (Subjective / Objective / Assessment
   / Plan).
3. If **AVImark** is the foreground window, the note is copied to the
   clipboard and pasted in automatically (simulated `Ctrl+V`).
4. If AVImark is *not* focused, a "Safety Flyout" window pops up in the
   bottom-right corner of the screen with the note text and buttons to copy
   it to the clipboard or inject it once you switch back to AVImark.

A tray icon shows the current state at a glance: green (idle), red
(recording), yellow (processing).

## Tech stack

| Concern | Library |
|---|---|
| System tray icon | [`pystray`](https://pypi.org/project/pystray/) |
| Icon rendering | [`Pillow`](https://pypi.org/project/Pillow/) |
| Audio capture | [`sounddevice`](https://pypi.org/project/sounddevice/) |
| WAV encoding | [`scipy.io.wavfile`](https://pypi.org/project/scipy/) |
| AI backend calls | [`httpx`](https://pypi.org/project/httpx/) |
| Global hotkey | [`pynput`](https://pypi.org/project/pynput/) |
| Clipboard access | [`pyperclip`](https://pypi.org/project/pyperclip/) |
| Windows automation (foreground detection, clipboard, simulated keystrokes) | [`pywin32`](https://pypi.org/project/pywin32/) |
| Safety flyout UI | `tkinter` (stdlib) |
| GUI acceptance testing | [`pywinauto`](https://pypi.org/project/pywinauto/) |
| Tests | `pytest`, `pytest-mock`, `pytest-asyncio`, `respx` |
| Packaging / dependency management | [`uv`](https://github.com/astral-sh/uv) |

`pywin32` and `pywinauto` are only installed on Windows (`sys_platform ==
'win32'` markers in `pyproject.toml`); the app can be developed and unit/
integration tested on Linux, but the actual AVImark injection only runs on
Windows.

## Installation

Requires Python 3.11+ and [`uv`](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/tharun-ragu22/vetscribe.git
cd vetscribe
uv sync
```

On Linux, running/testing also needs system packages for audio and Tk:

```bash
sudo apt-get install -y libportaudio2 python3-tk python3-dev
```

### Configuration

On first run, VetScribe creates `~/.vetscribe/config.json` with defaults
(see `src/vetscribe/config.py`):

```json
{
  "api_endpoint": "https://localhost:8443/api/soap",
  "api_timeout_seconds": 30,
  "hotkey": "<ctrl>+<shift>+r"
}
```

Edit `api_endpoint` to point at your SOAP-note-generation backend. It's
expected to accept a `POST` with raw WAV bytes (`Content-Type: audio/wav`)
and return JSON with `subjective`, `objective`, `assessment`, and `plan`
fields.

### Running

```bash
uv run python -m vetscribe.main
```

This starts the tray icon and registers the global hotkey. Press
`Ctrl+Shift+R` to start/stop a recording.

## Project layout

```
src/vetscribe/
  config.py            Config dataclass; loads/saves ~/.vetscribe/config.json
  api_client.py         ApiClient — POSTs audio to the AI backend, parses SoapNote
  audio_recorder.py     AudioRecorder — sounddevice-based mic capture + WAV export
  avimark_injector.py   AvimarkInjector — foreground-window check, clipboard + Ctrl+V
  flyout_ui.py          FlyoutWindow — Tkinter "Safety Flyout" shown when injection fails
  hotkey_listener.py    HotkeyListener — global Ctrl+Shift+R capture via pynput
  pipeline.py           Pipeline / PipelineState — the record→transcribe→inject state machine
  tray_app.py           TrayApp — pystray icon, state-to-color mapping
  main.py               build_app() wires everything together; run() is the entry point

tests/
  unit/                 Fast, isolated tests for each module (mocked collaborators)
  integration/          Tests that wire multiple real modules together (pipeline, tray, hotkey, main)
  acceptance/           End-to-end tests, including a fake AVImark window and Windows-only
                         pywinauto GUI automation tests (skipped on non-Windows platforms)

.github/workflows/ci.yml  GitHub Actions CI: runs the full suite on ubuntu-latest and
                          windows-latest (via uv) on every push/PR to main
```

### Key design points

- **Dependency injection**: `build_app(config=None, tk_root=None)` in
  `main.py` constructs the recorder, API client, injector, pipeline, tray
  app, and hotkey listener, so every piece can be swapped for a test double.
- **State machine**: `Pipeline` in `pipeline.py` only has three states
  (`IDLE`, `RECORDING`, `PROCESSING`). `toggle_recording()` is a no-op while
  processing, so a stray hotkey press mid-transcription can't corrupt state.
- **Injection safety**: `AvimarkInjector.inject()` refuses to send
  `Ctrl+V` unless AVImark is genuinely the foreground window (checked via
  `win32gui.GetForegroundWindow()`), so a SOAP note can never be pasted into
  the wrong application.
- **Mock AVImark for testing**: `tests/acceptance/mock_avimark.py` is a
  Tkinter stand-in for the real AVImark window, used by the Windows
  acceptance tests. Because Tkinter widgets have no native Win32 control
  class, its content can't be read back via GUI automation — instead it
  dumps its text to a file on every edit, which the tests poll and read.

## Testing

```bash
uv run pytest -v
```

On Linux, GUI-touching tests need a display (real or virtual):

```bash
xvfb-run -a uv run pytest -v
```

Windows-only acceptance tests (`tests/acceptance/test_e2e_*.py`) are
automatically skipped on non-Windows platforms and only run for real in CI
on the `windows-latest` runner.

## CI

`.github/workflows/ci.yml` runs the full test suite on both `ubuntu-latest`
and `windows-latest` for every push/PR to `main`, using `uv sync --locked`
for reproducible installs. This includes the real Windows GUI acceptance
tests (mock AVImark injection and safety-flyout fallback), so a green CI run
means the app has been verified end-to-end on a genuine, fresh Windows
machine.
