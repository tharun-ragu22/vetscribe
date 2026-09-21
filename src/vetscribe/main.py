import logging
import threading
import tkinter as tk
from pathlib import Path

import pyperclip

from vetscribe import autostart
from vetscribe.api_client import ApiClient
from vetscribe.audio_recorder import AudioRecorder
from vetscribe.avimark_injector import AvimarkInjector
from vetscribe.config import Config
from vetscribe.flyout_ui import FlyoutWindow
from vetscribe.history_store import HistoryStore
from vetscribe.history_ui import HistoryWindow
from vetscribe.hotkey_listener import HotkeyListener
from vetscribe.logger import build_logger
from vetscribe.offline_queue import OfflineQueue
from vetscribe.pipeline import Pipeline, format_soap_text
from vetscribe.settings_ui import SettingsWindow
from vetscribe.tray_app import TrayApp
from vetscribe.window_icon import apply_window_icon

logger = logging.getLogger("vetscribe.main")

CONFIG_PATH = Path.home() / ".vetscribe" / "config.json"


def run_on_main_thread(tk_root, fn):
    # Tkinter widgets may only be created on the thread running the mainloop.
    # Pipeline/offline-queue callbacks fire from background threads, so
    # marshal the work over via the thread-safe Tk event queue instead of
    # calling into Tk directly (which can hang indefinitely on some platforms).
    if threading.current_thread() is threading.main_thread():
        fn()
    else:
        tk_root.after(0, fn)


FOLLOW_ACTIVE_INTERVAL_MS = 250


def follow_active_avimark(tk_root, injector, window, interval_ms=FOLLOW_ACTIVE_INTERVAL_MS):
    # While a flyout / history window is open, keep re-capturing whichever
    # AVImark chart the vet is in, so "Copy & Inject" follows their latest
    # navigation and pastes into the chart they most recently switched to --
    # even with several AVImark windows open. Re-arms itself on the Tk event
    # loop and stops on its own once the window is gone.
    def track():
        if not window.winfo_exists():
            return
        injector.track_active_window()
        tk_root.after(interval_ms, track)

    tk_root.after(interval_ms, track)


def show_flyout(tk_root, injector, soap_text, on_open_history=None):
    # Seed the target with the chart in front right now (before the flyout takes
    # focus); follow_active_avimark then keeps it current as the vet navigates.
    injector.remember_active_window()

    def on_copy_and_inject():
        # The flyout is a clicked window, so AVImark isn't foreground; actively
        # raise it and paste rather than using the strict inject() guard (which
        # is for the automatic post-hotkey path where AVImark is still focused).
        injector.focus_and_inject(soap_text)
        flyout.destroy()

    def on_copy_to_clipboard():
        pyperclip.copy(soap_text)
        flyout.destroy()

    open_history = None
    if on_open_history is not None:
        # Close the transient popup as we hand the vet over to the full history
        # window (where they can read the transcript and older notes).
        def open_history():
            flyout.destroy()
            on_open_history()

    flyout = FlyoutWindow(
        master=tk_root,
        soap_text=soap_text,
        on_copy_and_inject=on_copy_and_inject,
        on_copy_to_clipboard=on_copy_to_clipboard,
        on_open_history=open_history,
    )
    follow_active_avimark(tk_root, injector, flyout)
    return flyout


def show_history(tk_root, injector, history_store, on_regenerate=None):
    injector.remember_active_window()
    window = HistoryWindow(
        master=tk_root,
        load_entries=history_store.list_entries,
        on_copy_and_inject=lambda soap_text: injector.focus_and_inject(soap_text),
        on_copy_to_clipboard=lambda soap_text: pyperclip.copy(soap_text),
        on_save_edit=lambda entry_id, soap_text, transcript: history_store.update(
            entry_id, soap_text=soap_text, transcript=transcript
        ),
        on_delete=lambda entry_id: history_store.delete(entry_id),
        on_regenerate=on_regenerate,
    )
    follow_active_avimark(tk_root, injector, window)
    return window


