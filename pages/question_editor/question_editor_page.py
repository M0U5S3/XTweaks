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
from widgets.question_editor_widgets import QuestionCanvas
from utils.mask import Mask
from utils.variable import Variable
from utils.app_logging import LogLevel
from utils.dependency_manager import DependencyManager
from utils.style import style
from utils.pages import Pages


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

    # Max character length for variable name input
    MAX_VARIABLE_NAME_LENGTH = 20

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
        button_style = style.get_button_style()
        label_style = style.get_label_style()
        frame_style = style.get_frame_style()

        # === Define Widgets ===

        # -- Header --
        header = ttk.Label(self, text="Question Editor", font=fonts["title"], **label_style)

        # -- Canvas --
        self.question_canvas = QuestionCanvas(
            self,
            controller,
            question_image_binary,
            self._on_second_click
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
            command=self._import_crng,
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

    def _on_second_click(self, mask: Mask):
        self.controller.log(LogLevel.DEBUG, 'Second canvas click')

        CreateVariableWindow(
            self,
            self.controller,
            mask,
            self.add_variables,
            self._variables,
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

    def _import_crng(self):
        result = self.fetch_read_and_parse()
        if result is None:
            return

        file_path, parsed = result
        required_modules = self._collect_required_modules(parsed)
        dependency_manager = DependencyManager(self, self.controller, required_modules)

        if not dependency_manager.handle_missing_dependencies():
            return

        module = self._import_module_from_path(file_path)
        if module is None:
            return

        crng_function = self._get_function(module, file_path, 'crng')
        if crng_function is None:
            return

        if not self._validate_crng(crng_function):
            return

        self.crng_function = crng_function
        self.controller.log(LogLevel.INFO, f"'crng' function successfully imported", prioritize=True)
        self.crng_status.mark_success()

    def fetch_read_and_parse(self):
        file_path = filedialog.askopenfilename(
            title="Select CRNG Python File",
            filetypes=[("Python Files", "*.py")]
        )

        if not file_path:  # Handle nothing being selected
            return

        # Read file as raw text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

        except Exception as e:  # Handle any read issue
            self.controller.log(LogLevel.ERROR, f"Failed to read file: {e}")
            return

        # Parse and validate 'crng' function
        try:
            parsed = ast.parse(source_code)

            # Iterate through each node.
            # Check if each node is a function and called crng.
            # Output True if any is True
            has_crng = any(
                isinstance(node, ast.FunctionDef) and node.name == "crng"
                for node in parsed.body
            )

            if not has_crng:  # Handle failure to find the function.
                self.controller.log(LogLevel.ERROR, "No function named 'crng' found in the selected file.")
                return

        except SyntaxError as e:  # Handle any syntax errors while parsing.
            self.controller.log(LogLevel.ERROR, f"Syntax error while parsing file: {e}")
            return

        return file_path, parsed

    def _collect_required_modules(self, parsed):
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

    def _import_module_from_path(self, file_path):
        # Dynamically import module
        try:
            # Retrieve file name.
            module_name = os.path.splitext(os.path.basename(file_path))[0]

            # Prepare and execute the module.
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        except Exception as e:  # Handle any exceptions.
            self.controller.log(LogLevel.ERROR, f"Failed to import module: {e}")
            return None

    def _get_function(self, module, file_path, function_name):
        # Validate function
        try:
            crng_function = getattr(module, function_name)
            self.controller.log(LogLevel.INFO, f"'{function_name}' function successfully found in {file_path}")
            return crng_function

        except AttributeError:  # crng might've somehow disappeared even after first checks.
            self.controller.log(LogLevel.ERROR, f"Function '{function_name}' not found.")
            return None

    def _validate_crng(self, crng_function: Callable):
        # Check the function behaves as it should
        sig = inspect.signature(crng_function)
        if len(sig.parameters) != 0:
            self.controller.log(
                LogLevel.ERROR,
                f"Function '{crng_function.__name__}' should take 0 parameters, but takes {len(sig.parameters)}."
            )
            return False

        # todo check that the dictionary keys also fit the variable name regex
        # Check the function returns a dictionary
        try:
            result = crng_function()
            if not isinstance(result, dict):
                self.controller.log(
                    LogLevel.ERROR,
                    f"Function '{crng_function.__name__}' should return a dictionary,"
                    f"but returned {type(result).__name__}."
                )
                return False

        except Exception as e:
            self.controller.log(
                LogLevel.ERROR,
                f"Function '{crng_function.__name__}' raised an exception when called: {e}"
            )
            return False

        return True

    def _export_question(self):
        valid = self._validate_question()

        if not valid:
            self.controller.log(LogLevel.ERROR, "Question export failed validation.")
            return

        # Confirm export
        if messagebox.askyesno(
                "Confirm Export",
                "Are you ready to export this question?"
        ):
            self.controller.log(LogLevel.INFO, "Question export confirmed.")
            # todo Add actual export logic here

        else:
            self.controller.log(LogLevel.INFO, "Question export cancelled.")

    def _validate_question(self):
        pass    # todo

    def check_image(self):
        if self.question_image_imported:
            return True
        return False
