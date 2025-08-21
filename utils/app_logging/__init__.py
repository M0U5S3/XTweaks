from ._levels import DebugMode, LogLevel
from ._logger import IGNORE_MODULES

from colorama import init
init(autoreset=True)

__all__ = ["DebugMode", "LogLevel", "IGNORE_MODULES"]
