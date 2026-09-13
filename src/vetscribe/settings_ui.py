import tkinter as tk
from dataclasses import replace


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, config, on_save):
        super().__init__(master)
        self.title("VetScribe Settings")
        self.config = config
        self.on_save = on_save

        self.endpoint_var = tk.StringVar(value=config.api_endpoint)
        self.api_key_var = tk.StringVar(value=config.api_key)
        self.hotkey_var = tk.StringVar(value=config.hotkey)
        self.target_window_var = tk.StringVar(value=config.target_window_matcher)

        tk.Label(self, text="API Endpoint URL").pack()
        self.endpoint_entry = tk.Entry(self, textvariable=self.endpoint_var)
        self.endpoint_entry.pack()

        tk.Label(self, text="API Key / Token").pack()
        self.api_key_entry = tk.Entry(self, textvariable=self.api_key_var, show="*")
        self.api_key_entry.pack()

        tk.Label(self, text="Hotkey Combination").pack()
        self.hotkey_entry = tk.Entry(self, textvariable=self.hotkey_var)
        self.hotkey_entry.pack()

        tk.Label(self, text="Target Window Matcher").pack()
        self.target_window_entry = tk.Entry(self, textvariable=self.target_window_var)
        self.target_window_entry.pack()

        self.save_button = tk.Button(self, text="Save", command=self._on_save_clicked)
        self.save_button.pack()

    def _on_save_clicked(self):
        new_config = replace(
            self.config,
            api_endpoint=self.endpoint_var.get(),
            api_key=self.api_key_var.get(),
            hotkey=self.hotkey_var.get(),
            target_window_matcher=self.target_window_var.get(),
        )
        self.on_save(new_config)
        self.destroy()
