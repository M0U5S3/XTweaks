from typing import Dict

class QuestionContext:
    """Interface the CRNG file with xTweaks"""
    def __init__(self):
        self._variables = {}
        self._solutions = {}
        self._workings = []

        self._question_text = ()

    @property
    def variables(self) -> Dict:
        """Returns a dictionary of variables"""
        return self._variables

    @property
    def solutions(self) -> Dict:
        """Returns a dictionary of solutions"""
        return self._solutions

    @property
    def workings(self):
        """Yields a list of workings"""
        for working in self._workings:
            yield working

    @property
    def question_text(self):
        """Returns text to display under the question"""
        return self._question_text

    def variable(self, name: str, value: int or float) -> str:
        """Create a new variable and return an identifier"""
        self._variables[name] = value
        return name

    def solution(self, name: str, value: int or float) -> str:
        """Create a new solution and return an identifier"""
        self._solutions[name] = value
        return name

    def output_workings(self, workings: str) -> None:
        """Print out a new line of working"""
        self._workings.append(workings)

    @question_text.setter
    def question_text(self, text: str):
        """Optional text to display under the question"""
        self._question_text = text
