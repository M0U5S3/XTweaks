# Standard library imports
from datetime import datetime
from typing import Optional, Dict, Any

# Third-party imports
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Local application imports
from utils.app_logging import LogLevel
from utils.style import style


class CreateQuestionWindow(tk.Toplevel):
    """Pop-up window to enter question metadata and export."""

    DIFFICULTIES = ("easy", "normal", "hard", "extreme")

    def __init__(self, parent, controller: tk.Tk) -> None:
        # === Page Setup ===
        super().__init__(parent)
        self.transient(parent)  # Tie minimizing to main window
        self.grab_set()  # block interaction with main window

        # Parameter attributes
        self.parent = parent
        self.controller = controller

        # Title
        self.title("Question metadata")

        # Result placeholder
        self.result: Optional[Dict[str, Any]] = None

        # Current time constraints
        self._current_year = datetime.now().year
        self._current_month = datetime.now().month

        # === Style Setup ===
        fonts = style.get_fonts()
        button_style = style.get_button_style_question_editor()
        label_style = style.get_label_style()
        frame_style = style.get_frame_style()

        # === Define Widgets ===

        # -- Header --
        header = ttk.Label(self, text="Question metadata", font=fonts["title"], **label_style)

        # -- Calculator allowed --
        self.var_calculator_allowed = tk.BooleanVar(value=False)
        chk_calculator = ttk.Checkbutton(self, text="Calculator allowed", variable=self.var_calculator_allowed)

        # -- Difficulty --
        diff_label = ttk.Label(self, text="Difficulty:", font=fonts["default"], **label_style)
        self.ent_difficulty = ttk.Combobox(self, values=self.DIFFICULTIES, state="readonly")
        self.ent_difficulty.set(self.DIFFICULTIES[0])

        # -- Question number --
        qnum_label = ttk.Label(self, text="Question number:", font=fonts["default"], **label_style)
        self.ent_question_number = tk.Entry(self, width=30)

        # -- Exam board --
        exam_label = ttk.Label(self, text="Exam board:", font=fonts["default"], **label_style)
        self.ent_exam_board = tk.Entry(self, width=30)

        # -- Year and Month --
        year_label = ttk.Label(self, text="Year:", font=fonts["default"], **label_style)
        self.var_year = tk.IntVar(value=self._current_year)
        self.ent_year = tk.Spinbox(self, from_=0, to=self._current_year, textvariable=self.var_year, width=10,
                                   command=self._enforce_month_limit)

        month_label = ttk.Label(self, text="Month:", font=fonts["default"], **label_style)
        self.var_month = tk.IntVar(value=self._current_month)
        self.ent_month = tk.Spinbox(self, from_=1, to=12, textvariable=self.var_month, width=10)

        # Feedback label (validation)
        self.feedback_label = tk.Label(self, text="", font=fonts["default"], foreground="blue")

        # -- Buttons --
        button_frame = tk.Frame(self, **frame_style)
        self.btn_export = tk.Button(button_frame, text="Export", command=self._on_export, **button_style)
        self.btn_cancel = tk.Button(button_frame, text="Cancel", command=self.destroy, **button_style)

        # === Pack Widgets ===

        # -- Header --
        header.pack(pady=10)

        # -- Calculator --
        chk_calculator.pack(anchor="w", padx=10, pady=(0, 8))

        # -- Difficulty --
        diff_label.pack(anchor="w", padx=10, pady=(6, 2))
        self.ent_difficulty.pack(padx=10, fill="x")

        # -- Question number --
        qnum_label.pack(anchor="w", padx=10, pady=(10, 2))
        self.ent_question_number.pack(padx=10, pady=(0, 5), fill="x")

        # -- Exam board --
        exam_label.pack(anchor="w", padx=10, pady=(6, 2))
        self.ent_exam_board.pack(padx=10, pady=(0, 5), fill="x")

        # -- Year / Month --
        year_label.pack(anchor="w", padx=10, pady=(6, 2))
        self.ent_year.pack(padx=10, pady=(0, 5), anchor="w")

        month_label.pack(anchor="w", padx=10, pady=(6, 2))
        self.ent_month.pack(padx=10, pady=(0, 5), anchor="w")

        # -- Feedback --
        self.feedback_label.pack(anchor="w", padx=10, pady=(6, 0))

        # -- Buttons --
        button_frame.pack(pady=12)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        self.btn_export.pack(side=tk.LEFT, padx=5)

        # When the year changes check the month is still valid
        self.var_year.trace_add("write", lambda *_: self._enforce_month_limit())

        # Start focused on the first text input
        self.ent_question_number.focus()

        self.controller.log(LogLevel.DEBUG, "Opened question metadata window")

    def _enforce_month_limit(self):
        # If this year is the year selected, make the maximum month the current month.
        year = int(self.var_year.get())
        max_month = self._current_month if year == self._current_year else 12
        self.ent_month.config(to=max_month)

        # Clamp the month down if the user already selected an out of bound option.
        if int(self.var_month.get()) > max_month:
            self.var_month.set(max_month)

    def _validate(self) -> Optional[str]:
        qnum = self.ent_question_number.get().strip()
        if qnum:
            try:
                qn = int(qnum)
                if qn < 1:
                    return "Question number must be one or positive."
            except ValueError:
                return "Question number must be an integer."

        # optional
        year_raw = self.var_year.get()
        year: Optional[int]
        if year_raw == "" or year_raw is None:
            year = None
        else:
            try:
                year = int(year_raw)
            except ValueError:
                return "Year must be an integer."
            if not (0 <= year <= self._current_year):
                return f"Year must be between 0 and {self._current_year}."

        # optional
        month_raw = self.var_month.get()
        month: Optional[int]
        if month_raw == "" or month_raw is None:
            month = None
        else:
            try:
                month = int(month_raw)
            except ValueError:
                return "Month must be an integer."
            if not (1 <= month <= 12):
                return "Month must be between 1 and 12."
            # only enforce current-month constraint if year is provided and equals current year
            if year is not None and year == self._current_year and month > self._current_month:
                return f"For the current year, month must be ≤ {self._current_month}."

        # difficulty
        diff = self.ent_difficulty.get()
        if diff not in self.DIFFICULTIES:
            return "Invalid difficulty selection."

        return None

    def _on_export(self):
        err = self._validate()
        if err:
            messagebox.showerror("Validation error", err, parent=self)
            self.feedback_label.config(text=err, fg="red")
            return

        self.result = {
            "calculator_allowed": bool(self.var_calculator_allowed.get()),
            "difficulty": self.ent_difficulty.get(),
            "question_number": int(self.ent_question_number.get()) if self.ent_question_number.get().strip() else None,
            "exam_board": self.ent_exam_board.get().strip() or None,
            "year": int(self.var_year.get()),
            "month": int(self.var_month.get()),
        }
        self.destroy()

    def fetch_result(self):
        """Wait for window closure"""
        self.wait_window(self)
        return self.result
