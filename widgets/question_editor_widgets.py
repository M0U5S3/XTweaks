# Standard library imports
import io
from typing import Callable, Optional, TypedDict

# Third-party imports
import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError

# Local application imports
from utils.image_tools import restricted_resize_image
from utils.mask import Mask

# Constants for image scaling
MAX_RELATIVE_IMAGE_HEIGHT: float = 0.20  # Maximum image height as a fraction of the window's height
MAX_RELATIVE_IMAGE_WIDTH: float = 0.40  # Maximum image width as a fraction of the window's width


class LassoIds(TypedDict):
    rect_id: Optional[int]
    handler_bind_id: Optional[str]

class QuestionCanvas(tk.Canvas):
    """
    Canvas to hold image and handle events related to interacting with the image.
    """

    def __init__(
            self,
            parent: tk.Widget,
            controller: tk.Tk,
            placeholder_image: bytes,
            on_second_click: Callable[[Mask], None]
    ) -> None:
        """
        Initialize the QuestionCanvas widgets.

        Args:
            parent (tk.Widget): The parent widget in which the canvas will be embedded.
            controller (tk.Tk): Root app controller.
            placeholder_image (bytes): Binary data for the image to be displayed.
        """

        # Parameter attributes
        self.parent: tk.Widget = parent
        self.controller: tk.Tk = controller
        self.on_second_click = on_second_click

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
        self.question_image_binary: bytes = placeholder_image

        # draw the placeholder so the attribute is “used” immediately
        self.create_image(0, 0, anchor='nw', image=self.tk_question_image)

        # Position vars
        self.mouse_x: tk.StringVar = tk.StringVar(value='X: 0')
        self.mouse_y: tk.StringVar = tk.StringVar(value='Y: 0')

        # Bind mouse events for clicking and movement
        self.bind('<Button-1>', self._canvas_click)
        self.bind('<Motion>', self._update_mouse_display)

    def _canvas_click(self, event: tk.Event) -> None:
        """
        Handle left mouse button clicks on the canvas.

        On first click, begin a dashed “lasso” rectangle for selection.
        On second click, finalize the rectangle, unbind the motion handler,
        and hand off the region for masking elsewhere.

        Args:
            event (tk.Event): Event data containing the click's coordinates.
        """

        # Process:
        # - If this is the first click (no existing `_last_click`), start drawing a lasso:
        #     - Bind mouse motion to `_handle_lasso`
        #     - Create dashed rectangle at (event.x, event.y)
        # - If this is the second click, finish the lasso:
        #     - Unbind the motion handler
        #     - Draw a solid rectangle from the stored start to (event.x, event.y)
        #     - Reset `_last_click`

        if not self.parent.check_image():
            return

        if self._last_click is None:
            self._lasso_ids['rect_id'] = self.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline='blue',
                dash=(2, 2),
            )
            self._lasso_ids['handler_bind_id'] = self.bind('<Motion>', self._handle_lasso, add='+')
            self._last_click = (event.x, event.y)

        else:
            self.unbind('<Motion>', self._lasso_ids['handler_bind_id'])
            self.delete(self._lasso_ids['rect_id'])
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
            self.on_second_click(mask)

            self._lasso_ids['handler_bind_id'] = None
            self._lasso_ids['rect_id'] = None
            self._last_click = None

    def _handle_lasso(self, event: tk.Event) -> None:
        """
        Update the dashed lasso rectangle as the mouse moves.

        Args:
            event (tk.Event): Event data containing the click's coordinates.
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
        """
        Render and display the image from binary data onto the canvas.

        Process:
            - Use PIL to treat binary data as an image file.
            - Calculate the max target dimensions based on screen size and scaling constants.
            - Resizes the image using 'restricted_resize_image' to preserve aspect ratio.
            - Updates the canvas size to math the image and renders the image.

        Raises:
            Exception: Raises any exception thrown during image processing.
        """
        try:
            # Wrap raw bytes in BytesIO and let PIL open it
            orig_question_image: Image.Image = Image.open(
                io.BytesIO(self._question_image_binary)
            )

        except TypeError as e:
            # Not a bytes-like object
            print(f"[render_image] invalid data type: {e}") # todo use log
            self.delete('all')
            return

        except UnidentifiedImageError as e:
            # Valid buffer, but PIL can’t parse it
            print(f"[render_image] could not decode image data: {e}")
            self.delete('all')
            return

        # Calculate max target dimensions for the image
        target_width: int = int(MAX_RELATIVE_IMAGE_WIDTH * self.controller.screen_width)
        target_height: int = int(MAX_RELATIVE_IMAGE_HEIGHT * self.controller.screen_height)

        # Resize the image while preserving its aspect ratio
        resized_image: Image.Image = restricted_resize_image(
            orig_question_image,
            target_width,
            target_height
        )

        # Convert the resized PIL image to a Tk image
        self.tk_question_image: ImageTk.PhotoImage = ImageTk.PhotoImage(resized_image)

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
        self._question_image_binary: bytes = binary
        self.render_image()
