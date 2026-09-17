import tkinter as tk

DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 480


class HistoryWindow(tk.Toplevel):
    def __init__(self, master, entries, on_copy_and_inject, on_copy_to_clipboard):
        super().__init__(master)
        self.title("VetScribe History")
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.entries = list(entries)
        self.on_copy_and_inject = on_copy_and_inject
        self.on_copy_to_clipboard = on_copy_to_clipboard
        self._selected_index = None

        # Left: scrollable list of past notes, newest first.
        list_frame = tk.Frame(self)
        list_frame.pack(side="left", fill="y")
        self.listbox = tk.Listbox(list_frame, width=32)
        self.listbox.pack(side="left", fill="y", expand=True)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        for entry in self.entries:
            self.listbox.insert("end", self._row_label(entry))
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Right: the selected note and its transcript.
        detail_frame = tk.Frame(self)
        detail_frame.pack(side="right", fill="both", expand=True)

        tk.Label(detail_frame, text="SOAP Note").pack(anchor="w")
        self.note_text = tk.Text(detail_frame, height=12, wrap="word")
        self.note_text.pack(fill="both", expand=True)

        tk.Label(detail_frame, text="Transcript").pack(anchor="w")
        self.transcript_text = tk.Text(detail_frame, height=8, wrap="word")
        self.transcript_text.pack(fill="both", expand=True)

        button_frame = tk.Frame(detail_frame)
        button_frame.pack(fill="x")
        self.copy_and_inject_button = tk.Button(
            button_frame,
            text="Copy & Inject to AVImark",
            command=self._on_copy_and_inject_clicked,
        )
        self.copy_and_inject_button.pack(side="left")
        self.copy_to_clipboard_button = tk.Button(
            button_frame,
            text="Copy to Clipboard",
            command=self._on_copy_to_clipboard_clicked,
        )
        self.copy_to_clipboard_button.pack(side="left")

        # Show the newest note by default so the window is useful on open.
        if self.entries:
            self.listbox.selection_set(0)
            self.show_entry(0)

    @staticmethod
    def _row_label(entry) -> str:
        preview = entry.subjective.replace("\n", " ")
        if len(preview) > 40:
            preview = preview[:39] + "…"
        return f"{entry.timestamp}  {preview}"

    def show_entry(self, index):
        entry = self.entries[index]
        self._selected_index = index
        self._replace_text(self.note_text, entry.soap_text)
        self._replace_text(self.transcript_text, entry.transcript)

    @staticmethod
    def _replace_text(widget, value):
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    def _on_listbox_select(self, _event):
        selection = self.listbox.curselection()
        if selection:
            self.show_entry(selection[0])

    def _selected_entry(self):
        if self._selected_index is None:
            return None
        return self.entries[self._selected_index]

    def _on_copy_and_inject_clicked(self):
        entry = self._selected_entry()
        if entry is not None:
            self.on_copy_and_inject(entry.soap_text)

    def _on_copy_to_clipboard_clicked(self):
        entry = self._selected_entry()
        if entry is not None:
            self.on_copy_to_clipboard(entry.soap_text)
