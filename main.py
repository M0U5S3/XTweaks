# Standard Library Imports
from pathlib import Path

# Local application imports
from controller import AppController, DebugMode
from utils.pages import Pages

CRNG_PATH = Path(__file__).resolve().parents[0] / "crng_files"

# Initialize AppController
if __name__ == '__main__':
    app = AppController(Pages.QUESTION_VIEWER, CRNG_PATH, debug_mode=DebugMode.DEBUG)
    app.run()
