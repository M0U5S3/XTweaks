# Third-party imports
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

# Local application imports
from widgets.question_editor_widgets import QuestionCanvas
from utils.mask import Mask
from utils.variable import Variable


class QuestionEditorPage(tk.Frame):
    """
    Page for creating masks on the question image.
    """

    # Max character length for variable name input
    MAX_VARIABLE_NAME_LENGTH = 20

    def __init__(self, parent: tk.Widget, controller: tk.Tk):
        super().__init__(parent)

        # Placeholder
        with open("placeholder_image.jpg", "rb") as f:
            question_image_binary = f.read()

        # Parameter attributes
        self.controller: tk.Tk = controller

        # Page data
        self._variables: dict[str: Variable] = {}

        # Title or header for the page.
        self.header = ttk.Label(self, text="Question Editor", font=("Arial", 20))

        # Instantiate and pack QuestionCanvas.
        self.question_canvas = QuestionCanvas(self, controller, question_image_binary)

        self.x_display = ttk.Label(self.controller, textvariable=self.question_canvas.mouse_x)
        self.y_display = ttk.Label(self.controller, textvariable=self.question_canvas.mouse_y)

        self.header.pack(pady=10)
        self.question_canvas.pack(pady=20)
        self.x_display.pack()
        self.y_display.pack()

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

        self._variables[variable_name] = Variable(
            variable_name,
            crng,
            masks = masks if masks is not None else []
        )

    def apply_mask(self, variable, mask):
        pass
