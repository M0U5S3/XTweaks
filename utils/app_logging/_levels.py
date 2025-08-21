from enum import Enum

class DebugMode(Enum):
    OFF = 0
    DEBUG = 1
    VERBOSE = 2

class LogLevel(Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
