# Standard library imports
from typing import Dict, Type
from pathlib import Path
import json

# Third-party imports
import tkinter as tk
from tkinter import filedialog, messagebox

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

    # Max character length for variable name input
    MAX_VARIABLE_NAME_LENGTH = 20
    CONFIG_PATH = "data/config.json"

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

    def get_crng_path(self):
        """Open a file finder window to select a CRNG file"""
        project_root = Path(__file__).resolve().parents[0]
        crng_dir = project_root / "crng_files"  # Directory for crng files.

        # In case the expected directory doesn't exist
        if not crng_dir.is_dir():
            messagebox.showwarning("Directory missing",
                                   f"Directory not found: {crng_dir}\n")
            self.log(LogLevel.ERROR, f"CRNG Directory not found at {crng_dir}")
            return
        else:
            start_dir = str(crng_dir)

        file_path = filedialog.askopenfilename(
            title="Select CRNG Python File",
            initialdir=start_dir,
            filetypes=[("Python Files", "*.py")]
        )

        if not file_path:
            return

        chosen = Path(file_path).resolve()
        try:
            # Ensure the chosen file is inside crng_dir
            chosen.relative_to(crng_dir)
        except ValueError:
            messagebox.showerror("Invalid selection",
                                 f"Please choose a file from {crng_dir}.")
            self.log(LogLevel.ERROR, f"Chosen file is not in the crng directory {crng_dir}")
            return

        # Return full path.
        return Path(chosen)

    def get_config(self, config):
        with open(self.CONFIG_PATH, "r") as f:
            return json.load(f)[config]

    def update_config(self, config, value):
        """Update a single config key with a new value."""
        with open(self.CONFIG_PATH, "r") as f:
            config_data = json.load(f)

        config_data[config] = value

        with open(self.CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=2)

    def log(self, level: LogLevel, message: str, prioritize: bool = False) -> None:
        # Wrap the logging module in the controller to pass it the debug mode attribute
        _core_log(level, self.debug_mode, message, prioritize=prioritize)

    def run(self) -> None:
        self.mainloop()
