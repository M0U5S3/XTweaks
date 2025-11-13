# Standard Library Imports
import ast
import importlib.util
import os
import inspect
from pathlib import Path
import dill as pickle

# Local application imports
from utils.app_logging import LogLevel
from utils.dependency_manager import DependencyManager
from utils.question import Question

class QuestionReader:
    def __init__(self, controller):
        self.controller = controller
        self._question_paths = None

    @property
    def question_paths(self):
        return self._question_paths

    @question_paths.setter
    def question_paths(self, question_paths: list[Path|str,...]):
        self._question_paths = question_paths

    @property
    def all_questions(self):
        return [self.get_question(n) for n in range(len(self.question_paths))]

    def get_question(self, question_number: int):
        # Ensure that there is actually questions.
        if not self.question_paths:
            self.controller.log(LogLevel.ERROR, 'No questions have been set to the reader.')
            return

        # Find the question's path.
        question_path = self._question_paths[question_number]

        # Load question data.
        with open(question_path, 'rb') as fh:
            question = pickle.load(fh)

        # Retrieve crng function.
        crng_path = self.controller.crng_dir / question.crng_name
        crng = self.get_crng_function(crng_path)

        # Return question data and generator function.
        return {'question_data': question, 'crng_function': crng}

    def get_crng_function(self, crng_path):
        required_modules = self._collect_required_modules(crng_path)
        dependency_manager = DependencyManager(self, self.controller, required_modules)

        if not dependency_manager.handle_missing_dependencies():
            return

        module = self._import_module_from_path(crng_path)
        if module is None:
            return

        crng_function = self._get_function(module, crng_path)
        if crng_function is None:
            return

        self.controller.log(LogLevel.INFO, f"CRNG function successfully imported")
        return crng_function


    def _collect_required_modules(self, crng_path):
        # Read file as raw text
        try:
            with open(crng_path, "r", encoding="utf-8") as f:
                source_code = f.read()

        except Exception as e:  # Handle any read issue
            self.controller.log(LogLevel.ERROR, f"Failed to read file: {e}")
            return

        # Parse and validate 'crng' function
        try:
            parsed = ast.parse(source_code)

        except SyntaxError as e:  # Handle any syntax errors while parsing.
            self.controller.log(LogLevel.ERROR, f"Syntax error while parsing file: {e}")
            return

        # Check for missing dependencies.
        required_modules = set()

        # Traverse syntax tree depth first so we don't miss nested imports.
        for node in ast.walk(parsed):
            # Check if the node is any kind of import
            if isinstance(node, ast.Import):
                required_modules.update(alias.name.split('.')[0] for alias in node.names)

            elif isinstance(node, ast.ImportFrom) and node.module:
                required_modules.add(node.module.split('.')[0])

        return required_modules


    @staticmethod
    def _import_module_from_path(file_path):
        # Retrieve file name.
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Prepare and execute the module.
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


    def _get_function(self, module, file_path):
        """Discovers exactly one @question-decorated function in a module."""
        # Scan for functions flagged by the decorator
        flagged = [
            fn for _, fn in inspect.getmembers(module, inspect.isfunction)
            if getattr(fn, "_is_question", False)
        ]

        # No flagged function.
        if not flagged:
            self.controller.log(
                LogLevel.ERROR,
                f"No @question function found in {file_path}"
            )
            return

        # More than one flagged function.
        if len(flagged) > 1:
            names = [fn.__name__ for fn in flagged]
            self.controller.log(
                LogLevel.ERROR,
                f"Multiple @question functions in {file_path}: {names}"
            )
            return

        # Exactly one flagged function
        fn = flagged[0]
        self.controller.log(
            LogLevel.INFO,
            f"Discovered '{fn.__name__}' in {file_path}"
        )
        return fn
