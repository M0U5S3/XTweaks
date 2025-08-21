# Standard library imports
from typing import Dict, Type, Tuple

# Third-party imports
import tkinter as tk
from colorama import init

# Local application imports
from pages.question_editor.question_editor_page import QuestionEditorPage
from utils.app_logging import DebugMode, LogLevel, IGNORE_MODULES
from utils.app_logging._logger import _core_log

IGNORE_MODULES.ignore(func_name='log')

class AppController(tk.Tk):
    """Main application controller that allows pages to request root-level actions."""

    PAGES: Tuple[Type, ...] = (QuestionEditorPage,)

    def __init__(
        self,
        launch_page: Type[tk.Widget],
        debug_mode: DebugMode = DebugMode.OFF
    ) -> None:
        super().__init__()

        self.debug_mode: DebugMode = debug_mode

        # Window properties
        self.title('ExamTweaks')
        self.state('zoomed')
        self.resizable(False, False)

        self.screen_width: int = self.winfo_screenwidth()
        self.screen_height: int = self.winfo_screenheight()
        self.home_page: Type[tk.Widget] = launch_page

        container: tk.Frame = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames: Dict[Type, tk.Widget] = {}

        for F in AppController.PAGES:
            frame: tk.Widget = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(self.home_page)

        self.log(LogLevel.INFO, "Initialised controller")

    def show_frame(self, page_class: Type) -> None:
        frame: tk.Widget = self.frames[page_class]
        frame.tkraise()

    def log(self, level: LogLevel, message: str, prioritize: bool = False) -> None:
        # Wrap the logging module in the controller to pass it the debug mode attribute
        _core_log(level, self.debug_mode, message, prioritize=prioritize)

    def run(self) -> None:
        self.mainloop()
