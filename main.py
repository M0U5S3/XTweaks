# Local application imports
from controller import AppController, DebugMode
from utils.pages import Pages

# Initialize AppController
if __name__ == '__main__':
    app = AppController(Pages.HOME, debug_mode=DebugMode.DEBUG)
    app.run()
