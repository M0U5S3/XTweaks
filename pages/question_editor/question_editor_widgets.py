# Standard library imports
import io
from typing import Optional, TypedDict

# Third-party imports
import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError

# Local application imports
from utils.image_tools import restricted_resize_image
from utils.mask import Mask
from utils.app_logging import LogLevel

# Constants for image scaling
MAX_RELATIVE_IMAGE_HEIGHT = 0.20  # Maximum image height as a fraction of the window's height
MAX_RELATIVE_IMAGE_WIDTH = 0.40  # Maximum image width as a fraction of the window's width


# Type definition
class LassoIds(TypedDict):
    rect_id: Optional[int]
    handler_bind_id: Optional[str]

class QuestionCanvas(tk.Canvas):
    """Canvas to hold image and handle events related to interacting with the image."""

    def __init__(
            self,
            parent: tk.Widget,
            controller: tk.Tk,
            placeholder_image: bytes
    ) -> None:
        """
        Initialize the QuestionCanvas widgets.

        Args:
            parent (tk.Widget): The parent widget in which the canvas will be embedded.
            controller (tk.Tk): Root app controller.
            placeholder_image (bytes): Binary data for the image to be displayed.
        """

        # Parameter attributes
        self.parent = parent
        self.controller = controller

        self._last_click: Optional[tuple[int, int]] = None  # Stores each first click
        self._lasso_ids: Optional[LassoIds] = {
            'rect_id': None,
            'handler_bind_id': None
        }

        # Initialize the base tk.Canvas using the parent widgets and computed width/height
        super().__init__(
            self.parent,
            width=MAX_RELATIVE_IMAGE_WIDTH * self.controller.screen_width,
            height=MAX_RELATIVE_IMAGE_HEIGHT * self.controller.screen_height
        )

        # Placeholder image
        self.tk_question_image = ImageTk.PhotoImage(
            Image.new(
                'RGBA',
                (1, 1),
                (0, 0, 0, 0)
            )
        )
        self.question_image_binary = placeholder_image

        # draw the placeholder so the attribute is “used” immediately
        self.create_image(0, 0, anchor='nw', image=self.tk_question_image)

        # Position vars
        self.mouse_x: tk.StringVar = tk.StringVar(value='X: 0')
        self.mouse_y: tk.StringVar = tk.StringVar(value='Y: 0')

        # Bind mouse events for clicking and movement
        self.bind('<Button-1>', self._canvas_click)
        self.bind('<Motion>', self._update_mouse_display)

    def _canvas_click(self, event) -> None:
        """Handle left clicks on the canvas."""

        # Make sure the canvas actually contains a question image.
        if not self.parent.question_image_imported:
            return

        # If this is the first click (no existing `_last_click`)
        if self._last_click is None:
            # Create dashed rectangle at (event.x, event.y)
            self._lasso_ids['rect_id'] = self.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline='blue',
                dash=(2, 2),
            )

            # Bind mouse motion to `_handle_lasso`
            self._lasso_ids['handler_bind_id'] = self.bind('<Motion>', self._handle_lasso, add='+')
            self._last_click = (event.x, event.y)

        # If this is the second click, finish the lasso:
        else:
            # Unbind the motion handler
            self.unbind('<Motion>', self._lasso_ids['handler_bind_id'])
            self.delete(self._lasso_ids['rect_id'])

            # Draw a solid rectangle from the stored start to here
            mask = Mask(
                self.create_rectangle(
                    *self._last_click,
                    event.x,
                    event.y,
                    outline='blue',
                ),
                self
            )

            # Pass mask up to page
            self.parent.on_second_click(mask)

            # Reset everything
            self._lasso_ids['handler_bind_id'] = None
            self._lasso_ids['rect_id'] = None
            self._last_click = None

    def _handle_lasso(self, event) -> None:
        """
        Update the dashed lasso rectangle as the mouse moves.
        """

        if self._last_click is None:    # Guard against race conditions
            return

        self.coords(
            self._lasso_ids['rect_id'],
            *self._last_click,
            event.x,
            event.y
        )

    def _update_mouse_display(self, event: tk.Event) -> None:
        """
        Update the position of the mouse on self.

        Args:
            event (tk.Event): Event data with current mouse coordinates.
        """
        self.mouse_x.set(f'X: {event.x}')
        self.mouse_y.set(f'Y: {event.y}')

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

        # Calculate max target dimensions for the image
        target_width = int(MAX_RELATIVE_IMAGE_WIDTH * self.controller.screen_width)
        target_height = int(MAX_RELATIVE_IMAGE_HEIGHT * self.controller.screen_height)

        # Resize the image
        resized_image = restricted_resize_image(
            orig_question_image,
            target_width,
            target_height
        )

        # Convert the resized PIL image to a Tk image
        self.tk_question_image = ImageTk.PhotoImage(resized_image)

        # Update the canvas dimensions to match the image
        self.config(width=self.tk_question_image.width(), height=self.tk_question_image.height())

        # Display the image on the canvas
        self.create_image(0, 0, anchor='nw', image=self.tk_question_image)

    @property
    def question_image_binary(self) -> bytes:
        """
        Getter for the question image binary data.

        Returns:
            bytes: The binary data of the question image.
        """
        return self._question_image_binary

    @question_image_binary.setter
    def question_image_binary(self, binary: bytes) -> None:
        """
        Setter for the question image binary data. Automatically renders image.

        Args:
            binary (bytes): New binary data for the image.
        """
        self._question_image_binary = binary
        self.render_image()
