import tkinter as tk
from pathlib import Path

import pyperclip

from vetscribe.api_client import ApiClient
from vetscribe.audio_recorder import AudioRecorder
from vetscribe.avimark_injector import AvimarkInjector
from vetscribe.config import Config
from vetscribe.flyout_ui import FlyoutWindow
from vetscribe.hotkey_listener import HotkeyListener
from vetscribe.logger import build_logger
from vetscribe.pipeline import Pipeline
from vetscribe.settings_ui import SettingsWindow
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
    api_client = ApiClient(config.api_endpoint, config.api_timeout_seconds, config.api_key)
    injector = AvimarkInjector(title_marker=config.target_window_matcher)

    pipeline = Pipeline(
        recorder=recorder,
        api_client=api_client,
        injector=injector,
        on_flyout_needed=lambda soap_text: show_flyout(tk_root, injector, soap_text),
        on_error=lambda message: show_flyout(tk_root, injector, message),
    )

    tray_app = TrayApp(pipeline=pipeline)
    hotkey_listener = HotkeyListener(
        on_trigger=tray_app.on_hotkey_triggered, hotkey=config.hotkey
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
        current_config["value"] = new_config

    def open_settings():
        SettingsWindow(master=tk_root, config=current_config["value"], on_save=apply_settings)

    tray_app.on_open_settings = open_settings

    return tray_app, hotkey_listener, tk_root


def run():
    build_logger()
    tray_app, hotkey_listener, _ = build_app()
    hotkey_listener.start()
    tray_app.icon.run()


if __name__ == "__main__":
    run()
