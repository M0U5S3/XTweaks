from colorama import Fore

from ._levels import LogLevel

CATEGORY_COLORS = {
    LogLevel.INFO:  Fore.GREEN,
    LogLevel.WARN:  Fore.YELLOW,
    LogLevel.ERROR: Fore.RED,
    LogLevel.DEBUG: Fore.CYAN
}
