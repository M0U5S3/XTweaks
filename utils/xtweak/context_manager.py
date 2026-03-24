import inspect
from functools import wraps
from .question_context import QuestionContext

def question(fn):
    # Enforce exactly one parameter (ctx)
    sig = inspect.signature(fn)
    params = [
        p for p in sig.parameters.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    if len(params) != 1:
        raise TypeError(
            f"@question requires 1 parameter, but `{fn.__name__}` has {len(params)}"
        )

    @wraps(fn)
    def wrapper():
        ctx = QuestionContext()
        result = fn(ctx)

        # Accept functions that don't return but normalize the output.
        if isinstance(result, QuestionContext):
            return result
        if result is None:
            return ctx

        # Raise an error if it's a bad function.
        raise RuntimeError(
            f"`{fn.__name__}` returned {result!r} "
            f"(type {type(result).__name__}); must return None or QuestionContext"
        )

    # Attach flags
    wrapper._is_question = True
    wrapper._question_name = fn.__name__

    return wrapper
