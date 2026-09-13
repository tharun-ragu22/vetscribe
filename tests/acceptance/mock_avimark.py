import sys
import tkinter as tk
from pathlib import Path

WINDOW_TITLE = "AVImark - [Patient: Max (Golden Retriever)]"


class MockAvimarkWindow(tk.Tk):
    def __init__(self, dump_path=None):
        try:
            super().__init__()
        except tk.TclError:
            # Recreating a Tk root right after a prior one was destroyed can
            # hit a one-shot Tcl interpreter init race on Windows; retrying
            # once succeeds.
            super().__init__()
        self.title(WINDOW_TITLE)
        self.dump_path = Path(dump_path) if dump_path else None
        self.text_widget = tk.Text(self)
        self.text_widget.pack(fill="both", expand=True)
        self.text_widget.focus_force()
        if self.dump_path is not None:
            self.text_widget.bind("<<Modified>>", self._on_text_modified)

    def _on_text_modified(self, event):
        self.text_widget.edit_modified(False)
        self.dump_path.write_text(self.text_widget.get("1.0", "end-1c"))


def main():
    dump_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = MockAvimarkWindow(dump_path=dump_path)
    app.mainloop()


if __name__ == "__main__":
    main()
