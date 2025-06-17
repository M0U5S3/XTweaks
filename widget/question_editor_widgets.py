import io

from PIL import Image, ImageTk

import tkinter as tk
from utils.image_tools import restricted_resize_image

WIN_WIDTH, WIN_HEIGHT = 1000, 700   # Define window geometry. Test on other resolution screens
MAX_RELATIVE_IMAGE_HEIGHT = 0.40    # Define Scale of image relative to window size
MAX_RELATIVE_IMAGE_WIDTH = 0.80


class QuestionCanvas(tk.Canvas):
    def __init__(self, parent, controller, question_image_binary, *args, **kwargs):
        self.controller = controller
        self.parent = parent

        super().__init__(
            self.parent,
            width=MAX_RELATIVE_IMAGE_WIDTH * self.controller.screen_width,
            height=MAX_RELATIVE_IMAGE_HEIGHT * self.controller.screen_height,
            *args,
            **kwargs
        )

        self.question_image_binary = question_image_binary

        self.mouse_x = tk.StringVar()
        self.mouse_y = tk.StringVar()

        self.mouse_x.set('X: 0')
        self.mouse_y.set('Y: 0')

        self.bind("<Button-1>", self._canvas_click)
        self.bind("<Motion>", self._update_mouse_display)

    def _canvas_click(self, event):
        print(f'Click at ({event.x},{event.y})')
        self.create_oval(event.x - 1, event.y - 1, event.x + 1, event.y + 1, fill="black", outline="black")

    def _update_mouse_display(self, event):
        self.mouse_x.set(f'X: {event.x}')
        self.mouse_y.set(f'Y: {event.y}')

    def render_image(self):
        orig_question_image = Image.open(io.BytesIO(self._question_image_binary))  # Open image from binary data

        # Define the target dimensions
        target_width = int(MAX_RELATIVE_IMAGE_WIDTH * self.controller.screen_width)
        target_height = int(MAX_RELATIVE_IMAGE_HEIGHT * self.controller.screen_height)

        self.tk_question_image = ImageTk.PhotoImage(restricted_resize_image(orig_question_image, target_width, target_height))

        self.config(width=self.tk_question_image.width(), height=self.tk_question_image.height())
        self.create_image(0, 0, anchor='nw', image=self.tk_question_image)

    @property
    def question_image_binary(self):
        return self._question_image_binary

    @question_image_binary.setter
    def question_image_binary(self, binary):
        self._question_image_binary = binary
        self.render_image()