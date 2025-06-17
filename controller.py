import tkinter as tk
from pages.question_editor_page import QuestionEditorPage
from pages.home_page import Home

class AppController(tk.Tk):
    # Page settings
    PAGES = (QuestionEditorPage,)

    def __init__(self, home_page=Home, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('ExamTweaks')
        self.state('zoomed')
        self.resizable(False, False)

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        self.home_page = home_page

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in AppController.PAGES:
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(self.home_page)

    def show_frame(self, page_class):
        """Raise the frame corresponding to the given page_class."""
        frame = self.frames[page_class]
        frame.tkraise()

    def run(self):
        self.mainloop()
