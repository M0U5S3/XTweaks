# Standard Library Imports
import ast
import importlib.util
import os
import inspect
import subprocess
import sys
import threading

# Third-party imports
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional, Type

# Local application imports
from pages.question_editor.create_variable_window import CreateVariableWindow
from widgets.question_editor_widgets import QuestionCanvas
from utils.mask import Mask
from utils.variable import Variable
from utils.app_logging import LogLevel


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

    def __init__(self, parent: tk.Widget, controller: tk.Tk):
        super().__init__(parent)

        # Placeholder
        with open("pages/question_editor/placeholder_image.jpg", "rb") as f:
            question_image_binary = f.read()

        # Parameter attributes
        self.controller: tk.Tk = controller

        # Page data
        self._variables: dict[str: Variable] = {}

        # Title or header for the page.
        self.header = ttk.Label(self, text="Question Editor", font=("Arial", 20))

        # Instantiate and pack QuestionCanvas.
        self.question_canvas = QuestionCanvas(
            self,
            controller,
            question_image_binary,
            self._on_second_click
        )

        self.x_display = ttk.Label(self.controller, textvariable=self.question_canvas.mouse_x)
        self.y_display = ttk.Label(self.controller, textvariable=self.question_canvas.mouse_y)

        self.crng_status = CRNGStatusLabel(self)

        self.header.pack(pady=10)
        self.question_canvas.pack(pady=20)
        self.crng_status.pack(pady=5)
        self.x_display.pack()
        self.y_display.pack()

        # --= Buttons =--
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        import_crng_button = ttk.Button(button_frame, text="Import CRNG", command=self._import_crng)
        import_crng_button.pack(side="left", padx=5)

        export_question_button = ttk.Button(button_frame, text="Export Question", command=self._export_question)
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

    def _import_crng(self):
        """
        Process:
        1. Prompt user to select a Python file via file dialog.
        2. Read and parse the file to verify it contains a function named 'crng'.
        3. Analyze the file's AST to detect imported modules.
        4. Check for missing dependencies using importlib.
        5. If any dependencies are missing, prompt the user via a messagebox to install them.
        6. Attempt to install missing modules using pip if the user agrees.
        7. Dynamically import the selected module and retrieve the 'crng' function.
        8. Validate that 'crng' takes zero parameters.
        9. Log each step and outcome for transparency and debugging.
        """

        file_path = self._get_crng_file_path()
        if not file_path:
            return

        source_code = self._read_file(file_path)
        if source_code is None:
            return

        parsed = self._parse_and_validate_crng(source_code)
        if parsed is None:
            return

        required_modules = self._collect_required_modules(parsed)
        if not self._handle_missing_dependencies(required_modules):
            return

        module = self._import_module_from_path(file_path)
        if module is None:
            return

        crng_function = self._get_and_validate_function(module, file_path, 'crng')
        if crng_function is None:
            return

        if not self._validate_function_parameters(crng_function, 0):
            return

        if not self._validate_function_returns_dict(crng_function, dict):
            return

        self.crng_function = crng_function
        self.controller.log(LogLevel.INFO, f"'crng' function successfully imported", prioritize=True)
        self.crng_status.mark_success()

    def _get_crng_file_path(self):
        file_path = filedialog.askopenfilename(
            title="Select CRNG Python File",
            filetypes=[("Python Files", "*.py")]
        )

        if not file_path:  # Handle nothing being selected
            return None

        return file_path

    def _read_file(self, file_path):
        # Read file as raw text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:  # Handle any read issue
            self.controller.log(LogLevel.ERROR, f"Failed to read file: {e}")
            return None

    def _parse_and_validate_crng(self, source_code):
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
                return None
            return parsed

        except SyntaxError as e:  # Handle any syntax errors while parsing.
            self.controller.log(LogLevel.ERROR, f"Syntax error while parsing file: {e}")
            return None

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

    def _show_progress_popup(self, total_modules):
        # Reset cancelled flag
        self._cancel_install = False

        # todo self or self.controller
        # Create window.
        self._progress_popup = tk.Toplevel(self)

        # Configure window
        self._progress_popup.title("Installing Dependencies")
        self._progress_popup.grab_set() # User can't interact with main window until the window closes.

        # Labels and progress bar
        tk.Label(self._progress_popup, text="Installing missing dependencies...").pack(pady=(10, 5))
        self._progress_label = tk.Label(self._progress_popup, text=f"0 / {total_modules}")
        self._progress_label.pack(pady=(0, 10))

        # Cancel button
        cancel_btn = tk.Button(self._progress_popup, text="Cancel", command=self._cancel_dependency_install)
        cancel_btn.pack(pady=(0, 10))

        # X button cancels the download too.
        self._progress_popup.protocol("WM_DELETE_WINDOW", self._cancel_dependency_install)

    def _update_progress_label(self, current, total):
        # If progress label exists yet.
        if hasattr(self, "_progress_label"):
            self._progress_label.config(text=f"{current} / {total}")

            # Move the UI update to the front of the event queue
            self._progress_label.update_idletasks()

    def _cancel_dependency_install(self):
        self._cancel_install = True

    def _handle_missing_dependencies(self, required_modules):
        # Separate the dependencies that aren't installed
        missing_modules = [mod for mod in required_modules if importlib.util.find_spec(mod) is None]

        # There might be no missing dependencies, if so return success
        if not missing_modules:
            return True

        if messagebox.askyesno(
                "Missing Dependencies",
                f"The following dependencies are missing:\n\n"
                f"{', '.join(missing_modules)}\n\n"
                "Would you like to install them now?"
        ):
            # Try to install each dependency with the user's permission.
            installed_modules = []

            # Show progress window.
            self._show_progress_popup(len(missing_modules))

            def disable_cancel_button():
                try:
                    if hasattr(self, "_cancel_button") and self._cancel_button.winfo_exists():
                        self._cancel_button.config(state="disabled")
                except Exception:
                    pass

            # Define the thread.
            def do_installs():
                try:
                    for idx, mod in enumerate(missing_modules, start=1):
                        # Check if a cancel has happened before downloading next module
                        if self._cancel_install:
                            raise RuntimeError("Installation cancelled by user.")

                        # Install the module
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", mod],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL  # Suppress pip updates
                        )

                        self.controller.log(LogLevel.INFO, f"Installed missing module: {mod}")
                        installed_modules.append(mod)

                        # Ensure UI update happens in main thread
                        # Schedule progress indicator update
                        self.controller.after(0, self._update_progress_label, idx, len(missing_modules))

                # In the event of ANY error, we must roll back previous installs
                except Exception as e:
                    # Use an if statement instead of declaring mod before try
                    # because we want to add or remove a space at the end.
                    self.controller.log(LogLevel.ERROR, f"Failed to install{f' {mod}' if 'mod' in locals() else ''}: {e}")

                    # Iterate through each module already installed and uninstall them.
                    for installed in installed_modules:
                        try:
                            # Attempt to uninstall module
                            subprocess.check_call(
                                [sys.executable, "-m", "pip", "uninstall", "-y", installed],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            self.controller.log(LogLevel.WARN, f"Rolled back module: {installed}")

                        # Notify the user if we fail to uninstall a module then carry on.
                        except Exception as uninstall_error:
                            self.controller.log(LogLevel.ERROR, f"Failed to roll back {installed}: {uninstall_error}")

                # Schedule to close progress window.
                finally:
                    # Check that the popup was even created yet.
                    if hasattr(self, "_progress_popup"):
                        self.controller.after(0, self._progress_popup.destroy)

            # Configure cancel button to disable
            # once pressed to prevent multiple triggers.

            # Check the cancel button exists.
            if hasattr(self, "_cancel_button") and self._cancel_button.winfo_exists():
                self._cancel_button.config(
                    command = lambda: [
                    setattr(self, "_cancel_install", True), # Set cancel flag to True.
                    disable_cancel_button() # Disable the button from being double pressed
                    ]
                )

            # todo below
            # daemon for now but this isn't robust: if the interpreter crashes
            # the thread does too. This means roll back and error handling never happens.
            # We can either make it non daemon or self fixing on restart.
            install_thread = threading.Thread(target=do_installs, daemon=True)
            install_thread.start()

            # Pause main thread until progress window closes.
            self.controller.wait_window(self._progress_popup)

            # Tell the handler the download was cancelled if it was.
            if self._cancel_install:
                return False

        # If the user declined the download
        else:
            self.controller.log(LogLevel.WARN, "User declined to install missing dependencies.")
            return False    # Tell the handler the download was cancelled.

        # Successful download
        return True

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

    def _get_and_validate_function(self, module, file_path, function_name):
        # Validate function
        try:
            crng_function = getattr(module, function_name)
            self.controller.log(LogLevel.INFO, f"'{function_name}' function successfully validated in {file_path}")
            return crng_function

        except AttributeError:  # crng might've somehow disappeared even after first checks.
            self.controller.log(LogLevel.ERROR, f"Function '{function_name}' not found after import.")
            return None

    def _validate_function_parameters(self, crng_function: Callable[[], float], parameters: int):
        # Check the function behaves as it should
        sig = inspect.signature(crng_function)
        if len(sig.parameters) != parameters:
            self.controller.log(
                LogLevel.ERROR,
                f"Function '{crng_function.__name__}' should take 0 parameters, but takes {len(sig.parameters)}."
            )
            return False
        return True

    def _validate_function_returns_dict(self, crng_function: Callable[[], float], type: Type):
        # todo check that the dictionary keys also fit the variable name regex
        # Check the function returns a dictionary
        try:
            result = crng_function()
            if not isinstance(result, type):
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
# todo create git commit
