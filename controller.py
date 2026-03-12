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
from pages.question_viewer.question_viewer_page import QuestionViewerPage

# Ignore the log wrapper in verbose traceback
IGNORE_MODULES.ignore(func_name='log')


class AppController(tk.Tk):
    """Main application controller that allows pages to request root-level actions."""

    PAGES: Dict[str, Type[tk.Frame]] = {
        Pages.HOME: Home,
        Pages.QUESTION_EDITOR: QuestionEditorPage,
        Pages.QUESTION_VIEWER: QuestionViewerPage
    }

    CONFIG_PATH = "data/config.json"

    def __init__(
        self,
        launch_page: PAGES,
        crng_dir: Path | str,
        debug_mode: DebugMode = DebugMode.OFF
    ) -> None:
        super().__init__()

        # Debug mode Off, On, Verbose
        self.debug_mode: DebugMode = debug_mode

        # Directory for crng files.
        self.crng_dir = crng_dir

        style.set_controller(self)

        # Window properties
        self.title('ExamTweaks')
        self.state('zoomed')
        self.resizable(False, False)

        self.launch_page: str = launch_page

        self.container: tk.Frame = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Loaded pages
        self.frames: Dict[str, tk.Frame] = {}

        self.current_page = self.launch_page
        self.show_page(self.launch_page)

        self.log(LogLevel.INFO, "Initialized controller")

    def initialize_page(self, page: Pages):
        frame: tk.Frame = self.__class__.PAGES[page](parent=self.container, controller=self)

        # If frame has already been opened, reset it
        if page in self.frames:
            self.frames[page].destroy()

        self.frames[page] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def show_page(self, page_name: Pages, reset: bool = True) -> None:
        # If the page doesn't exist.
        if page_name not in self.__class__.PAGES:
            raise ValueError(f"Page '{page_name}' is not registered in {self.__class__.__name__}.PAGES")

        # Initialize a page if it hasn't been created yet or if reset is True.
        if reset or page_name not in self.frames:
            self.initialize_page(page_name)

        # Raise the frame.
        self.frames[page_name].tkraise()

        self.log(LogLevel.INFO, f"Page change {self.current_page} -> {page_name}")
        self.current_page = page_name

    def get_crng_path(self):
        """Open a file finder window to select a CRNG file"""

        # In case the expected directory doesn't exist
        if not self.crng_dir.is_dir():
            messagebox.showwarning("Directory missing",
                                   f"Directory not found: {self.crng_dir}\n")
            self.log(LogLevel.ERROR, f"CRNG Directory not found at {self.crng_dir}")
            return
        else:
            start_dir = str(self.crng_dir)

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
            chosen.relative_to(self.crng_dir)
        except ValueError:
            messagebox.showerror("Invalid selection",
                                 f"Please choose a file from {self.crng_dir}.")
            self.log(LogLevel.ERROR, f"Chosen file is not in the crng directory {self.crng_dir}")
            return

        # Return full path.
        return Path(chosen)

    def get_xtweak_paths(self):
        """Open a file finder window to select a xtweak file"""
        paths = filedialog.askopenfilenames(
            parent=self, title="Open .xtweak files",
            filetypes=[("XTweak files", "*.xtweak"), ("All files", "*.*")]
        )

        return list(paths) if paths else None

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
