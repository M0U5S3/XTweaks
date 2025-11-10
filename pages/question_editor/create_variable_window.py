# Standard library imports
import re

# Third-party imports
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Local application imports
from utils.mask import Mask
from utils.variable import Variable
from utils.app_logging import LogLevel
from utils.style import style


class CreateVariableWindow(tk.Toplevel):
    """Pop-up window to define a new variable or link to an existing one."""

    def __init__(
            self,
            parent,
            controller: tk.Tk,
            mask: Mask,
            variables: dict[str, Variable]
    ) -> None:
        # === Page Setup ===
        super().__init__(parent)
        self.transient(parent)  # Tie minimizing to main window
        self.grab_set()  # block interaction with main window

        # Parameter attributes
        self.parent = parent
        self.controller = controller
        self.mask = mask
        self._variables = variables

        # Load config attributes
        self._max_variable_name_length = self.controller.get_config("max_variable_length")
        self._allowed_variable_characters_pattern =  re.compile(self.controller.get_config("allowed_variable_characters"))

        self.title("Create / Link Variable")

        # Track whether the page is being closed intentionally (via valid progression)
        self._intentional_close = False  # Set to True when the user correctly advances past this page
        self.bind("<Destroy>", self._on_destruction)
        self._direct_destroy = super().destroy

        # Produce a list of existing variable names.
        self.existing_variable_names = list(self._variables.keys())

        # === Style Setup ===
        fonts = style.get_fonts()
        button_style = style.get_button_style_question_editor()
        label_style = style.get_label_style()
        frame_style = style.get_frame_style()

        # === Define Widgets ===

        # -- Header --
        header = ttk.Label(self, text="Create / Link Variable", font=fonts["title"], **label_style)

        # -- Variable name label and entry --
        name_label = ttk.Label(self, text="Variable name (case-sensitive):", font=fonts["default"], **label_style)

        # After each key press update existing or creating.
        self.var_name_entry = tk.Entry(self, width=30)
        self.var_name_entry.bind("<KeyRelease>", self._on_name_change)

        # Tells user whether this variable is being created or already exists.
        self.feedback_label = tk.Label(self, text="", font=fonts["default"], foreground="blue")

        # -- Existing variables list --
        existing_label = ttk.Label(self, text="Existing variables:", font=fonts["default"], **label_style)

        self.listbox = tk.Listbox(self, height=6, exportselection=False)
        for name in self.existing_variable_names:
            self.listbox.insert(tk.END, name)  # Append each known variable to list
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # -- Buttons --
        button_frame = tk.Frame(self, **frame_style)

        cancel_button = tk.Button(button_frame, text="Cancel", command=self.destroy, **button_style)
        confirm_button = tk.Button(button_frame, text="Confirm", command=self._on_confirm, **button_style)

        # === Pack Widgets ===

        # -- Header --
        header.pack(pady=10)

        # -- Name input --
        name_label.pack(anchor="w", padx=10, pady=(10, 2))
        self.var_name_entry.pack(padx=10, pady=(0, 5))

        # -- Feedback --
        self.feedback_label.pack(anchor="w", padx=10)

        # -- Existing variables --
        existing_label.pack(anchor="w", padx=10, pady=(10, 2))
        self.listbox.pack(padx=10, fill="both")

        # -- Buttons --
        button_frame.pack(pady=10)
        cancel_button.pack(side=tk.LEFT, padx=5)
        confirm_button.pack(side=tk.LEFT, padx=5)

        # Start focused on the only text input
        self.var_name_entry.focus()

        self.controller.log(LogLevel.DEBUG, 'Opened variable link window')

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

    def _validate_name(self, name: str) -> str | None:
        """
        Validate a variable name and return a feedback string
        describing the first problem found, or None if the name is valid.

        Priority of checks:
          1. Empty
          2. Too long (self._max_variable_name_length)
          3. Invalid characters (anything not matching self._allowed_variable_characters_pattern)
        """

        if not name:
            return "Please enter a variable name."

        if len(name) > self._max_variable_name_length:
            return f"Name too long: {len(name)} characters (maximum {self._max_variable_name_length})."

        # Find offending characters in order of first appearance, unique
        offending = []
        for ch in name:
            if not self._allowed_variable_characters_pattern.fullmatch(ch):
                if ch not in offending:
                    offending.append(ch)

        if offending:
            offending_display = ", ".join(repr(ch) for ch in offending)
            return (
                f"Invalid characters: {offending_display}. "
                f"Allowed: {self._allowed_variable_characters_pattern.pattern}."
            )

        # If we reach here the name is valid
        return

    def _update_feedback(self, name: str):
        """
        Live feedback for the entry. Uses _validate_name for the validation part,
        and if valid, reports whether the name will create a new variable or use
        an existing one.
        """
        # Validate the variable name.
        error = self._validate_name(name)

        if error:
            # Show the reason for bad input.
            self.feedback_label.config(text=error, fg="red")
            return

        # If name is valid tell user if they are creating a variable or linking one.
        if self.variable_exists(name):
            self.feedback_label.config(text="Using existing variable.", fg="green")
        else:
            self.feedback_label.config(text="Creating new variable.", fg="blue")

    def _on_confirm(self):
        """
        Ensure the variable name is valid. If it is then create or
        link the variable, if it isn't then show an appropriate warning
        and update the feedback label.
        """

        name = self.var_name_entry.get()

        # Final validation via helper
        error = self._validate_name(name)
        if error:
            # Update feedback label and show consistent warning dialog
            self.feedback_label.config(text=error, fg="red")
            messagebox.showwarning("Invalid Variable Name", error)
            return

        # Name is valid: proceed with create/link logic
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