def build_app(config=None, tk_root=None):
    config = config or Config.load(CONFIG_PATH)
    tk_root = tk_root or tk.Tk()
    tk_root.withdraw()
    apply_window_icon(tk_root)

    recorder = AudioRecorder()
    api_client = ApiClient(config.api_endpoint, config.api_timeout_seconds, config.api_key)
    injector = AvimarkInjector(title_marker=config.target_window_matcher)
    history_store = HistoryStore()

    def regenerate_from_transcript(transcript):
        # Blocking backend call; HistoryWindow runs this on a worker thread and
        # marshals the result back to the Tk loop itself.
        note = api_client.regenerate_soap_note(transcript)
        return format_soap_text(note)

    def open_history():
        show_history(
            tk_root, injector, history_store, on_regenerate=regenerate_from_transcript
        )

    # A note flyout offers an "Open History" button; an error flyout doesn't
    # (there's no note to browse), so it goes through show_flyout directly.
    def show_note_flyout(soap_text):
        show_flyout(
            tk_root,
            injector,
            soap_text,
            on_open_history=open_history,
        )

    offline_queue = OfflineQueue(
        api_client=api_client,
        on_note_ready=lambda soap_text: run_on_main_thread(
            tk_root, lambda: show_note_flyout(soap_text)
        ),
        history_store=history_store,
    )

    pipeline = Pipeline(
        recorder=recorder,
        api_client=api_client,
        injector=injector,
        on_flyout_needed=lambda soap_text: run_on_main_thread(
            tk_root, lambda: show_note_flyout(soap_text)
        ),
        on_error=lambda message: run_on_main_thread(
            tk_root, lambda: show_flyout(tk_root, injector, message)
        ),
        offline_queue=offline_queue,
        history_store=history_store,
    )

    tray_app = TrayApp(
        pipeline=pipeline,
        on_show_note=lambda soap_text: run_on_main_thread(
            tk_root, lambda: show_note_flyout(soap_text)
        ),
        on_show_history=lambda: run_on_main_thread(tk_root, open_history),
    )
    pipeline.on_state_change = lambda state: tray_app.update_icon_for_state()
    tray_app.attach_offline_queue(offline_queue)
    tray_app.attach_tk_root(tk_root)

    def dispatch_hotkey_trigger():
        # tray_app.on_hotkey_triggered() runs the full pipeline synchronously,
        # including the blocking backend call. HotkeyListener invokes this
        # callback directly on the OS-level global keyboard hook thread, and a
        # slow low-level keyboard hook stalls key delivery system-wide until
        # it returns -- any real keypresses during that stall get queued by
        # Windows and replayed once we return, which can re-fire the hotkey
        # without the user actually holding it down at that moment. Hand the
        # work off to a worker thread so the hook callback returns instantly.
        threading.Thread(target=tray_app.on_hotkey_triggered, daemon=True).start()

    hotkey_listener = HotkeyListener(
        on_trigger=dispatch_hotkey_trigger, hotkey=config.hotkey
    )
    tray_app.attach_hotkey_listener(hotkey_listener)

    current_config = {"value": config}

    def apply_settings(new_config):
        new_config.save(CONFIG_PATH)
        api_client.endpoint = new_config.api_endpoint
        api_client.timeout_seconds = new_config.api_timeout_seconds
        api_client.api_key = new_config.api_key
        injector.title_marker = new_config.target_window_matcher
        hotkey_listener.update_hotkey(new_config.hotkey)
        if new_config.launch_on_startup:
            autostart.enable(autostart.default_launch_command())
        else:
            autostart.disable()
        current_config["value"] = new_config

    def open_settings():
        SettingsWindow(master=tk_root, config=current_config["value"], on_save=apply_settings)

    # The tray menu fires on the pystray icon thread, so -- like on_show_note /
    # on_show_history above -- constructing the Tk window must be marshalled onto
    # the main thread; a direct Tk construction from the tray thread deadlocks
    # (hard-to-kill hang, no traceback), especially while another window's
    # follow_active_avimark after-loop is keeping the Tcl interpreter busy.
    tray_app.on_open_settings = lambda: run_on_main_thread(tk_root, open_settings)

    return tray_app, hotkey_listener, tk_root


def run():
    build_logger()
    logger.info("VetScribe starting up")
    tray_app, hotkey_listener, tk_root = build_app()
    hotkey_listener.start()
    tray_app.offline_queue.start()
    logger.info("offline retry queue started, ready for hotkey")
    # Run the tray icon on its own thread so the main thread is free to run
    # the Tk mainloop, which is required for flyout/settings windows to be
    # created safely (Tk calls from other threads must go through the
    # mainloop, see run_on_main_thread above).
    tray_app.icon.run_detached()
    tk_root.mainloop()


if __name__ == "__main__":
    run()
