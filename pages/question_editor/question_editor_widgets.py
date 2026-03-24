# Standard library imports
import io
from typing import Optional, TypedDict, Callable

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

        # If this is the first click (no `_last_click`)
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

            # Pass mask up to page
            self.parent.on_second_click(mask)

            # Reset everything
            self._lasso_ids['handler_bind_id'] = None
            self._lasso_ids['rect_id'] = None
            self._last_click = None

    def _handle_lasso(self, event) -> None:
        """Update the dashed lasso rectangle as the mouse moves."""

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

class ArrowStepper(tk.Frame):
    def __init__(
        self,
        parent,
        step: Callable[[], None],
        max_pages: int
    ) -> None:
        super().__init__(parent)
        self._step = step

        self._max_pages = max(1, int(max_pages))
        self._page = 1

        # Create buttons and middle display
        self.btn_left = tk.Button(self, text="◀", width=3, command=self._on_left)
        self.lbl_page = tk.Label(self, text=f"{self._page}/{self._max_pages}", width=8, anchor="center")
        self.btn_right = tk.Button(self, text="▶", width=3, command=self._on_right)

        # Layout: left, middle, right
        self.btn_left.pack(side=tk.LEFT, padx=(0, 4))
        self.lbl_page.pack(side=tk.LEFT)
        self.btn_right.pack(side=tk.LEFT, padx=(4, 0))

        # Keyboard bindings (global) for convenience
        self.bind_all("<Left>", lambda e: self._on_left())
        self.bind_all("<Right>", lambda e: self._on_right())

        # initial display update
        self._update_display()

    def _update_display(self) -> None:
        """Refresh the middle label and enable/disable buttons as appropriate."""
        # Clamp page into valid range.
        if self._page < 1:
            self._page = 1
        if self._max_pages < 1:
            self._max_pages = 1
        if self._page > self._max_pages:
            self._page = self._max_pages

        # Update label.
        self.lbl_page.config(text=f"{self._page}/{self._max_pages}")

        # Disable/enable buttons at bounds for clearer UX.
        self.btn_left.config(state=tk.NORMAL if self._page > 1 else tk.DISABLED)
        self.btn_right.config(state=tk.NORMAL if self._page < self._max_pages else tk.DISABLED)

    def _on_left(self) -> None:
        if self._page > 1:
            self._page -= 1
            self._update_display()
            self._step()

    def _on_right(self) -> None:
        if self._page < self._max_pages:
            self._page += 1
            self._update_display()
            self._step()

    def set_max_pages(self, max_pages: int) -> None:
        """Update max_pages and refresh the display"""
        self._max_pages = max(1, int(max_pages))
        self._update_display()

    def set_page(self, page: int) -> None:
        """Set the current page and refresh the display."""
        self._page = int(page)
        self._update_display()

    def get_page(self) -> int:
        """Return the current page number."""
        return self._page
