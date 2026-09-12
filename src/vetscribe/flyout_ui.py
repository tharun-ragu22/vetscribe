import tkinter as tk


class FlyoutWindow(tk.Toplevel):
    def __init__(self, master, soap_text, on_copy_and_inject, on_copy_to_clipboard):
        super().__init__(master)
        self.text_widget = tk.Text(self)
        self.text_widget.insert("1.0", soap_text)
        self.text_widget.pack()
