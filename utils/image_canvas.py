# Standard library imports
import io
from typing import Optional, TypedDict

# Third-party imports
import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError

# Local application imports
from utils.image_tools import restricted_resize_image
from utils.app_logging import LogLevel

class ImageCanvas(tk.Canvas):
    """Canvas to hold an image"""

    def __init__(
            self,
            parent: tk.Widget,
            controller: tk.Tk,
            width: int,
            height: int,
            **kwargs
    ) -> None:
        # Parameter attributes
        self.parent = parent
        self.controller = controller

        self.max_width = width
        self.max_height = height

        self.width = width
        self.height = height

        # Initialize the base tk.Canvas
        super().__init__(
            self.parent,
            width=width,
            height=height,
            borderwidth=0,
            highlightthickness=0,
            **kwargs
        )

        self._question_image_binary = None

        # Placeholder image
        self.tk_question_image = ImageTk.PhotoImage(
            Image.new(
                'RGBA',
                (1, 1),
                (0, 0, 0, 0)
            )
        )

        # Draw the placeholder.
        self.create_image(0, 0, anchor='nw', image=self.tk_question_image)

    def render_image(self) -> None:
        """Render and display the image from binary data onto the canvas."""
        try:
            # Wrap binary in BytesIO and let PIL open it
            orig_question_image = Image.open(
                io.BytesIO(self._question_image_binary)
            )

        except TypeError as e:
            # Not a bytes-like object
            self.controller.log(LogLevel.ERROR, "[render_image] invalid data type: {e}")
            self.delete('all')
            return

        except UnidentifiedImageError as e:
            # PIL can’t parse binary
            self.controller.log(LogLevel.ERROR, f"[render_image] could not decode image data: {e}")
            self.delete('all')
            return

        # Resize the image
        resized_image = restricted_resize_image(
            orig_question_image,
            self.max_width,
            self.max_height
        )

        # Convert the resized PIL image to a Tk image
        self.tk_question_image = ImageTk.PhotoImage(resized_image)

        self.width, self.height = self.tk_question_image.width(), self.tk_question_image.height()

        # Update the canvas dimensions to match the image
        self.config(width=self.width, height=self.height)

        # Display the image on the canvas
        self.create_image(0, 0, anchor='nw', image=self.tk_question_image)

    @property
    def question_image_binary(self) -> bytes:
        return self._question_image_binary

    @question_image_binary.setter
    def question_image_binary(self, binary: bytes) -> None:
        self._question_image_binary = binary
        self.render_image()