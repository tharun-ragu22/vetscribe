import logging
import tkinter as tk

logger = logging.getLogger("vetscribe.history_ui")

DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 480
# How often an open window re-reads the store so notes recorded while it's open
# appear without the vet reopening it. A save happens on the pipeline thread or
# the offline-queue thread; polling on the Tk event loop picks up both without
# any cross-thread widget access.
DEFAULT_POLL_INTERVAL_MS = 1000


class HistoryWindow(tk.Toplevel):
    def __init__(
        self,
        master,
        load_entries,
        on_copy_and_inject,
        on_copy_to_clipboard,
        on_save_edit=None,
        on_delete=None,
        confirm_delete=None,
        poll_interval_ms=DEFAULT_POLL_INTERVAL_MS,
    ):
        super().__init__(master)
        self.title("VetScribe History")
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self._load_entries = load_entries
        self.on_copy_and_inject = on_copy_and_inject
        self.on_copy_to_clipboard = on_copy_to_clipboard
        self.on_save_edit = on_save_edit or (
            lambda entry_id, soap_text, transcript: None
        )
        self.on_delete = on_delete or (lambda entry_id: None)
        self._confirm_delete = confirm_delete or self._default_confirm_delete
        self.entries = list(load_entries())
        self._selected_index = None

        # Left: scrollable list of past notes, newest first.
        list_frame = tk.Frame(self)
        list_frame.pack(side="left", fill="y")
        self.listbox = tk.Listbox(list_frame, width=32)
        self.listbox.pack(side="left", fill="y", expand=True)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
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
        self.save_button = tk.Button(
            button_frame,
            text="Save Changes",
            command=self._on_save_clicked,
        )
        self.save_button.pack(side="left")
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
        self.delete_button = tk.Button(
            button_frame,
            text="Delete Note",
            command=self._on_delete_clicked,
        )
        self.delete_button.pack(side="right")

        self._populate_listbox()
        # Show the newest note by default so the window is useful on open.
        if self.entries:
            self._select(0)

        # Auto-refresh so notes recorded while the window is open show up live.
        self._poll_interval_ms = poll_interval_ms
        self._poll_job = None
        self.bind("<Destroy>", self._on_destroy)
        if poll_interval_ms:
            self._schedule_poll()

    @staticmethod
    def _row_label(entry) -> str:
        preview = entry.subjective.replace("\n", " ")
        if len(preview) > 40:
            preview = preview[:39] + "…"
        return f"{entry.timestamp}  {preview}"

    def _populate_listbox(self):
        self.listbox.delete(0, "end")
        for entry in self.entries:
            self.listbox.insert("end", self._row_label(entry))

    def refresh(self):
        """Re-read the store and reflect any notes added since the last read.

        If the vet is viewing the newest note (or nothing yet), advance to the
        just-recorded note; if they've deliberately opened an older note, keep
        their selection so they aren't yanked away mid-read. An in-progress
        unsaved edit is never overwritten -- the list still updates around it.
        """
        new_entries = list(self._load_entries())
        if new_entries == self.entries:
            return

        dirty = self._has_unsaved_edits()
        viewing_newest = self._selected_index in (None, 0)
        previously_selected = self._selected_entry()

        self.entries = new_entries
        self._populate_listbox()

        if not self.entries:
            self._selected_index = None
            if not dirty:
                self._replace_text(self.note_text, "")
                self._replace_text(self.transcript_text, "")
                self._mark_clean()
            return

        if dirty and previously_selected is not None:
            # Keep the vet's half-typed edit on screen; just keep the list
            # selection pointed at the same note without repainting the panes.
            target = self._index_of(previously_selected)
            if target is None:
                target = min(self._selected_index or 0, len(self.entries) - 1)
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(target)
            self._selected_index = target
            return

        if viewing_newest:
            target = 0
        else:
            target = self._index_of(previously_selected)
            if target is None:
                target = 0
        self._select(target)

    def _index_of(self, entry):
        # Match on the stable id so an edit (which changes the note's content)
        # doesn't lose the vet's place.
        if entry is None:
            return None
        for index, candidate in enumerate(self.entries):
            if candidate.entry_id == entry.entry_id:
                return index
        return None

    def _select(self, index):
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        self.show_entry(index)

    def show_entry(self, index):
        entry = self.entries[index]
        self._selected_index = index
        self._replace_text(self.note_text, entry.soap_text)
        self._replace_text(self.transcript_text, entry.transcript)
        self._mark_clean()

    def _mark_clean(self):
        # Reset the widgets' modified flags so programmatic population isn't
        # mistaken for a vet edit.
        self.note_text.edit_modified(False)
        self.transcript_text.edit_modified(False)

    def _has_unsaved_edits(self) -> bool:
        return bool(
            self.note_text.edit_modified() or self.transcript_text.edit_modified()
        )

    def _on_save_clicked(self):
        entry = self._selected_entry()
        if entry is None:
            return
        soap_text = self.note_text.get("1.0", "end-1c")
        transcript = self.transcript_text.get("1.0", "end-1c")
        updated = self.on_save_edit(entry.entry_id, soap_text, transcript)
        # Reflect the persisted edit locally so the next auto-refresh sees no
        # change and doesn't repaint (which would otherwise be a no-op flicker).
        if updated is not None and self._selected_index is not None:
            self.entries[self._selected_index] = updated
        self._mark_clean()

    def _default_confirm_delete(self, entry):
        from tkinter import messagebox

        return messagebox.askyesno(
            "Delete note",
            "Delete this SOAP note and its transcript? This cannot be undone.",
            parent=self,
        )

    def _on_delete_clicked(self):
        entry = self._selected_entry()
        if entry is None:
            return
        if not self._confirm_delete(entry):
            return
        self.on_delete(entry.entry_id)
        # Re-read the store rather than mutating locally, so what's shown always
        # matches what's persisted. Keep the vet near where they were: select the
        # note that slid into the deleted one's slot (or the new last note).
        deleted_index = self._selected_index or 0
        self.entries = list(self._load_entries())
        self._populate_listbox()
        if not self.entries:
            self._selected_index = None
            self._replace_text(self.note_text, "")
            self._replace_text(self.transcript_text, "")
            self._mark_clean()
            return
        self._select(min(deleted_index, len(self.entries) - 1))

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

    def _schedule_poll(self):
        self._poll_job = self.after(self._poll_interval_ms, self._poll)

    def _poll(self):
        self._poll_job = None
        if not self.winfo_exists():
            return
        try:
            self.refresh()
        except Exception:
            # A history read must never crash or kill the live-refresh loop.
            logger.exception("failed to refresh history window")
        if self._poll_interval_ms:
            self._schedule_poll()

    def _on_destroy(self, event):
        # Stop the poll loop when the window goes away so a pending `after`
        # callback never fires against a destroyed widget.
        if event.widget is self and self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except tk.TclError:
                pass
            self._poll_job = None
