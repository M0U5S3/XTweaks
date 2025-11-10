from typing import Callable, Optional, Dict
import dill as pickle
from pathlib import Path
from utils.xtweak import QuestionContext
from utils.variable import Variable


class Question:
    def __init__(
            self,
            crng_name: str,
            image_binary: bytes,
            variables: Dict[str, Variable],
            calculator_allowed: bool,
            difficulty: str,
            question_number: Optional[int] = None,
            exam_board: Optional[str] = None,
            year: Optional[int] = None,
            month: Optional[int] = None,
    ):
        self.crng_name = crng_name
        self.image_binary = image_binary
        self.variables = variables
        self.calculator_allowed = calculator_allowed
        self.difficulty = difficulty
        self.question_number = question_number
        self.exam_board = exam_board
        self.year = year
        self.month = month

    def export(self, directory: Optional[str] = None) -> str:
        """
        Exports to a .xtweaks file.
        If `directory` isn’t provided, defaults to ~/Downloads.
        Returns the path of the new file.
        """
        # Resolve target directory.
        target = Path(directory) if directory else Path.home() / "Downloads"
        target.mkdir(parents=True, exist_ok=True)

        # Build a descriptive filename.
        parts = [
            self.exam_board or "question",
            str(self.question_number) if self.question_number else None,
            str(self.year) if self.year else None,
            str(self.month) if self.month else None
        ]

        # Filter out None and join with underscores
        name = "_".join(p for p in parts if p)
        filename = f"{name}.xtweak"

        # Avoid overwriting by appending a counter if needed
        file_path = target / filename
        counter = 1
        while file_path.exists():
            file_path = target / f"{name}_({counter}).xtweak"
            counter += 1

        # Pickle-dump self
        with file_path.open("wb") as fh:
            pickle.dump(self, fh)

            return str(file_path)

