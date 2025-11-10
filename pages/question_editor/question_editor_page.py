# Standard Library Imports
import ast
import importlib.util
import os
import inspect

# Third-party imports
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

# Local application imports
from pages.question_editor.create_variable_window import CreateVariableWindow
from pages.question_editor.question_editor_widgets import QuestionCanvas
from utils.mask import Mask
from utils.variable import Variable
from utils.app_logging import LogLevel
from utils.dependency_manager import DependencyManager
from utils.style import style
from utils.pages import Pages
from utils.question import Question


class CRNGStatusLabel(ttk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self.configure(text="❗ You need to import a CRNG file ❗", foreground="red")
        self.crng_imported = False

    def mark_success(self):
        self.configure(text="✅ CRNG function loaded ✅", foreground="green")
        self.crng_imported = True

class QuestionEditorPage(tk.Frame):
    """
    Page for creating masks on the question image.
    """

    def __init__(self, parent: tk.Widget, controller: tk.Tk, **kwargs):
        # === Page Setup ===
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.controller = controller

        with open("data/placeholder_image.jpeg", "rb") as f:
            question_image_binary = f.read()

        self.question_image_imported = False
        self._variables: dict[str: Variable] = {}

        # === Style Setup ===
        fonts = style.get_fonts()
        button_style = style.get_button_style_question_editor()
        label_style = style.get_label_style()
        frame_style = style.get_frame_style()

        # === Define Widgets ===

        # -- Header --
        header = ttk.Label(self, text="Question Editor", font=fonts["title"], **label_style)

        # -- Canvas --
        self.question_canvas = QuestionCanvas(
            self,
            controller,
            question_image_binary
        )

        # -- Status & Coordinates --
        self.x_display = ttk.Label(self, textvariable=self.question_canvas.mouse_x, font=fonts["default"],
                                   **label_style)
        self.y_display = ttk.Label(self, textvariable=self.question_canvas.mouse_y, font=fonts["default"],
                                   **label_style)

        self.crng_status = CRNGStatusLabel(self)
        self.crng_status.configure(font=fonts["default"], **label_style)

        # -- Buttons --
        back_button = tk.Button(
            self,
            text="←",
            command=lambda: self.controller.show_page(Pages.HOME),
            **style.get_back_button_style()
        )

        import_export_buttons = tk.Frame(self, **frame_style)

        import_crng_button = tk.Button(
            import_export_buttons,
            text="Import CRNG",
            command=self._assign_crng_name,
            **button_style
        )

        question_button = tk.Button(
            import_export_buttons,
            text="Import Image",
            command=self._import_image,
            **button_style
        )

        export_question_button = tk.Button(
            import_export_buttons,
            text="Export Question",
            command=self._export_question,
            **button_style
        )

        # === Pack Widgets ===

        # -- Header --
        header.pack(pady=10)

        # -- Canvas --
        self.question_canvas.pack(pady=20)

        # -- Status & Coordinates --
        self.x_display.pack()
        self.y_display.pack()
        self.crng_status.pack(pady=5)

        # -- Buttons --
        back_button.place(x=10, y=10)

        import_export_buttons.pack(pady=5)
        import_crng_button.pack(side="left", padx=5)
        question_button.pack(side="left", padx=5)
        export_question_button.pack(side="left", padx=5)

    @property
    def variables(self):
        return self._variables

    def add_variables(
            self,
            variable_name: str,
            crng: Callable[[], float],
            masks: Optional[list[Mask,...]] = None
    ) -> None:
        """
        Add a new Variable instance to the variables list.

        Args:
            variable_name (str): The name to assign to the new variable.
            crng (Callable[[], float]): A function that returns a float, used for generating random values or distributions.
            masks (list[Mask], optional): A list of Mask objects associated with the variable. Defaults to an empty list.
        """

        # Add to variables list and pass an empty list if no masks are passed
        self._variables[variable_name] = Variable(
            variable_name,
            crng,
            masks = masks if masks is not None else []
        )

    def on_second_click(self, mask: Mask):
        CreateVariableWindow(
            self,
            self.controller,
            mask,
            self._variables
        )

    def _import_image(self):
        # Open file explorer
        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )

        if file_path:
            with open(file_path, "rb") as f:
                self.question_canvas.question_image_binary = f.read()
            self.question_image_imported = True

    def _assign_crng_name(self):
        self.crng_path = self.controller.get_crng_path()   # Open file finder.
        self.controller.log(LogLevel.INFO, f"CRNG function successfully imported")
        self.crng_status.mark_success()

    # === LEGACY CODE ===

    def _import_crng(self, crng_path):
        required_modules = self._collect_required_modules(crng_path)
        dependency_manager = DependencyManager(self, self.controller, required_modules)

        if not dependency_manager.handle_missing_dependencies():
            return

        module = self._import_module_from_path(crng_path)
        if module is None:
            return

        crng_function = self._get_function(module, crng_path)
        if crng_function is None:
            return

        self.crng_function = crng_function
        self.controller.log(LogLevel.INFO, f"'crng' function successfully imported")

    def _collect_required_modules(self, crng_path):
        # Read file as raw text
        try:
            with open(crng_path, "r", encoding="utf-8") as f:
                source_code = f.read()

        except Exception as e:  # Handle any read issue
            self.controller.log(LogLevel.ERROR, f"Failed to read file: {e}")
            return

        # Parse and validate 'crng' function
        try:
            parsed = ast.parse(source_code)

        except SyntaxError as e:  # Handle any syntax errors while parsing.
            self.controller.log(LogLevel.ERROR, f"Syntax error while parsing file: {e}")
            return

        # Check for missing dependencies.
        required_modules = set()

        # Traverse syntax tree depth first so we don't miss nested imports.
        for node in ast.walk(parsed):
            # Check if the node is any kind of import
            if isinstance(node, ast.Import):
                required_modules.update(alias.name.split('.')[0] for alias in node.names)

            elif isinstance(node, ast.ImportFrom) and node.module:
                required_modules.add(node.module.split('.')[0])

        return required_modules

    @staticmethod
    def _import_module_from_path(file_path):
        # Retrieve file name.
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Prepare and execute the module.
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _get_function(self, module, file_path):
        """Discovers exactly one @question-decorated function in a module."""
        # Scan for functions flagged by the decorator
        flagged = [
            fn for _, fn in inspect.getmembers(module, inspect.isfunction)
            if getattr(fn, "_is_question", False)
        ]

        # No flagged function.
        if not flagged:
            self.controller.log(
                LogLevel.ERROR,
                f"No @question function found in {file_path}"
            )
            return

        # More than one flagged function.
        if len(flagged) > 1:
            names = [fn.__name__ for fn in flagged]
            self.controller.log(
                LogLevel.ERROR,
                f"Multiple @question functions in {file_path}: {names}"
            )
            return

        # Exactly one flagged function
        fn = flagged[0]
        self.controller.log(
            LogLevel.INFO,
            f"Discovered '{fn.__name__}' in {file_path}"
        )
        return fn

    # === LEGACY CODE END ===

    def _export_question(self):
        self.controller.log(LogLevel.INFO, "Attempting an export...")

        if not self.question_image_imported:
            self.controller.log(LogLevel.WARN, "Question image not imported.")
            return

        if not self.crng_status.crng_imported:
            self.controller.log(LogLevel.WARN, "CRNG not imported.")
            return

        # todo check that all variables have a link to CRNG.
        # todo check solutions exist

        # Confirm export
        # todo change to be a window with inputs: difficulty, exam board, calculator allowed and marks
        calculator_allowed = True # todo all temporary
        difficulty = 'Hard'
        question_number = 7
        exam_board = 'AQA'
        year = 2020
        month = 5

        if messagebox.askyesno(
                "Confirm Export",
                "Are you ready to export this question?"
        ):
            self.controller.log(LogLevel.INFO, "Question export confirmed.")

            q = Question(
                self.crng_path,
                self.question_canvas.question_image_binary,
                self.variables,
                calculator_allowed,
                difficulty,
                question_number = question_number,
                exam_board = exam_board,
                year = year,
                month = month
            )

            q.export()

        else:
            self.controller.log(LogLevel.INFO, "Question export cancelled.")
