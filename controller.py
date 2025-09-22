# Standard library imports
from typing import Dict, Type

# Third-party imports
import tkinter as tk

# Local application imports
from utils.app_logging import DebugMode, LogLevel, IGNORE_MODULES
from utils.app_logging._logger import _core_log
from utils.style import style
from utils.pages import Pages

# Pages
from pages.home.home_page import Home
from pages.question_editor.question_editor_page import QuestionEditorPage

# Ignore the log wrapper in verbose traceback
IGNORE_MODULES.ignore(func_name='log')


class AppController(tk.Tk):
    """Main application controller that allows pages to request root-level actions."""

    PAGES: Dict[str, Type[tk.Frame]] = {
        Pages.HOME: Home,
        Pages.QUESTION_EDITOR: QuestionEditorPage
    }

    def __init__(
        self,
        launch_page: PAGES,
        debug_mode: DebugMode = DebugMode.OFF
    ) -> None:
        super().__init__()

        self.debug_mode: DebugMode = debug_mode

        style.set_controller(self)

        # Window properties
        self.title('ExamTweaks')
        self.state('zoomed')
        self.resizable(False, False)

        self.screen_width: int = self.winfo_screenwidth()
        self.screen_height: int = self.winfo_screenheight()
        self.launch_page: str = launch_page

        self.container: tk.Frame = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames: Dict[str, tk.Frame] = {}

        self.current_page = self.launch_page
        self.show_page(self.launch_page)

        self.log(LogLevel.INFO, "Initialized controller")

    def initialize_page(self, page: Pages):
        frame: tk.Frame = self.__class__.PAGES[page](parent=self.container, controller=self)

        # If frame has already been opened and reset is on, reset it
        if page in self.frames:
            self.frames[page].destroy()

        self.frames[page] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def show_page(self, page_name: Pages, reset: bool = True) -> None:
        if page_name not in self.__class__.PAGES:
            raise ValueError(f"Page '{page_name}' is not registered in {self.__class__.__name__}.PAGES")

        if reset or page_name not in self.frames:
            self.initialize_page(page_name)

        new_frame: tk.Frame = self.frames[page_name]
        new_frame.tkraise()

        self.log(LogLevel.INFO, f"Page change {self.current_page} -> {page_name}")
        self.current_page = page_name

    def log(self, level: LogLevel, message: str, prioritize: bool = False) -> None:
        # Wrap the logging module in the controller to pass it the debug mode attribute
        _core_log(level, self.debug_mode, message, prioritize=prioritize)

    def run(self) -> None:
        self.mainloop()
