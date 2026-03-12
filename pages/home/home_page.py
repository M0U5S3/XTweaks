# Third-party imports
import tkinter as tk
from tkinter import font

# Local application imports
from utils.app_logging import LogLevel
from utils.pages import Pages
from utils.style import style


class Home(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")

        self.parent = parent
        self.controller = controller

        # Fonts
        title_font = font.Font(family="Helvetica", size=24, weight="bold")
        button_font = font.Font(family="Helvetica", size=12)

        # Title
        title = tk.Label(self, text="XTweak Revision Tools", font=title_font, bg="#f0f4f8", fg="#2c3e50")
        title.pack(pady=(40, 20))
        # todo apply styles.py somehow maybe by default in controller

        subtitle = tk.Label(self, text="Choose your path to mathematical greatness:",
                            font=("Helvetica", 14), bg="#f0f4f8", fg="#34495e")
        subtitle.pack(pady=(0, 30))

        # Button style
        button_style = style.get_button_style_home()

        # Buttons
        self.create_button("🧠 Question Tweaker", self.go_to_tweaker, **button_style)
        self.create_button("📡 Open Questions", self.go_to_viewer, **button_style)

    def create_button(self, text, command, **kwargs):
        btn = tk.Button(self, text=text, command=command, **kwargs)
        btn.pack(pady=10)

    # Navigation methods
    def go_to_tweaker(self):
        self.controller.show_page(Pages.QUESTION_EDITOR)
        # todo all of below

    def go_to_viewer(self):
        self.controller.show_page(Pages.QUESTION_VIEWER)
