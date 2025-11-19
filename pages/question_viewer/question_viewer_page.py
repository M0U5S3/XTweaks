

# Third-party imports
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict

# Local application imports
from utils.parse_question import QuestionReader
from utils.style import style
from utils.pages import Pages
from utils.image_canvas import ImageCanvas
from utils.question import Question
from utils.xtweak import QuestionContext


class QuestionViewerPage(tk.Frame):
    """
    Page for opening a question file.
    """

    def __init__(self, parent: tk.Widget, controller: tk.Tk, **kwargs):
        # === Page Setup ===
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.controller = controller

        # Reader for question files.
        self.reader = QuestionReader(self.controller)

        # Start with no question yet
        # todo but will force this to be set on init instead
        self.questions = None
        self.current_question = None

        # Dynamic answer boxes.
        self.solution_entries = {}

        # Record of which answers are wrong or right.
        self.correct_solutions = {}

        # === Style Setup ===
        fonts = style.get_fonts()
        button_style = style.get_button_style_question_editor()
        label_style = style.get_label_style()
        frame_style = style.get_frame_style()
        back_button_style = style.get_back_button_style()

        # === Define widgets ===
        # --- Header ---
        # --- Back Button ---
        back_button = tk.Button(
            self,
            text="←",
            command=lambda: self.controller.show_page(Pages.HOME),
            **back_button_style
        )
        back_button.place(x=10, y=10)

        # --- Title ---
        self.title = tk.StringVar(value="Select A Question")
        title_label = ttk.Label(
            self,
            textvariable=self.title,
            font=fonts["title"],
            **label_style
        )

        title_label.pack(pady=(20, 10))

        # --- Main Body ---
        main_frame = tk.Frame(self, **frame_style)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Two equal sized columns.
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1, uniform="half")
        main_frame.grid_columnconfigure(1, weight=1, uniform="half")

        # --- Question Frame ---
        question_frame = tk.Frame(main_frame)
        question_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        # Prompt, Canvas, Info.
        question_frame.grid_rowconfigure(0, weight=0)
        question_frame.grid_rowconfigure(1, weight=1)
        question_frame.grid_rowconfigure(2, weight=0)
        question_frame.grid_columnconfigure(0, weight=1)

        # --- Question Prompt ---
        self.question_prompt = tk.StringVar(value='No Question Loaded')
        question_prompt_label = ttk.Label(
            question_frame,
            textvariable=self.question_prompt,
            font=fonts["default"],
            **label_style
        )
        question_prompt_label.grid(row=0, column=0, sticky="nw", padx=4, pady=(6, 6))

        # --- Image Canvas ---
        self.question_canvas = ImageCanvas(
            question_frame,
            self.controller,
            width=700,
            height=700  # todo expand to fit frame
        )
        self.question_canvas.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # --- Question Information ---
        self.question_info = tk.StringVar(value='No Question Loaded')
        question_info_label = ttk.Label(
            question_frame,
            textvariable=self.question_info,
            font=fonts["default"],
            **label_style
        )
        question_info_label.grid(row=2, column=0, sticky="sw", padx=4, pady=(6, 6))

        # --- Controls Frame ---
        controls_frame = tk.Frame(main_frame)
        controls_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        # --- Solutions Title ---
        solutions_frame_label = tk.Label(controls_frame, text="Solutions", font=fonts["subtitle"], **label_style)
        solutions_frame_label.pack(anchor="w", pady=(0, 5))

        # --- Solutions Frame ---
        # Use a frame with a canvas + scrollbar, keep a flexible width so right pane fills half
        solutions_container = tk.Frame(controls_frame)
        solutions_container.pack(fill="both", expand=True)

        solutions_canvas = tk.Canvas(solutions_container, borderwidth=0, highlightthickness=0)
        solutions_scroll = ttk.Scrollbar(solutions_container, orient="vertical", command=solutions_canvas.yview)
        solutions_canvas.configure(yscrollcommand=solutions_scroll.set)

        # place canvas and scrollbar
        solutions_canvas.pack(side="left", fill="both", expand=True)
        solutions_scroll.pack(side="right", fill="y")

        self.solutions_frame = tk.Frame(solutions_canvas, **frame_style)
        self.solutions_window = solutions_canvas.create_window((0, 0), window=self.solutions_frame, anchor="nw")

        def _on_frame_configure(event):
            solutions_canvas.configure(scrollregion=solutions_canvas.bbox("all"))

        def _on_canvas_configure(event):
            # make the inner frame match the canvas width
            canvas_width = event.width
            solutions_canvas.itemconfig(self.solutions_window, width=canvas_width)

        self.solutions_frame.bind("<Configure>", _on_frame_configure)
        solutions_canvas.bind("<Configure>", _on_canvas_configure)

        # --- Buttons Frame ---
        buttons_row = tk.Frame(controls_frame)
        buttons_row.pack(anchor="w", pady=(8, 12))

        # --- Check Solutions Button ---
        check_button = tk.Button(
            buttons_row,
            text="Check Solutions",
            command=self.check_solution,
            **button_style
        )
        check_button.pack(side="left", padx=5)

        # --- Generate Context Button ---
        gen_context_button = tk.Button(
            buttons_row,
            text="Generate Context",
            command=self.generate_context,
            **button_style
        )
        gen_context_button.pack(side="left", padx=5)

        # --- Workings Title ---
        workings_label = tk.Label(controls_frame, text="Workings", font=fonts["subtitle"], **label_style)
        workings_label.pack(anchor="w", pady=(10, 2))

        # --- Workings Area ---
        self.workings_text = tk.Text(
            controls_frame,
            width=40,
            height=12,
            wrap="word",
            font=fonts["math"]
        )
        self.workings_text.pack(fill="both", expand=True)

        # === Load questions button ===
        load_frame = tk.Frame(self, **frame_style)
        load_frame.pack(side="bottom", fill="x", pady=10)

        load_button = tk.Button(
            load_frame,
            text="Load questions",
            command=self.import_questions,
            **button_style
        )
        load_button.pack(side="right", padx=20)

    def check_solution(self):
        # Cycle through variable names and correct answers.
        for name, solution in self.current_ctx.solutions.items():
            entered = self.solution_entries[name][1].get().strip()
            expected = str(solution)
            is_correct = entered == expected

            self.correct_solutions[name] = is_correct

            # Update answer feedback.
            color = 'green' if is_correct else 'red'
            self.solution_entries[name][2].config(fg=color)

        # Show the workings to the student.
        self.show_workings()

    def show_workings(self):
        # Output the workings line-by-line.
        for line in self.current_ctx.workings:
            self.workings_text.insert(tk.END, f"{line}\n")

    def import_questions(self):
        # todo add database call.
        # todo force an import before page opens.
        self.reader.question_paths = [
            'C:/Users/dariu/Downloads/AQA_7_2020_5.xtweak'
        ]
        # self.controller.open_questiondb or something return a list of paths. Only ".xtweak" files.

        # Save every selected question to an attribute in order of the list of paths.
        self.questions: list[Dict[str, Question|Callable[[], QuestionContext]],...] = self.reader.all_questions

        # Load and generate the first question upon import
        self.load_question(0)

    def load_question(self, question_number):
        # Set the current question we're working on and seperate the question object first.
        self.current_question = self.reader.get_question(question_number)
        question_data = self.current_question['question_data']

        # Render the image.
        self.question_canvas.question_image_binary = question_data.image_binary

        # Format question info correctly.
        display_date = question_data.month and question_data.year
        display_location = question_data.exam_board and question_data.question_number

        date = f'{question_data.month}/{question_data.year}' if display_date else ''
        optional_newline = '\n' if not display_location and display_date else ' '
        location = f'{question_data.exam_board} Q{question_data.question_number}\n' if display_location else ''

        self.question_info.set(f'{date}{optional_newline}{location}'
                               f'Difficulty: {question_data.difficulty}\n'
                               f'Calculator is{' ' if question_data.calculator_allowed else ' not '}allowed')

        # Generate context and apply changes
        self.generate_context()

    def generate_context(self):
        # Create a ctx instance
        self.current_ctx = self.current_question['crng_function']()

        # Load dynamic question prompt
        self.question_prompt.set(self.current_ctx.question_text)

        # Change the GUI to accommodate a potentially new number of solutions.
        self.configure_solutions_input()

        # Place the new variables over old ones in the image
        self.place_masks()

        print(self.current_ctx.solutions)
        print(self.current_ctx.variables)  # DEBUG

    def configure_solutions_input(self):
        fonts = style.get_fonts()

        # Reset the current entries first.
        self.initialize_solutions()

        # Loop through solutions and make an input for each one.
        for key in self.current_ctx.solutions:
            row_frame = tk.Frame(self.solutions_frame)
            row_frame.pack(fill="x", pady=2)

            var = tk.StringVar()
            lbl = tk.Label(row_frame, text=f"{key}", width=10, font=fonts["default"], **style.get_label_style())
            ent = tk.Entry(row_frame, textvariable=var, width=15, font=fonts["default"])

            lbl.pack(side="left")
            ent.pack(side="left", padx=(5, 0))

            # Store references
            self.solution_entries[key] = [row_frame, var, lbl]

    def place_masks(self):
        variables = self.current_question['question_data'].variables

        for var_name in variables:
            variables[var_name].new_canvas_masks(self.question_canvas, self.current_ctx, fill='white')

    def initialize_solutions(self):
        # Loop through each entry and delete its frame.
        for data in self.solution_entries.values():
            data[0].destroy()

        # Clear refrences to the deleted elements
        self.solution_entries = {}

        # Reset the solution checks
        self.correct_solutions = {}
