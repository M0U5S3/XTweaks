# Standard library imports
from typing import Callable

# Third-party imports
import tkinter as tk
from tkinter import messagebox

# Local application imports
from utils.mask import Mask
from utils.variable import Variable
from utils.app_logging import LogLevel

class CreateVariableWindow(tk.Toplevel):
    """
    Pop-up window to define a new variable or link to an existing one.
    Case-sensitive name checking with real-time feedback.
    """

    def __init__(
        self,
        parent: tk.Widget,
        controller: tk.Tk,
        mask: Mask,
        create_variable: Callable[[Variable], None],
        variables: dict[str: Variable],
    ) -> None:
        """
        Args:
            parent: Parent widget.
            controller: Root app controller.
            mask: The mask that triggered the window.
            create_variable: Callback for adding/linking a variable.
            variables: List of all existing variables.
        """

        super().__init__(parent)
        self.transient(parent)  # Tie minimizing to main window
        self.grab_set()  # block interaction with main window

        # Parameter attributes
        self.parent = parent
        self.controller = controller
        self.mask = mask
        self.create_variable = create_variable
        self._variables = variables

        # Track whether the page is being closed intentionally (via valid progression)
        self._intentional_close = False  # Set to True when the user correctly advances past this page
        self.bind('<Destroy>', self._on_destruction)
        self._direct_destroy = super().destroy

        # Produce a list of existing variable names.
        self.existing_variable_names = list(self._variables.keys())

        self.title("Create / Link Variable")

        # --= Widgets =--
        tk.Label(self, text="Variable name (case-sensitive):").pack(anchor="w", padx=10, pady=(10, 2))

        # After each key press update existing or creating.
        self.var_name_entry = tk.Entry(self, width=30)
        self.var_name_entry.pack(padx=10, pady=(0, 5))
        self.var_name_entry.bind("<KeyRelease>", self._on_name_change)

        # Tells user whether this variable is being created or already exists.
        self.feedback_label = tk.Label(self, text="", fg="blue")
        self.feedback_label.pack(anchor="w", padx=10)

        tk.Label(self, text="Existing variables:").pack(anchor="w", padx=10, pady=(10, 2))

        self.listbox = tk.Listbox(self, height=6, exportselection=False)
        for name in self.existing_variable_names:
            self.listbox.insert(tk.END, name)   # Append each known variable to list
        self.listbox.pack(padx=10, fill="both")
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # --- Buttons ---
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Confirm", command=self._on_confirm).pack(side=tk.LEFT, padx=5)

        self.var_name_entry.focus() # Start focused on the only text input

    def _on_listbox_select(self, event):
        """Update entry when user selects from list."""
        selection = self.listbox.curselection() # Index of selected item
        if selection:   # Guard from user clicking empty space on the list
            selected = self.listbox.get(selection[0])
            self.var_name_entry.delete(0, tk.END)
            self.var_name_entry.insert(0, selected)
            self._update_feedback(selected)

    def _on_name_change(self, event):
        """Called whenever the entry text changes."""
        name = self.var_name_entry.get().strip()
        self._update_feedback(name)

    def variable_exists(self, name: str) -> bool:
        """Return True if `name` matches an existing variable (case-sensitive)."""
        return name in self.existing_variable_names

    def _update_feedback(self, name: str):
        """Display whether this is existing or new."""
        if not name:
            self.feedback_label.config(text="Please enter a variable name.", fg="red")
        elif self.variable_exists(name):
            self.feedback_label.config(text="Using existing variable.", fg="green")
        else:
            self.feedback_label.config(text="Creating new variable.", fg="blue")

        # todo add regex validation

    def _on_confirm(self):
        """Validate and run the creation/link logic."""
        name = self.var_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid Name", "Please enter a variable name.")
            return

        # Process:
        # 1. Check if the variable name already exists.
        #    - If it does: retrieve the variable object and append the mask.
        #    - If it doesn't: create a new variable with its mask.
        # 2. Intentionally destroy the window.

        if self.variable_exists(name):
            self._variables[name].add_mask(self.mask)

        else:
            self._variables[name] = Variable(name, [self.mask])

        self.destroy(intentional=True)

    def destroy(self, intentional=False):
        self._intentional_close = intentional
        self.controller.log(LogLevel.DEBUG, 'Window closure detected')
        self._direct_destroy()

    def _on_destruction(self, event):
        if not self._intentional_close:
            self.mask.delete_rectangle()
