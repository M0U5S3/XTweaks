import tkinter as tk
from tkinter import ttk
from widget.question_editor_widgets import QuestionCanvas


class QuestionEditorPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Placeholder
        with open("placeholder_image.jpg", "rb") as f:
            question_image_binary = f.read()

        self.controller = controller

        # Title or header for the page.
        self.header = ttk.Label(self, text="Question Editor", font=("Arial", 20))

        # Instantiate and pack the custom QuestionCanvas.
        self.question_canvas = QuestionCanvas(self, controller, question_image_binary)

        self.x_display = ttk.Label(self.controller, textvariable=self.question_canvas.mouse_x)
        self.y_display = ttk.Label(self.controller, textvariable=self.question_canvas.mouse_y)

        self.header.pack(pady=10)
        self.question_canvas.pack(pady=20)
        self.x_display.pack()
        self.y_display.pack()
