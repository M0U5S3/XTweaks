# Standard Library Imports
import tkinter as tk

class Mask:
    """
    Contains all the data required to replace a number in an image with a new one.
    """

    def __init__(
            self,
            rectangle_id: int,
            canvas_parent: tk.Canvas
    ) -> None:
        """
        Initialize a new Mask instance.

        Args:
            rectangle_id (int): Identifier for a tk rectangle.
            canvas_parent (tk.Canvas): Canvas that the rectangle belongs to.
        """

        # Parameter Attributes
        self.rectangle_id: int = rectangle_id
        self.parent_canvas: tk.Canvas = canvas_parent

        # Calculate normalised coordinates
        x1, y1, x2, y2 = self.parent_canvas.coords(self.rectangle_id)
        canvas_width = self.parent_canvas.winfo_width()
        canvas_height = self.parent_canvas.winfo_height()

        self.relative_coordinates = (
            (x1 / canvas_width, y1 / canvas_height),
            (x2 / canvas_width, y2 / canvas_height)
        )

        self.active_rectangle: bool = True

    def delete_rectangle(self):
        self.parent_canvas.delete(self.rectangle_id)
        self.active_rectangle = False
