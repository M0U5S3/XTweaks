import tkinter as tk
import tkinter.font as tkfont
from typing import Tuple

from utils.style import style

class Mask:
    """
    Contains all the data required to replace a number in an image with a new one.
    """

    def __init__(
            self,
            x1: int,
            y1: int,
            x2: int,
            y2: int,
            parent_canvas,  # Can't save as an attribute because can't pickle a widget
            **kwargs
    ) -> None:
        """
        Initialize a new Mask instance.

        Args:
            rectangle_id (int): Identifier for a tk rectangle.
            parent_canvas (tk.Canvas): Canvas that the rectangle belongs to.
        """

        # Parameter Attributes
        self.rectangle_id: int = parent_canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    **kwargs
                )

        self._relative_coordinates = (
            (x1 / parent_canvas.width, y1 / parent_canvas.height),
            (x2 / parent_canvas.width, y2 / parent_canvas.height)
        )

        self.active_rectangle = True
        self._text_id = None
        self._text_font_family = style.get_fonts()['math']
        self._text_font_weight: str = "normal"     # could be "bold"

    def delete_rectangle(self, parent_canvas):
        parent_canvas.delete(self.rectangle_id)
        self.active_rectangle = False

    def translate_absolute_coordinates(self, new_canvas):
        x1 = self._relative_coordinates[0][0] * new_canvas.width
        y1 = self._relative_coordinates[0][1] * new_canvas.height
        x2 = self._relative_coordinates[1][0] * new_canvas.width
        y2 = self._relative_coordinates[1][1] * new_canvas.height

        return int(x1), int(y1), int(x2), int(y2)

    def place_text(self, canvas, text: str, padding: float = 0.1) -> None:
        """Render some text so it fits inside the mask."""


        font = style.get_fonts()['math']
        # Remove previous text if any
        if self._text_id is not None:
            try:
                canvas.delete(self._text_id)
            except Exception:   # Incase mask already has a text id but nothing on that canvas
                pass

            self._text_id = None

        # Get absolute rectangle in current canvas coordinates
        x1, y1, x2, y2 = self.translate_absolute_coordinates(canvas)

        # Correctly order coordinates.
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))

        rect_w = right - left
        rect_h = bottom - top

        if rect_w <= 0 or rect_h <= 0:
            return

        # Apply padding (as fraction of rect dims)
        pad_x = padding * rect_w
        pad_y = padding * rect_h
        available_w = max(1, rect_w - 2 * pad_x)
        available_h = max(1, rect_h - 2 * pad_y)

        # Font measurement helpers
        def text_size_for_font_size(fs: int) -> Tuple[int, int]:
            f = tkfont.Font(family=font, size=fs)
            width = f.measure(text)
            height = f.metrics("linespace")
            return width, height

        # Binary search for maximum font size that fits in both dimensions
        # Set reasonable bounds for font sizes
        max_possible = int(min(available_h, available_w) * 2) + 4  # very loose upper bound
        lo, hi = 1, max_possible
        best = 1

        while lo <= hi:
            mid = (lo + hi) // 2
            w, h = text_size_for_font_size(mid)
            if w <= available_w and h <= available_h:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1

        # Final font
        final_font = tkfont.Font(family=font, size=best)

        # Center the text in the rectangle
        cx = left + rect_w / 2
        cy = top + rect_h / 2

        # Create text item (anchor center)
        self._text_id = canvas.create_text(
            round(cx),
            round(cy),
            text=text,
            font=final_font,
            anchor="center"
        )
