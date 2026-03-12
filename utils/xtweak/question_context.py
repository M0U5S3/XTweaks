from typing import Dict, Union

Number = Union[int, float]

class VarRef:
    __slots__ = ("_ctx", "_name", "_store")

    def __init__(self, ctx, name: str, store: str = "_variables"):
        self._ctx = ctx
        self._name = name
        self._store = store

    @property
    def value(self):
        return getattr(self._ctx, self._store)[self._name]

    def set(self, new):
        getattr(self._ctx, self._store)[self._name] = new
        return self

    # numeric protocol: allow use in arithmetic and f-strings
    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

    # Binary ops.
    def __add__(self, other):
        return self.value + (other.value if isinstance(other, VarRef) else other)

    def __radd__(self, other):
        return (other.value if isinstance(other, VarRef) else other) + self.value

    def __sub__(self, other):
        return self.value - (other.value if isinstance(other, VarRef) else other)

    def __rsub__(self, other):
        return (other.value if isinstance(other, VarRef) else other) - self.value

    def __mul__(self, other):
        return self.value * (other.value if isinstance(other, VarRef) else other)

    def __rmul__(self, other):
        return (other.value if isinstance(other, VarRef) else other) * self.value

    def __truediv__(self, other):
        return self.value / (other.value if isinstance(other, VarRef) else other)

    def __rtruediv__(self, other):
        return (other.value if isinstance(other, VarRef) else other) / self.value

    # In-place ops.
    def __iadd__(self, other):
        new = self.value + (other.value if isinstance(other, VarRef) else other)
        self.set(new)
        return self

    def __isub__(self, other):
        new = self.value - (other.value if isinstance(other, VarRef) else other)
        self.set(new)
        return self

    def __imul__(self, other):
        new = self.value * (other.value if isinstance(other, VarRef) else other)
        self.set(new)
        return self

    def __itruediv__(self, other):
        new = self.value / (other.value if isinstance(other, VarRef) else other)
        self.set(new)
        return self

    # Comparisons
    def __eq__(self, other):
        return self.value == (other.value if isinstance(other, VarRef) else other)

    def __lt__(self, other):
        return self.value < (other.value if isinstance(other, VarRef) else other)

    def __le__(self, other):
        return self.value <= (other.value if isinstance(other, VarRef) else other)

class QuestionContext:
    """Interface the CRNG file with xTweaks."""
    def __init__(self):
        self._variables: Dict[str, Number] = {}
        self._solutions: Dict[str, Number] = {}
        self._workings = []
        self._question_text = ''

    @property
    def variables(self) -> Dict:
        return self._variables

    @property
    def solutions(self) -> Dict:
        return self._solutions

    @property
    def workings(self):
        return self._workings

    @property
    def question_text(self):
        return self._question_text

    @question_text.setter
    def question_text(self, text: str):
        self._question_text = text

    def variable(self, name, value):
        self._variables[name] = value
        return VarRef(self, name, "_variables")

    def solution(self, name, value):
        self._solutions[name] = value
        return VarRef(self, name, "_solutions")

    def output_workings(self, workings: str) -> None:
        self._workings.append(workings)
