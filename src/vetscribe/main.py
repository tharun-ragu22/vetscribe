import tkinter as tk
from pathlib import Path

import pyperclip

from vetscribe.api_client import ApiClient
from vetscribe.audio_recorder import AudioRecorder
from vetscribe.avimark_injector import AvimarkInjector
from vetscribe.config import Config
from vetscribe.flyout_ui import FlyoutWindow
from vetscribe.hotkey_listener import HotkeyListener
from vetscribe.pipeline import Pipeline
from vetscribe.tray_app import TrayApp

CONFIG_PATH = Path.home() / ".vetscribe" / "config.json"


def show_flyout(tk_root, injector, soap_text):
    def on_copy_and_inject():
        injector.inject(soap_text)
        flyout.destroy()

    def on_copy_to_clipboard():
        pyperclip.copy(soap_text)
        flyout.destroy()

    flyout = FlyoutWindow(
        master=tk_root,
        soap_text=soap_text,
        on_copy_and_inject=on_copy_and_inject,
        on_copy_to_clipboard=on_copy_to_clipboard,
    )
    return flyout


def build_app(config=None, tk_root=None):
    config = config or Config.load(CONFIG_PATH)
    tk_root = tk_root or tk.Tk()
    tk_root.withdraw()

    recorder = AudioRecorder()
    api_client = ApiClient(config.api_endpoint, config.api_timeout_seconds)
    injector = AvimarkInjector()

    pipeline = Pipeline(
        recorder=recorder,
        api_client=api_client,
        injector=injector,
        on_flyout_needed=lambda soap_text: show_flyout(tk_root, injector, soap_text),
    )

    tray_app = TrayApp(pipeline=pipeline)
    hotkey_listener = HotkeyListener(
        on_trigger=tray_app.on_hotkey_triggered, hotkey=config.hotkey
    )
    tray_app.attach_hotkey_listener(hotkey_listener)

    return tray_app, hotkey_listener, tk_root


def run():
    tray_app, hotkey_listener, _ = build_app()
    hotkey_listener.start()
    tray_app.icon.run()


if __name__ == "__main__":
    run()
