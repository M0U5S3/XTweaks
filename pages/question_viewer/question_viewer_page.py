import tkinter as tk

class QuestionEditorPage(tk.Frame):
    """
    Page for opening a question file.
    """

    def __init__(self, parent: tk.Widget, controller: tk.Tk, **kwargs):
        # === Page Setup ===
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.controller = controller

        with open("data/placeholder_image.jpeg", "rb") as f:
            question_image_binary = f.read()

        self.question_image_imported = False
        self._variables: dict[str: Variable] = {}

        # === Style Setup ===
        fonts = style.get_fonts()
        button_style = style.get_button_style_question_editor()
        label_style = style.get_label_style()
        frame_style = style.get_frame_style()

        # === Define Widgets ===

        # -- Header --
        header = ttk.Label(self, text="Question Editor", font=fonts["title"], **label_style)

        # -- Canvas --
        self.question_canvas = QuestionCanvas(
            self,
            controller,
            question_image_binary
        )

        # -- Status & Coordinates --
        self.x_display = ttk.Label(self, textvariable=self.question_canvas.mouse_x, font=fonts["default"],
                                   **label_style)
        self.y_display = ttk.Label(self, textvariable=self.question_canvas.mouse_y, font=fonts["default"],
                                   **label_style)

        self.crng_status = CRNGStatusLabel(self)
        self.crng_status.configure(font=fonts["default"], **label_style)

        # -- Buttons --
        back_button = tk.Button(
            self,
            text="←",
            command=lambda: self.controller.show_page(Pages.HOME),
            **style.get_back_button_style()
        )

        import_export_buttons = tk.Frame(self, **frame_style)

        import_crng_button = tk.Button(
            import_export_buttons,
            text="Import CRNG",
            command=self._assign_crng_name,
            **button_style
        )

        question_button = tk.Button(
            import_export_buttons,
            text="Import Image",
            command=self._import_image,
            **button_style
        )

        export_question_button = tk.Button(
            import_export_buttons,
            text="Export Question",
            command=self._export_question,
            **button_style
        )

        # === Pack Widgets ===

        # -- Header --
        header.pack(pady=10)

        # -- Canvas --
        self.question_canvas.pack(pady=20)

        # -- Status & Coordinates --
        self.x_display.pack()
        self.y_display.pack()
        self.crng_status.pack(pady=5)

        # -- Buttons --
        back_button.place(x=10, y=10)

        import_export_buttons.pack(pady=5)
        import_crng_button.pack(side="left", padx=5)
        question_button.pack(side="left", padx=5)
        export_question_button.pack(side="left", padx=5)