import tkinter as tk


class FlyoutWindow(tk.Toplevel):
    def __init__(self, master, soap_text, on_copy_and_inject, on_copy_to_clipboard):
        super().__init__(master)
        self.text_widget = tk.Text(self)
        self.text_widget.insert("1.0", soap_text)
        self.text_widget.pack()

        self.copy_and_inject_button = tk.Button(
            self, text="Copy & Inject to AVImark", command=on_copy_and_inject
        )
        self.copy_and_inject_button.pack()

        self.copy_to_clipboard_button = tk.Button(
            self, text="Copy to Clipboard", command=on_copy_to_clipboard
        )
        self.copy_to_clipboard_button.pack()
