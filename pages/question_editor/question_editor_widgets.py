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
from utils.image_canvas import ImageCanvas


# Type definition
class LassoIds(TypedDict):
    rect_id: Optional[int]
    handler_bind_id: Optional[str]

class QuestionEditorCanvas(ImageCanvas):
    """Canvas to hold image and handle events related to interacting with the image."""

    def __init__(
            self,
            parent: tk.Widget,
            controller: tk.Tk,
            width: int,
            height: int
    ) -> None:
        """
        Initialize the QuestionCanvas widgets.

        Args:
            parent (tk.Widget): The parent widget in which the canvas will be embedded.
            controller (tk.Tk): Root app controller.
            placeholder_image (bytes): Binary data for the image to be displayed.
        """
        self._last_click: Optional[tuple[int, int]] = None  # Stores each first click
        self._lasso_ids: Optional[LassoIds] = {
            'rect_id': None,
            'handler_bind_id': None
        }

        # Initialize the base ImageCanvas.
        super().__init__(
            parent,
            controller,
            width,
            height
        )

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
                *self._last_click,
                event.x,
                event.y,
                self,
                outline='blue'
            )

            # DEBUG
            print(f'old dimensions: {self.width}, {self.height}')
            print(f'old rect: {self._last_click[0]}, {self._last_click[1]}, {event.x}, {event.y}')

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
