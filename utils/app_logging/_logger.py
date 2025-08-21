# Standard library imports
from typing import Callable, Dict
import sys
import datetime
import inspect
import os

# Third-party imports
from colorama import Style, Fore

# Local application imports
from ._levels import DebugMode, LogLevel
from ._colors import CATEGORY_COLORS


_LOGGER_DIR = os.path.dirname(__file__)

# Any extra modules to skip even if they're outside the logger directory
class IgnoreModules(set):
    def ignore(self, func_name: str = None) -> None:
        frame = inspect.stack()[1]
        mod = inspect.getmodule(frame.frame)
        if mod:
            key = (mod.__name__, func_name)
            self.add(key)

IGNORE_MODULES = IgnoreModules()


def _timestamp() -> str:
    return datetime.datetime.now().strftime('%H:%M:%S')


def _log_debug(category: str, message: str) -> None:
    print(f"[{_timestamp()}] [{category}] {message}")

def _log_verbose(category: str, message: str) -> None:
    for frame_info in inspect.stack():
        frame_path = os.path.abspath(frame_info.filename)
        mod = inspect.getmodule(frame_info.frame)

        # Skip frames if they are in logger dir OR in an explicitly ignored module
        if (
            frame_path.startswith(_LOGGER_DIR)
            or (mod and mod.__name__ in IGNORE_MODULES)
        ):
            continue

        if (mod.__name__, frame_info.function) in IGNORE_MODULES:
            continue

        # Found the first "external" caller
        filepath = os.path.basename(frame_info.filename)
        lineno = frame_info.lineno
        funcname = frame_info.function
        break

    print(
        f"[{_timestamp()}] [{category}] {message} "
        f"@ {filepath}:{lineno} in {funcname}()"
    )


# Mode‑specific log handlers
debug_handlers: Dict[DebugMode, Callable] = {
    DebugMode.DEBUG: _log_debug,
    DebugMode.VERBOSE: _log_verbose
}

def _core_log(
        level: LogLevel,
        debug_mode: DebugMode,
        message: str,
        prioritize: bool
) -> None:
    """Log output according to debug mode."""

    if debug_mode is DebugMode.OFF:
        return

    color = CATEGORY_COLORS.get(level, "")
    category = f"{color}{level.value}{Style.RESET_ALL}"

    handler = debug_handlers.get(debug_mode)
    if handler:
        if prioritize:
            handler(category, f"{Fore.RED}{message}{Style.RESET_ALL}")
        else:
            handler(category, message)
    else:
        print(
            f"[{Fore.MAGENTA}LOG_ERROR{Style.RESET_ALL}]"
            f"No handler for mode: {debug_mode}",
            file=sys.stderr
        )
        raise RuntimeError(f"Missing debug handler for mode {debug_mode}")
