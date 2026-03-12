# Standard Library Imports

# Third-party imports
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Local application imports
from pages.question_editor.create_variable_window import CreateVariableWindow
from pages.question_editor.question_editor_widgets import QuestionEditorCanvas
from pages.question_editor.export_question_window import CreateQuestionWindow

from utils.mask import Mask
from utils.variable import Variable
from utils.app_logging import LogLevel
from utils.style import style
from utils.pages import Pages
from utils.question import Question


class CRNGStatusLabel(ttk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
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
        self.question_canvas = QuestionEditorCanvas(
            self,
            controller,
            1200,
            600
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

    def on_second_click(self, mask: Mask):
        CreateVariableWindow(
            self,
            self.controller,
            mask,
            self._variables
        )

    def _import_image(self):
        # Open file explorer.
        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )

        if file_path:
            # Set and render the question image.
            with open(file_path, "rb") as f:
                self.question_canvas.question_image_binary = f.read()
            # Set the import flag to True.
            self.question_image_imported = True

    def _assign_crng_name(self):
        # Connect CRNG path to the question.
        self.crng_name = self.controller.get_crng_path().name   # Open file finder.
        if self.crng_name:
            self.controller.log(LogLevel.INFO, f"CRNG function successfully imported")
            self.crng_status.mark_success()

    def _export_question(self):
        self.controller.log(LogLevel.INFO, "Attempting an export...")

        if not self.question_image_imported:
            self.controller.log(LogLevel.WARN, "Question image not imported.")
            return

        if not self.crng_status.crng_imported:
            self.controller.log(LogLevel.WARN, "CRNG not imported.")
            return

        export_window = CreateQuestionWindow(self, self.controller)
        result = export_window.fetch_result()

        if result:
            q = Question(
                self.crng_name,
                self.question_canvas.question_image_binary,
                self.variables,
                result["calculator_allowed"],
                result["difficulty"],
                question_number = result["question_number"],
                exam_board = result["exam_board"],
                year = result["year"],
                month = result["month"]
            )

            q.export()

            self.controller.log(LogLevel.INFO, "Question export completed.")

        self.controller.log(LogLevel.INFO, "Question export cancelled.")
