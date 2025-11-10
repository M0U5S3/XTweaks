# Standard library imports
from typing import Dict
import json

# Third-party imports
from tkinter import font, ttk

# Local application imports
from utils.app_logging import LogLevel

__all__ = ["style"]


class ControllerNotSetError(Exception):
    """Raised when the _StyleManager is used without a controller"""
    pass

def _requires_controller(method):
    """Decorator to check that a controller has been set before running a method"""
    def wrapper(self, *args, **kwargs):
        if self._controller is None:
            raise ControllerNotSetError("StyleManager requires a controller to perform this action.")
        return method(self, *args, **kwargs)
    return wrapper


class _StyleManager:
    def __init__(self, size_multiplier: float = 1.0):
        self._controller = None
        self._theme = None
        self._new_theme = None
        self.size_multiplier = size_multiplier

        self._themes = {
            "light": {
                "background": "#f0f4f8",
                "primary": "#3498db",
                "primary_dark": "#2980b9",
                "text_main": "#2c3e50",
                "text_secondary": "#34495e",
                "button_text": "white",
                "back_button": "#B20F0F",
                "back_button_dark": "#820A0A"
            },
            "dark": {
                "background": "#1e1e2f",
                "primary": "#9b59b6",
                "primary_dark": "#8e44ad",
                "text_main": "#ecf0f1",
                "text_secondary": "#bdc3c7",
                "button_text": "#ffffff",
                "back_button": "#B20F0F",
                "back_button_dark": "#820A0A"
            }
        }

    @_requires_controller
    def _load_theme(self):
        self._theme = self._controller.get_config("theme")
        self._new_theme = self._theme

    @_requires_controller
    def _register_ttk_styles(self):
        style_engine = ttk.Style()

        # Apply current theme
        style_engine.theme_use("clam")

        colors = self.get_colors()

        # Label style
        style_engine.configure("Custom.TLabel",
                               foreground=colors["text_main"],
                               background=colors["background"]
                               )

        # Frame style
        style_engine.configure("Custom.TFrame",
                               background=colors["background"]
                               )

        # Button style
        style_engine.configure("Custom.TButton",
                               foreground=colors["button_text"],
                               background=colors["primary"],
                               padding=6
                               )

        self._controller.log(LogLevel.INFO, f"Initialized ttk styling")

    @_requires_controller
    def toggle_theme(self):
        """Switch between light and dark themes"""
        self._new_theme = "dark" if self._new_theme == "light" else "light"
        self._controller.update_config("theme", self._new_theme)
        self._controller.log(LogLevel.INFO, f'Toggled theme to {self._new_theme}. Waiting to restart...')

    # Dictionaries are wrapped in a function to avoid premature initialization.
    def get_fonts(self) -> Dict:
        """Return font styles"""
        return {
            "title": font.Font(family="Helvetica", size=int(24 * self.size_multiplier), weight="bold"),
            "subtitle": font.Font(family="Helvetica", size=int(14 * self.size_multiplier)),
            "button": font.Font(family="Helvetica", size=int(12 * self.size_multiplier)),
            "default": font.Font(family="Helvetica", size=int(11 * self.size_multiplier))
        }

    def get_button_style_home(self):
        return {
            "font": self.get_fonts()['button'],
            "bg": "#3498db",
            "fg": "white",
            "activebackground": "#2980b9",
            "activeforeground": "white",
            "width": 20,
            "height": 2,
            "bd": 0,
            "relief": "flat",
            "cursor": "hand2"
        }

    def get_button_style_question_editor(self) -> Dict:
        """Return button style of the selected theme"""
        colors = self.get_colors()
        return {
            "font": self.get_fonts()['button'],
            "bg": colors["primary"],
            "fg": colors["button_text"],
            "activebackground": colors["primary_dark"],
            "activeforeground": colors["button_text"],
            "width": 20,
            "height": 2,
            "bd": 0,
            "relief": "flat",
            "cursor": "hand2"
        }

    def get_label_style(self) -> Dict:
        colors = self.get_colors()
        return {
            "foreground": colors["text_main"],
            "background": colors["background"]
        }

    def get_frame_style(self) -> Dict:
        colors = self.get_colors()
        return {
            "background": colors["background"]
        }

    def get_back_button_style(self) -> Dict:
        """Return style for a small back button in the top-left corner"""
        colors = self.get_colors()
        return {
            "bg": colors["back_button"],
            "fg": colors["text_main"],
            "activebackground": colors["back_button_dark"],
            "activeforeground": colors["button_text"],
            "bd": 1,
            "relief": "solid",
            "cursor": "hand2",
            "font": font.Font(family="Helvetica", size=int(10 * self.size_multiplier)),
            "width": 3,
            "height": 1
        }

    def get_colors(self) -> Dict:
        """Return colours of the selected theme"""
        return self._themes[self._theme]

    def set_controller(self, controller):
        """Attach the shared controller instance"""
        self._controller = controller
        self._load_theme()
        self._register_ttk_styles()
        self._controller.log(LogLevel.INFO, f"Styler controller set. {self._theme} theme selected.")

# Shared instance
style = _StyleManager()
