import tkinter as tk

WINDOW_TITLE = "AVImark - [Patient: Max (Golden Retriever)]"


class MockAvimarkWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.text_widget = tk.Text(self)
        self.text_widget.pack(fill="both", expand=True)
        self.text_widget.focus_force()


def main():
    app = MockAvimarkWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
