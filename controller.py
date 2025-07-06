# Standard library imports
from typing import Any, Dict, Type, Tuple

# Third-party imports
import tkinter as tk

# Local application imports
from pages.question_editor_page import QuestionEditorPage
from pages.home_page import Home


class AppController(tk.Tk):
    """
    Main application controller that allows pages to request root-level actions.

    Inherits from:
        tk.Tk: The base class for Tkinter.

    Class Attributes:
        PAGES (Tuple[Type, ...]): A tuple containing the page classes used in the application.
    """

    # Define all pages
    PAGES: Tuple[Type, ...] = (QuestionEditorPage,)

    def __init__(
            self,
            home_page: Type[tk.Widget] = Home,
    ) -> None:
        """
        Initialize the AppController, set up the main window, and initialize all pages.

        Args:
            home_page (Type[tk.Widget], optional): The default home page class to display.
                Defaults to Home.
        """
        super().__init__()

        # Configure window properties.
        self.title('ExamTweaks')
        self.state('zoomed')  # Start the application in zoomed (maximized) state.
        self.resizable(False, False)  # Disable window resizing.

        # Retrieve screen dimensions.
        self.screen_width: int = self.winfo_screenwidth()
        self.screen_height: int = self.winfo_screenheight()

        # Store the default home page class.
        self.home_page: Type[tk.Widget] = home_page

        # Create a container frame to hold all pages.
        container: tk.Frame = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        # Configure the grid structure to allow expanding.
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Initialize a dictionary to store page instances.
        self.frames: Dict[Type, tk.Widget] = {}

        # Instantiate each page and stack them in the same grid cell.
        for F in AppController.PAGES:
            frame: tk.Widget = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Display the default home page.
        self.show_frame(self.home_page)

    def show_frame(self, page_class: Type) -> None:
        """
        Bring the frame corresponding to the specified page class to the front.

        Args:
            page_class (Type): The class of the page to be displayed.
        """
        frame: tk.Widget = self.frames[page_class]
        frame.tkraise()

    def run(self) -> None:
        """
        Start the Tkinter event loop.
        """
        self.mainloop()

