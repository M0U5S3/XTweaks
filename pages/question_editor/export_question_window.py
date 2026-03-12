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

        # Track whether the page is being closed intentionally (via valid progression)
        self._intentional_close = False  # Set True when user advances via Export
        self.bind("<Destroy>", self._on_destruction)
        self._direct_destroy = super().destroy

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
                                   command=self._on_year_spinbox_change)

        month_label = ttk.Label(self, text="Month:", font=fonts["default"], **label_style)
        self.var_month = tk.IntVar(value=self._current_month)
        self.ent_month = tk.Spinbox(self, from_=1, to=12, textvariable=self.var_month, width=10)

        # Feedback label (validation)
        self.feedback_label = tk.Label(self, text="", font=fonts["default"], foreground="blue")

        # -- Buttons --
        button_frame = tk.Frame(self, **frame_style)
        self.btn_export = tk.Button(button_frame, text="Export", command=self._on_export, **button_style)
        self.btn_cancel = tk.Button(button_frame, text="Cancel", command=self._on_cancel, **button_style)

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

        # Bindings
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # When the year changes check the month is still valid
        self.var_year.trace_add("write", lambda *_: self._enforce_month_limit())

        # Start focused on the first text input
        self.ent_question_number.focus()

        self.controller.log(LogLevel.DEBUG, "Opened question metadata window")

    def _on_year_spinbox_change(self):
        try:
            _ = int(self.var_year.get())
        except Exception:
            pass
        self._enforce_month_limit()

    def _enforce_month_limit(self):
        """Clamp month max to current month if year == current year."""
        try:
            year = int(self.var_year.get())
        except Exception:
            return

        max_month = self._current_month if year >= self._current_year else 12

        try:
            self.ent_month.config(to=max_month)
            if int(self.var_month.get()) > max_month:
                self.var_month.set(max_month)
        except Exception:
            pass

    def _validate(self) -> Optional[str]:
        """Validate inputs. Return None if OK otherwise error message string."""
        # optional
        qnum = self.ent_question_number.get().strip()
        if qnum:
            try:
                qn = int(qnum)
                if qn < 0:
                    return "Question number must be zero or positive."
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
        """Validate, set result and then close intentionally."""
        err = self._validate()
        if err:
            self.feedback_label.config(text=err, fg="red")
            messagebox.showerror("Validation error", err, parent=self)
            return

        # question number (optional)
        qnum_raw = self.ent_question_number.get().strip()
        qnum = int(qnum_raw) if qnum_raw != "" else None

        # exam board (optional)
        exam_raw = self.ent_exam_board.get().strip()
        exam_board = exam_raw if exam_raw != "" else None

        # year (optional)
        try:
            year_val = self.var_year.get()
            year = int(year_val) if year_val != "" else None
        except Exception:
            year = None

        # month (optional)
        try:
            month_val = self.var_month.get()
            month = int(month_val) if month_val != "" else None
        except Exception:
            month = None

        self.result = {
            "calculator_allowed": bool(self.var_calculator_allowed.get()),
            "difficulty": self.ent_difficulty.get(),
            "question_number": qnum,
            "exam_board": exam_board,
            "year": year,
            "month": month,
        }
        self.destroy(intentional=True)

    def _on_cancel(self):
        """User pressed Cancel button."""
        self.result = None
        self.destroy()

    def _on_close(self):
        """User closed the window via the window manager (X)."""
        self.result = None
        self.destroy(intentional=False)

    def destroy(self, intentional: bool = False):
        """Override destroy to record whether the close was intentional."""
        self._intentional_close = intentional
        try:
            self.controller.log(LogLevel.DEBUG, "Window closure detected")
        except Exception:
            pass
        self._direct_destroy()

    def _on_destruction(self, event):
        """Called when the window is destroyed."""
        if not self._intentional_close:
            pass
